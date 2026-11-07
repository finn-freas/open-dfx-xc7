set CONFIG_PART      xc7a35tcsg324-1
set CONFIG_SRCROOT   [lindex $argv 0]
set CONFIG_OUTROOT   [lindex $argv 1]
set CONFIG_NAMES     [lrange $argv 2 end]
set CONFIG_MAX_PATHS 5000
set CONFIG_STYLES    {abs rel}
set CONFIG_BITSTREAM 1
set CONFIG_ROUTE_CONST 1
set CONFIG_DIAG_NETS 25

proc step {fh name script} {
    set ::cur_step $name
    set t0 [clock milliseconds]
    uplevel 1 $script
    puts $fh [format "%s %.2f" $name [expr {([clock milliseconds] - $t0) / 1000.0}]]
    flush $fh
}

proc node_of {tw} {
    if {[info exists ::nodecache($tw)]} { return $::nodecache($tw) }
    set n [get_nodes -quiet -of_objects [get_wires -quiet $tw]]
    set ::nodecache($tw) $n
    return $n
}

proc nname {n style} {
    if {$style eq "abs"} { return $n }
    return [lindex [split $n /] end]
}

proc emit {node style} {
    set out [nname $node $style]
    if {![info exists ::kids($node)]} { return $out }
    set ks $::kids($node)
    foreach k [lrange $ks 0 end-1] { append out " \{ " [emit $k $style] " \}" }
    append out " " [emit [lindex $ks end] $style]
    return $out
}

proc build_tree {pips} {
    array unset ::kids
    set ups {}
    set dns {}
    set bad {}
    foreach p $pips {
        lassign [split $p /] tile src dst
        set u [node_of $tile/$src]
        set d [node_of $tile/$dst]
        if {$u eq "" || $d eq ""} { lappend bad $p; continue }
        if {[info exists seen($u,$d)]} { continue }
        set seen($u,$d) 1
        lappend ::kids($u) $d
        lappend ups $u
        lappend dns $d
        set ::edge_out [list $u $d $p]
        lappend ::edges $::edge_out
    }
    set roots {}
    foreach u [lsort -unique $ups] { if {[lsearch -exact $dns $u] < 0} { lappend roots $u } }
    return [list $roots $bad]
}

proc route_string {roots style} {
    set parts {}
    foreach r $roots { lappend parts "\{ [emit $r $style] \}" }
    return [join $parts " "]
}

proc read_lines {path} {
    set out {}
    if {![file exists $path]} { return $out }
    set f [open $path]
    while {[gets $f line] >= 0} { if {[string trim $line] ne ""} { lappend out $line } }
    close $f
    return $out
}

file mkdir $CONFIG_OUTROOT
foreach name $CONFIG_NAMES {
    set src $CONFIG_SRCROOT/$name
    set out $CONFIG_OUTROOT/$name
    file mkdir $out
    if {[file exists $out/status.txt]} { puts "skip: $out/status.txt exists"; continue }
    puts "XROUTE_BEGIN $name"
    array unset ::nodecache
    set top [string trim [read [open $src/top.txt]]]
    set tf [open $out/times.txt w]
    set ::cur_step read
    set rc [catch {
        create_project -in_memory -part $CONFIG_PART
        file copy -force $src/netlist.edf $out/$top.edf
        read_edif $out/$top.edf
        link_design -top $top -part $CONFIG_PART
        read_xdc $src/constraints.xdc
        step $tf place {
            set lf [open $out/place_log.txt w]
            set nlock 0
            foreach line [read_lines $src/lockpins.txt] {
                lassign $line cell lp
                set c [get_cells -quiet $cell]
                if {$c eq ""} { puts $lf "lock_missing $cell"; continue }
                set_property LOCK_PINS $lp $c
                incr nlock
            }
            set placed 0
            set fixed {}
            set mfixed {}
            foreach line [read_lines $src/macros.txt] {
                set m [lindex $line 0]
                set site [lindex [split [lindex $line 2] /] 0]
                if {[catch { set_property LOC $site [get_cells $m] } err]} { puts $lf "macro_fail $m $err"; continue }
                foreach {sub loc} [lrange $line 1 end] {
                    set c [get_cells $m/$sub]
                    set got [get_bels -quiet -of_objects $c]
                    if {$got ne $loc} { puts $lf "macro_bel $m/$sub want $loc got $got" }
                    lappend mfixed $c
                    incr placed
                }
            }
            if {[llength $mfixed]} { set_property IS_LOC_FIXED 1 $mfixed }
            foreach line [read_lines $src/place.txt] {
                lassign $line cell loc
                set c [get_cells -quiet $cell]
                if {$c eq ""} { puts $lf "missing $cell"; continue }
                if {[catch { place_cell $c $loc } err]} { puts $lf "fail $cell $loc $err"; continue }
                incr placed
                lappend fixed $c
            }
            if {[llength $fixed]} {
                set_property IS_LOC_FIXED 1 $fixed
                set_property IS_BEL_FIXED 1 $fixed
            }
            puts $lf "placed $placed lockpins $nlock"
            close $lf
            place_design
        }
        step $tf setroute {
            set rf [open $out/route_log.txt w]
            set ::edges {}
            set ok 0
            set okstyle(rel) 0
            set okstyle(abs) 0
            set fixednets {}
            set nfail 0
            set ef [open $out/edges.txt w]
            foreach line [read_lines $src/routes.txt] {
                set ident [lindex $line 0]
                set nnm [lindex $line 1]
                set pips [lrange $line 2 end]
                set net [get_nets -quiet -of_objects [get_pins -quiet $ident]]
                if {$net eq ""} { puts $rf "nonet {$ident} {$nnm}"; continue }
                set ::edges {}
                lassign [build_tree $pips] roots bad
                if {[llength $bad]} { puts $rf "badpips $net [llength $bad] [lrange $bad 0 3]" }
                if {[llength $roots] != 1} { puts $rf "roots $net [llength $roots] $roots" }
                foreach e $::edges { puts $ef "$net\t[lindex $e 0]\t[lindex $e 1]\t[lindex $e 2]" }
                set done 0
                foreach style $::CONFIG_STYLES {
                    set rs [route_string $roots $style]
                    if {[catch { set_property ROUTE $rs $net } err]} {
                        puts $rf "err_$style $net $err"
                        catch { set_property ROUTE {} $net }
                        continue
                    }
                    set st [get_property ROUTE_STATUS $net]
                    if {$st ne "ROUTED"} { puts $rf "status_$style $net $st"; catch { set_property ROUTE {} $net }; continue }
                    incr okstyle($style)
                    set done 1
                    break
                }
                if {$done} { incr ok; lappend fixednets $net }
                if {!$done} {
                    catch { set_property ROUTE [route_string $roots abs] $net }
                    incr nfail
                    if {$nfail <= $::CONFIG_DIAG_NETS} {
                        set df [open $out/route_diag.txt a]
                        puts $df [report_route_status -of_objects $net -return_string]
                        close $df
                    }
                }
            }
            close $ef
            if {[llength $fixednets]} { set_property IS_ROUTE_FIXED 1 $fixednets }
            puts $rf "ok $ok rel $okstyle(rel) abs $okstyle(abs)"
            close $rf
        }
        step $tf route { if {[catch { route_design -preserve } rerr]} { set ef2 [open $out/route_error.txt w]; puts $ef2 $rerr; close $ef2 } }
        report_route_status -file $out/route_status.rpt
        report_utilization -file $out/util.rpt
        report_timing_summary -file $out/timing.rpt
        step $tf dump {
            set pf [open $out/vpips.txt w]
            foreach n [get_nets -hierarchical -top_net_of_hierarchical_group -filter {ROUTE_STATUS != NOLOADS}] {
                foreach p [get_pips -quiet -of_objects $n] { puts $pf "$n\t$p" }
            }
            close $pf
            set sf [open $out/sinks.txt w]
            foreach n [get_nets -hierarchical -top_net_of_hierarchical_group -filter {ROUTE_STATUS != NOLOADS}] {
                foreach pin [get_pins -quiet -leaf -of_objects $n -filter {DIRECTION == IN}] {
                    set sp [get_site_pins -quiet -of_objects $pin]
                    set nd {}
                    foreach s $sp { lappend nd [get_nodes -quiet -of_objects $s] }
                    set drv [get_pins -quiet -leaf -of_objects $n -filter {DIRECTION == OUT}]
                    puts $sf "$n\t$drv\t$pin\t$sp\t$nd"
                }
            }
            close $sf
        }
        step $tf netdelay {
            set df [open $out/net_delays.txt w]
            set probe [lindex [get_nets -hierarchical -filter {ROUTE_STATUS == ROUTED}] 0]
            catch {
                set pf [open $out/netdelay_props.txt w]
                puts $pf [report_property -return_string [lindex [get_net_delays -of_objects $probe] 0]]
                close $pf
            }
            foreach n [get_nets -hierarchical -top_net_of_hierarchical_group -filter {ROUTE_STATUS != NOLOADS}] {
                if {[catch {
                    foreach d [get_net_delays -quiet -of_objects $n] {
                        puts $df "$n\t[get_property -quiet FROM_PIN $d]\t[get_property -quiet TO_PIN $d]\t[get_property -quiet SLOW_MAX $d]\t[get_property -quiet FAST_MIN $d]\t[get_property -quiet DELAY $d]\t[get_property -quiet ESTIMATED $d]"
                    }
                } err]} { puts $df "$n\tERR\t$err" }
            }
            close $df
        }
        step $tf paths {
            report_timing -setup -max_paths $::CONFIG_MAX_PATHS -nworst 1 -input_pins -file $out/paths_setup.rpt
            report_timing -hold -max_paths $::CONFIG_MAX_PATHS -nworst 1 -input_pins -file $out/paths_hold.rpt
        }
        if {$CONFIG_BITSTREAM} {
            step $tf bitstream {
                foreach c [get_drc_checks] { catch { set_property SEVERITY Warning $c } }
                write_bitstream -force $out/$top.bit
            }
        }
    } err]
    close $tf
    set sf [open $out/status.txt w]
    puts $sf "rc $rc"
    if {$rc} { puts $sf "step $::cur_step"; puts $sf "error $err" }
    close $sf
    catch { close_project }
}
set fh [open $CONFIG_OUTROOT/version.txt w]
puts $fh [version]
close $fh
