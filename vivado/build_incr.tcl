set src_ref  [lindex $argv 0]
set src_edit [lindex $argv 1]
set out      [lindex $argv 2]
file mkdir $out

proc step {fh name script} {
    set t0 [clock milliseconds]
    uplevel 1 $script
    puts $fh [format "%s %.2f" $name [expr {([clock milliseconds] - $t0) / 1000.0}]]
    flush $fh
}

proc one {src out run {ref_dcp ""}} {
    file mkdir $out/$run
    set part [string trim [read [open $src/part.txt]]]
    set top [string trim [read [open $src/top.txt]]]
    set tf [open $out/$run/times.txt w]
    puts $tf "threads [get_param general.maxThreads]"
    set rc [catch {
        create_project -in_memory -part $part
        foreach f [glob -nocomplain $src/*.v] { read_verilog -sv $f }
        read_xdc [glob $src/*.xdc]
        cd $src
        step $tf synth { synth_design -top $top -part $part }
        step $tf opt { opt_design }
        if {$ref_dcp ne ""} {
            step $tf read_checkpoint_incremental { read_checkpoint -incremental $ref_dcp }
        }
        step $tf place { place_design }
        step $tf route { route_design }
        report_timing_summary -file $out/$run/timing.rpt
        report_utilization -file $out/$run/util.rpt
        if {$ref_dcp ne ""} { report_incremental_reuse -file $out/$run/incremental_reuse.rpt }
        if {$run eq "ref"} { write_checkpoint -force $out/ref_routed.dcp }
        set p [get_timing_paths -max_paths 1 -nworst 1 -setup]
        puts $tf [format "wns %s" [get_property SLACK $p]]
    } err]
    close $tf
    set sf [open $out/$run/status.txt w]
    puts $sf "rc $rc"
    if {$rc} { puts $sf "error $err" }
    close $sf
    catch { close_project }
}

one $src_ref $out ref
one $src_edit $out full
one $src_edit $out incr $out/ref_routed.dcp
