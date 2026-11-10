set CONFIG_PART    xc7a35tcsg324-1
set CONFIG_SRCROOT [lindex $argv 0]
set CONFIG_OUTROOT [lindex $argv 1]
set CONFIG_NAMES   [lrange $argv 2 end]

proc step {fh name script} {
    set ::cur_step $name
    set t0 [clock milliseconds]
    uplevel 1 $script
    puts $fh [format "%s %.2f" $name [expr {([clock milliseconds] - $t0) / 1000.0}]]
    flush $fh
}

proc xt_dump_cells {fn} {
    set f [open $fn w]
    foreach c [get_cells -hierarchical -filter {IS_PRIMITIVE}] {
        puts $f [join [list [get_property NAME $c] [get_property REF_NAME $c] [get_property LOC $c] [get_property BEL $c]] "\t"]
    }
    close $f
}

proc xt_dump_paths {fn n} {
    set f [open $fn w]
    foreach p [get_timing_paths -setup -max_paths $n -nworst 1 -unique_pins] {
        set cells {}
        foreach c [get_cells -of_objects $p] { lappend cells [get_property NAME $c] }
        puts $f [join [list [get_property SLACK $p] [get_property DATAPATH_DELAY $p] [get_property DATAPATH_LOGIC_DELAY $p] \
                           [get_property DATAPATH_NET_DELAY $p] [get_property STARTPOINT_PIN $p] [get_property ENDPOINT_PIN $p] \
                           [join $cells " "]] "\t"]
    }
    close $f
}

file mkdir $CONFIG_OUTROOT
foreach name $CONFIG_NAMES {
    set src $CONFIG_SRCROOT/$name
    set out $CONFIG_OUTROOT/$name
    file mkdir $out
    if {[file exists $out/status.txt]} { puts "skip: $out/status.txt exists"; continue }
    puts "XTIME_BEGIN $name"
    set top [string trim [read [open $src/top.txt]]]
    set mode [string trim [read [open $src/mode.txt]]]
    set part [expr {[file exists $src/part.txt] ? [string trim [read [open $src/part.txt]]] : $CONFIG_PART}]
    set tf [open $out/times.txt w]
    set ::cur_step read
    set rc [catch {
        create_project -in_memory -part $part
        file copy -force $src/netlist.edf $out/$top.edf
        read_edif $out/$top.edf
        link_design -top $top -part $part
        read_xdc $src/constraints.xdc
        if {$mode eq "free"} {
            step $tf opt { opt_design }
        }
        if {[file exists $src/place.txt]} {
            set placed 0
            set missed {}
            set fixed {}
            set pf [open $src/place.txt]
            while {[gets $pf line] >= 0} {
                lassign $line cell loc
                set c [get_cells -quiet $cell]
                if {$c eq ""} { lappend missed $cell; continue }
                if {[catch { place_cell $c $loc } err]} { lappend missed "$cell $loc $err"; continue }
                incr placed
                lappend fixed $c
            }
            close $pf
            set mf [open $out/place_missed.txt w]
            puts $mf "placed $placed"
            foreach m $missed { puts $mf $m }
            close $mf
            if {[llength $fixed]} {
                set_property IS_LOC_FIXED 1 $fixed
                set_property IS_BEL_FIXED 1 $fixed
            }
        }
        step $tf place { place_design }
        step $tf route { route_design }
        report_utilization -file $out/util.rpt
        report_timing_summary -file $out/timing.rpt
        report_timing -max_paths 10 -nworst 1 -input_pins -file $out/paths.rpt
        if {[file exists $src/dump.flag]} {
            xt_dump_cells $out/cells.txt
            xt_dump_paths $out/paths.txt 1000
        }
        if {[file exists $src/endpoints.flag]} {
            catch { report_timing_summary -max_paths 10 -report_unconstrained -check_timing_verbose -file $out/timing_full.rpt }
            catch { report_timing -hold -max_paths 10 -nworst 1 -input_pins -file $out/paths_hold.rpt }
            catch { report_clock_interaction -file $out/clock_interaction.rpt }
            catch { report_pulse_width -file $out/pulse_width.rpt }
            catch { report_pulse_width -all -file $out/pulse_width_all.rpt }
            catch { report_cdc -file $out/cdc.rpt }
            catch { report_methodology -file $out/methodology.rpt }
        }
        set paths [get_timing_paths -setup -max_paths 2000 -nworst 1 -unique_pins]
        set wf [open $out/worst_paths.txt w]
        foreach p $paths {
            puts $wf [format "%s %s %s" [get_property SLACK $p] [get_property STARTPOINT_PIN $p] [get_property ENDPOINT_PIN $p]]
        }
        close $wf
        if {[file exists $src/endpoints.flag]} {
            foreach {kind fn} {setup endpoints_setup.txt hold endpoints_hold.txt} {
                set ef [open $out/$fn w]
                foreach p [get_timing_paths -$kind -max_paths 200000 -nworst 1 -unique_pins] {
                    set ep [get_property ENDPOINT_PIN $p]
                    set c [get_cells -quiet -of_objects [get_pins -quiet $ep]]
                    set ref [expr {$c eq "" ? "port" : [get_property REF_NAME $c]}]
                    puts $ef [format "%s %s %s %s {%s} {%s}" [get_property SLACK $p] $ref $ep \
                        [get_property STARTPOINT_PIN $p] [get_property STARTPOINT_CLOCK $p] [get_property ENDPOINT_CLOCK $p]]
                }
                close $ef
            }
            set uf [open $out/check_timing.rpt w]
            puts $uf [check_timing -verbose -return_string]
            close $uf
        }
        if {[file exists $src/paths.txt]} {
            set af [open $src/paths.txt]
            set of [open $out/paths_vivado.txt w]
            while {[gets $af line] >= 0} {
                lassign $line c1 p1 c2 p2 npr
                set to [get_pins -quiet "$c2/$p2"]
                if {$to eq "" && [regexp {^(.*?)([0-9]+)$} $p2 -> base idx]} { set to [get_pins -quiet "$c2/$base\[$idx\]"] }
                set from [get_cells -quiet $c1]
                if {$from eq "" || $to eq ""} { puts $of "$npr - - - - {$c1 $p1 -> $c2 $p2 not found}"; continue }
                if {[catch {
                    set tp [get_timing_paths -setup -from $from -to $to -max_paths 1]
                    puts $of [format "%s %s %s %s %s {%s %s -> %s %s}" $npr [get_property SLACK $tp] [get_property DATAPATH_DELAY $tp] \
                        [get_property DATAPATH_LOGIC_DELAY $tp] [get_property DATAPATH_NET_DELAY $tp] $c1 $p1 $c2 $p2]
                } err]} { puts $of "$npr - - - - {$err}" }
            }
            close $af
            close $of
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
