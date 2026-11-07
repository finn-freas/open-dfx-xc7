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

proc clock_pairs {fh} {
    foreach lc [get_clocks -quiet] {
        foreach cc [get_clocks -quiet] {
            set p [get_timing_paths -quiet -setup -from $lc -to $cc -max_paths 1 -nworst 1]
            if {[llength $p] == 0} { continue }
            puts $fh [format "pair %s %s slack %s req %s datapath %s exception {%s} start %s end %s" \
                $lc $cc [get_property SLACK $p] [get_property REQUIREMENT $p] [get_property DATAPATH_DELAY $p] \
                [get_property EXCEPTION $p] [get_property STARTPOINT_PIN $p] [get_property ENDPOINT_PIN $p]]
        }
    }
    foreach kind {from_ports to_ports} {
        foreach delay {setup hold} {
            if {$kind eq "from_ports"} {
                set p [get_timing_paths -quiet -$delay -from [all_inputs] -max_paths 1 -nworst 1]
            } else {
                set p [get_timing_paths -quiet -$delay -to [all_outputs] -max_paths 1 -nworst 1]
            }
            if {[llength $p] == 0} { continue }
            set tag [expr {$delay eq "setup" ? $kind : "${kind}_hold"}]
            puts $fh [format "%s slack %s req %s datapath %s start %s end %s" $tag [get_property SLACK $p] \
                [get_property REQUIREMENT $p] [get_property DATAPATH_DELAY $p] [get_property STARTPOINT_PIN $p] \
                [get_property ENDPOINT_PIN $p]]
        }
    }
}

file mkdir $CONFIG_OUTROOT
foreach name $CONFIG_NAMES {
    set src $CONFIG_SRCROOT/$name
    set out $CONFIG_OUTROOT/$name
    file mkdir $out
    if {[file exists $out/status.txt]} { puts "skip: $out/status.txt exists"; continue }
    puts "XDCTIME_BEGIN $name"
    set top [string trim [read [open $src/top.txt]]]
    set tf [open $out/times.txt w]
    set ::cur_step read
    set rc [catch {
        create_project -in_memory -part $CONFIG_PART
        file copy -force $src/netlist.edf $out/$top.edf
        read_edif $out/$top.edf
        link_design -top $top -part $CONFIG_PART
        read_xdc $src/constraints.xdc
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
        step $tf place { place_design }
        step $tf route { route_design }
        report_timing_summary -file $out/timing.rpt
        report_exceptions -file $out/exceptions.rpt
        report_timing -setup -max_paths 3 -nworst 1 -input_pins -file $out/paths.rpt
        report_timing -setup -from [all_inputs] -max_paths 2 -nworst 1 -input_pins -file $out/in_setup.rpt
        report_timing -hold -from [all_inputs] -max_paths 2 -nworst 1 -input_pins -file $out/in_hold.rpt
        report_timing -setup -to [all_outputs] -max_paths 1 -nworst 1 -input_pins -file $out/out_setup.rpt
        set pf [open $out/pairs.txt w]
        clock_pairs $pf
        close $pf
        foreach {corner other} {Slow Fast Fast Slow} {
            if {[catch {
                config_timing_corners -corner $other -delay_type none
                config_timing_corners -corner $corner -delay_type min_max
                report_timing -setup -from [all_inputs] -max_paths 2 -nworst 1 -input_pins -file $out/in_setup_[string tolower $corner].rpt
                report_timing -hold -from [all_inputs] -max_paths 2 -nworst 1 -input_pins -file $out/in_hold_[string tolower $corner].rpt
                report_timing -setup -to [all_outputs] -max_paths 1 -nworst 1 -input_pins -file $out/out_setup_[string tolower $corner].rpt
                report_timing -hold -to [all_outputs] -max_paths 1 -nworst 1 -input_pins -file $out/out_hold_[string tolower $corner].rpt
                report_timing -setup -from [all_registers] -to [all_registers] -max_paths 1 -nworst 1 -input_pins -file $out/reg_setup_[string tolower $corner].rpt
                report_timing -hold -from [all_registers] -to [all_registers] -max_paths 1 -nworst 1 -input_pins -file $out/reg_hold_[string tolower $corner].rpt
            } cerr]} { puts "corner $corner: $cerr" }
        }
        catch { config_timing_corners -corner Slow -delay_type min_max ; config_timing_corners -corner Fast -delay_type min_max }
        set lf [open $out/placed_cells.txt w]
        foreach c [get_cells -hierarchical -filter {IS_PRIMITIVE}] {
            puts $lf [format "%s %s %s %s" [get_property REF_NAME $c] $c [get_property -quiet LOC $c] [get_property -quiet BEL $c]]
        }
        close $lf
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
