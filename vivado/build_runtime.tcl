set src [lindex $argv 0]
set out [lindex $argv 1]
set tag [lindex $argv 2]
file mkdir $out
proc step {fh name script} {
    set t0 [clock milliseconds]
    uplevel 1 $script
    puts $fh [format "%s %.2f" $name [expr {([clock milliseconds] - $t0) / 1000.0}]]
    flush $fh
}
set part [string trim [read [open $src/part.txt]]]
set top [string trim [read [open $src/top.txt]]]
set tf [open $out/times.txt w]
puts $tf "threads [get_param general.maxThreads]"
puts $tf "part $part"
set rc [catch {
    step $tf read {
        create_project -in_memory -part $part
        foreach f [concat [glob -nocomplain $src/*.v] [glob -nocomplain $src/*.sv]] { read_verilog -sv $f }
        read_xdc [glob $src/*.xdc]
    }
    cd $src
    step $tf synth { synth_design -top $top -part $part }
    step $tf opt { opt_design }
    step $tf place { place_design }
    step $tf route { route_design }
    step $tf bitstream { write_bitstream -force $out/$tag.bit }
    report_utilization -file $out/util.rpt
    report_timing_summary -file $out/timing.rpt
} err]
close $tf
set sf [open $out/status.txt w]
puts $sf "rc $rc"
if {$rc} { puts $sf "error $err" }
close $sf
