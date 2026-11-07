set CONFIG_PART    xc7a35tcsg324-1
set CONFIG_SRCROOT [lindex $argv 0]
set CONFIG_OUTROOT [lindex $argv 1]
set CONFIG_NAMES   [lrange $argv 2 end]

file mkdir $CONFIG_OUTROOT

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
        if {$kind eq "from_ports"} {
            set p [get_timing_paths -quiet -setup -from [all_inputs] -max_paths 1 -nworst 1]
        } else {
            set p [get_timing_paths -quiet -setup -to [all_outputs] -max_paths 1 -nworst 1]
        }
        if {[llength $p] == 0} { continue }
        puts $fh [format "%s slack %s req %s datapath %s start %s end %s" $kind [get_property SLACK $p] \
            [get_property REQUIREMENT $p] [get_property DATAPATH_DELAY $p] [get_property STARTPOINT_PIN $p] \
            [get_property ENDPOINT_PIN $p]]
    }
}

proc pad_arcs {fh} {
    foreach p [lsort [get_ports]] {
        foreach c [get_cells -quiet -of_objects [get_nets -quiet -of_objects $p] -filter {IS_PRIMITIVE && REF_NAME =~ *BUF*}] {
            foreach a [get_timing_arcs -quiet -of_objects $c] {
                set vals {}
                foreach k {DELAY_SLOW_MAX_RISE DELAY_SLOW_MAX_FALL DELAY_SLOW_MIN_RISE DELAY_SLOW_MIN_FALL DELAY_FAST_MAX_RISE DELAY_FAST_MAX_FALL DELAY_FAST_MIN_RISE DELAY_FAST_MIN_FALL} {
                    lappend vals $k=[get_property -quiet $k $a]
                }
                puts $fh [format "port %s cell %s ref %s site %s iostd %s drive %s slew %s from %s to %s %s" $p $c                     [get_property REF_NAME $c] [get_property -quiet LOC $c] [get_property -quiet IOSTANDARD $p]                     [get_property -quiet DRIVE $p] [get_property -quiet SLEW $p] [get_property FROM_PIN $a]                     [get_property TO_PIN $a] [join $vals " "]]
            }
        }
    }
}

foreach name $CONFIG_NAMES {
    set src $CONFIG_SRCROOT/$name
    set out $CONFIG_OUTROOT/$name
    file mkdir $out
    if {[file exists $out/status.txt]} { puts "skip: $out/status.txt exists"; continue }
    puts "XDC_BEGIN $name"
    set ::cur_step read
    set rc [catch {
        create_project -in_memory -part $CONFIG_PART
        foreach f [glob -nocomplain $src/*.v] { read_verilog -sv $f }
        read_xdc [glob $src/*.xdc]
        set ::cur_step synth
        synth_design -top $name -part $CONFIG_PART
        set cf [open $out/synth_cells.txt w]
        foreach c [get_cells -hierarchical -filter {IS_PRIMITIVE}] {
            puts $cf [format "%s %s ASYNC_REG=%s" [get_property REF_NAME $c] $c [get_property -quiet ASYNC_REG $c]]
        }
        close $cf
        set ::cur_step opt
        opt_design
        set ::cur_step place
        place_design
        set ::cur_step route
        route_design
        report_timing_summary -file $out/timing.rpt
        report_clocks -file $out/clocks.rpt
        report_clock_interaction -file $out/clock_interaction.rpt
        report_exceptions -file $out/exceptions.rpt
        check_timing -verbose -file $out/check_timing.rpt
        report_io -file $out/io.rpt
        report_drc -file $out/drc.rpt
        report_timing -setup -max_paths 3 -nworst 1 -file $out/paths.rpt
        set pf [open $out/pairs.txt w]
        clock_pairs $pf
        close $pf
        set af [open $out/pad_arcs.txt w]
        pad_arcs $af
        close $af
        set a0 [lindex [get_timing_arcs -quiet -of_objects [get_cells -quiet -hierarchical -filter {REF_NAME == OBUF}]] 0]
        if {$a0 ne ""} { report_property $a0 -file $out/arc_props.txt }
        report_timing -from [all_inputs] -max_paths 200 -nworst 1 -file $out/in_paths.rpt
        report_timing -to [all_outputs] -max_paths 200 -nworst 1 -file $out/out_paths.rpt
        report_timing -hold -from [all_inputs] -max_paths 200 -nworst 1 -file $out/in_hold.rpt
        report_timing -hold -max_paths 3 -nworst 1 -file $out/hold_paths.rpt
        set lf [open $out/placed_cells.txt w]
        foreach c [get_cells -hierarchical -filter {IS_PRIMITIVE}] {
            puts $lf [format "%s %s %s %s" [get_property REF_NAME $c] $c [get_property -quiet LOC $c] [get_property -quiet BEL $c]]
        }
        close $lf
        set ::cur_step bitstream
        write_bitstream -force $out/$name.bit
    } err]
    set sf [open $out/status.txt w]
    puts $sf "rc $rc"
    if {$rc} { puts $sf "step $::cur_step"; puts $sf "error $err" }
    close $sf
    catch { close_project }
}
set fh [open $CONFIG_OUTROOT/version.txt w]
puts $fh [version]
close $fh
