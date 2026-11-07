set CONFIG_PART      xc7a35tcsg324-1
set CONFIG_SRCROOT   [lindex $argv 0]
set CONFIG_OUTROOT   [lindex $argv 1]
set CONFIG_NAMES     [lrange $argv 2 end]
set CONFIG_STYLES    {abs rel}

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

proc slack_of {paths} {
    if {[llength $paths] == 0} { return "none" }
    return [get_property SLACK [lindex $paths 0]]
}

proc write_slack {fn} {
    set f [open $fn w]
    set seq [get_cells -hierarchical -filter {IS_SEQUENTIAL && REF_NAME != ICAPE2}]
    puts $f "wns [slack_of [get_timing_paths -setup -max_paths 1]]"
    puts $f "whs [slack_of [get_timing_paths -hold -max_paths 1]]"
    set p [get_timing_paths -setup -max_paths 1 -from $seq -to $seq]
    puts $f "wns_noicap [slack_of $p]"
    if {[llength $p]} {
        puts $f "noicap_path [get_property STARTPOINT_PIN $p] [get_property ENDPOINT_PIN $p] logic [get_property DATAPATH_LOGIC_DELAY $p] net [get_property DATAPATH_NET_DELAY $p] levels [get_property LOGIC_LEVELS $p]"
    }
    puts $f "whs_noicap [slack_of [get_timing_paths -hold -max_paths 1 -from $seq -to $seq]]"
    set tns 0.0
    foreach q [get_timing_paths -setup -max_paths 100000 -nworst 1 -unique_pins -slack_lesser_than 0 -from $seq -to $seq] {
        set tns [expr {$tns + [get_property SLACK $q]}]
    }
    puts $f "tns_noicap $tns"
    close $f
}

proc dump_cells {fn} {
    set f [open $fn w]
    foreach c [get_cells -hierarchical -filter {IS_PRIMITIVE}] {
        puts $f [join [list [get_property NAME $c] [get_property REF_NAME $c] [get_property LOC $c] [get_property BEL $c]] "\t"]
    }
    close $f
}

proc place_fixed {src out} {
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
    set nfail 0
    foreach line [read_lines $src/place.txt] {
        lassign $line cell loc
        set c [get_cells -quiet $cell]
        if {$c eq ""} { puts $lf "missing $cell"; continue }
        if {[catch { place_cell $c $loc } err]} { puts $lf "fail $cell $loc $err"; incr nfail; continue }
        incr placed
        lappend fixed $c
    }
    if {[llength $fixed]} {
        set_property IS_LOC_FIXED 1 $fixed
        set_property IS_BEL_FIXED 1 $fixed
    }
    puts $lf "placed $placed failed $nfail lockpins $nlock"
    close $lf
}

proc set_routes {src out} {
    set rf [open $out/route_log.txt w]
    set ok 0
    set fixednets {}
    set nfail 0
    set nnone 0
    foreach line [read_lines $src/routes.txt] {
        set ident [lindex $line 0]
        set nnm [lindex $line 1]
        set pips [lrange $line 2 end]
        set net [get_nets -quiet -of_objects [get_pins -quiet $ident]]
        if {$net eq ""} { incr nnone; puts $rf "nonet {$ident} {$nnm}"; continue }
        lassign [build_tree $pips] roots bad
        if {[llength $bad]} { puts $rf "badpips $net [llength $bad] [lrange $bad 0 3]" }
        set done 0
        foreach style $::CONFIG_STYLES {
            set rs [route_string $roots $style]
            if {[catch { set_property ROUTE $rs $net } err]} {
                catch { set_property ROUTE {} $net }
                continue
            }
            set st [get_property ROUTE_STATUS $net]
            if {$st ne "ROUTED"} { catch { set_property ROUTE {} $net }; continue }
            set done 1
            break
        }
        if {$done} { incr ok; lappend fixednets $net }
        if {!$done} {
            catch { set_property ROUTE [route_string $roots abs] $net }
            incr nfail
            puts $rf "partial $net"
        }
    }
    if {[llength $fixednets]} { set_property IS_ROUTE_FIXED 1 $fixednets }
    puts $rf "ok $ok partial $nfail nonet $nnone"
    close $rf
}

file mkdir $CONFIG_OUTROOT
foreach name $CONFIG_NAMES {
    set src $CONFIG_SRCROOT/$name
    set out $CONFIG_OUTROOT/$name
    file mkdir $out
    if {[file exists $out/status.txt]} { puts "skip: $out/status.txt exists"; continue }
    puts "RTE_BEGIN $name"
    array unset ::nodecache
    set top [string trim [read [open $src/top.txt]]]
    set mode [string trim [read [open $src/mode.txt]]]
    set tf [open $out/times.txt w]
    set ::cur_step read
    set rc [catch {
        create_project -in_memory -part $CONFIG_PART
        file copy -force $src/netlist.edf $out/$top.edf
        read_edif $out/$top.edf
        link_design -top $top -part $CONFIG_PART
        read_xdc $src/constraints.xdc
        if {$mode eq "vref"} {
            step $tf place { place_design }
            step $tf route { route_design }
            dump_cells $out/cells.txt
        } else {
            step $tf place { place_fixed $src $out; place_design }
            step $tf setroute { set_routes $src $out }
            step $tf route { if {[catch { route_design -preserve } rerr]} { set ef2 [open $out/route_error.txt w]; puts $ef2 $rerr; close $ef2 } }
        }
        report_route_status -file $out/route_status.rpt
        report_timing_summary -file $out/timing.rpt
        report_timing -setup -max_paths 20 -nworst 1 -file $out/paths_setup.rpt
        write_slack $out/slack.txt
        set seqc [get_cells -hierarchical -filter {IS_SEQUENTIAL && REF_NAME != ICAPE2}]
        report_timing -setup -max_paths 10 -nworst 1 -from $seqc -to $seqc -file $out/paths_noicap.rpt
        set pf [open $out/paths_noicap.txt w]
        foreach p [get_timing_paths -setup -max_paths 200 -nworst 1 -from $seqc -to $seqc] {
            set pins {}
            foreach pn [get_pins -of_objects $p] { lappend pins [get_property NAME $pn] }
            puts $pf "[get_property SLACK $p]\t[get_property DATAPATH_NET_DELAY $p]\t[get_property DATAPATH_LOGIC_DELAY $p]\t[join $pins { }]"
        }
        close $pf
        set df [open $out/net_delays.txt w]
        foreach n [get_nets -hierarchical -top_net_of_hierarchical_group -filter {ROUTE_STATUS != NOLOADS}] {
            catch {
                foreach d [get_net_delays -quiet -of_objects $n] {
                    puts $df "[get_property -quiet TO_PIN $d]\t[get_property -quiet SLOW_MAX $d]"
                }
            }
        }
        close $df
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
