set CONFIG_PART       xc7a35tcsg324-1
set CONFIG_SRCROOT    [lindex $argv 0]
set CONFIG_OUTROOT    [lindex $argv 1]
set CONFIG_NAMES      [lrange $argv 2 end]
set CONFIG_DIRECTIVES {Default Explore ExtraTimingOpt}
set CONFIG_NPATHS     1000
set CONFIG_NCELLS     300

proc step {fh name script} {
    set ::cur_step $name
    set t0 [clock milliseconds]
    uplevel 1 $script
    puts $fh [format "%s %.2f" $name [expr {([clock milliseconds] - $t0) / 1000.0}]]
    flush $fh
}

proc dump_paths {fname npaths ncells} {
    set paths [get_timing_paths -setup -max_paths $npaths -nworst 1 -unique_pins]
    set wf [open $fname w]
    set i 0
    foreach p $paths {
        set luts -
        set carry -
        set muxf -
        if {$i < $ncells} {
            set cells [get_cells -quiet -of_objects $p]
            set luts [llength [filter -quiet $cells {REF_NAME =~ LUT*}]]
            set carry [llength [filter -quiet $cells {REF_NAME == CARRY4}]]
            set muxf [llength [filter -quiet $cells {REF_NAME =~ MUXF*}]]
        }
        puts $wf [format "%s %s %s %s %s %s %s %s %s %s %s %s %s" [get_property SLACK $p] [get_property REQUIREMENT $p] \
            [get_property LOGIC_LEVELS $p] $luts $carry $muxf [get_property DATAPATH_DELAY $p] \
            [get_property DATAPATH_LOGIC_DELAY $p] [get_property DATAPATH_NET_DELAY $p] \
            [get_property STARTPOINT_CLOCK $p] [get_property ENDPOINT_CLOCK $p] \
            [get_property STARTPOINT_PIN $p] [get_property ENDPOINT_PIN $p]]
        incr i
    }
    close $wf
}

file mkdir $CONFIG_OUTROOT
foreach name $CONFIG_NAMES {
    set src $CONFIG_SRCROOT/$name
    set out $CONFIG_OUTROOT/$name
    file mkdir $out
    if {[file exists $out/status.txt]} { puts "skip: $out/status.txt exists"; continue }
    puts "SYNX_BEGIN $name"
    set top [string trim [read [open $src/top.txt]]]
    set mode [string trim [read [open $src/mode.txt]]]
    set dirs $CONFIG_DIRECTIVES
    if {[file exists $src/directives.txt]} { set dirs [string trim [read [open $src/directives.txt]]] }
    set tf [open $out/times.txt w]
    set ::cur_step read
    set rc [catch {
        create_project -in_memory -part $CONFIG_PART
        cd $src
        if {$mode eq "rtl"} {
            foreach f [concat [glob -nocomplain $src/*.v] [glob -nocomplain $src/*.sv]] { read_verilog -sv $f }
            read_xdc [glob $src/*.xdc]
            set sopts {}
            if {[file exists $src/synth_opts.txt]} { set sopts [string trim [read [open $src/synth_opts.txt]]] }
            puts "SYNX_SYNTH_OPTS $name: $sopts"
            step $tf synth { synth_design -top $top -part $CONFIG_PART {*}$sopts }
        } else {
            file copy -force $src/netlist.edf $out/$top.edf
            read_edif $out/$top.edf
            step $tf link { link_design -top $top -part $CONFIG_PART }
            read_xdc [glob $src/*.xdc]
        }
        report_utilization -file $out/synth_util.rpt
        step $tf opt { opt_design }
        report_utilization -file $out/opt_util.rpt
        report_design_analysis -logic_level_distribution -logic_level_dist_paths 5000 -file $out/opt_lld.rpt
        dump_paths $out/opt_paths.txt $CONFIG_NPATHS $CONFIG_NCELLS
        write_checkpoint -force $out/opt.dcp
        close_project
        foreach d $dirs {
            set o $out/$d
            file mkdir $o
            open_checkpoint $out/opt.dcp
            step $tf "place_$d" { place_design -directive $d }
            step $tf "route_$d" { route_design }
            report_utilization -file $o/util.rpt
            report_timing_summary -file $o/timing.rpt
            report_design_analysis -logic_level_distribution -logic_level_dist_paths 5000 -file $o/lld.rpt
            dump_paths $o/paths.txt $CONFIG_NPATHS $CONFIG_NCELLS
            close_project
        }
        file delete -force $out/opt.dcp
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
