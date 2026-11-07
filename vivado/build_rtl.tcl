set CONFIG_PART xc7a35tcsg324-1
set CONFIG_SRC  [lindex $argv 0]
set CONFIG_OUT  [lindex $argv 1]
set CONFIG_NAMES [lrange $argv 2 end]

proc slurp {f} { set fh [open $f r]; set s [string trim [read $fh]]; close $fh; return $s }

foreach name $CONFIG_NAMES {
    set src $CONFIG_SRC/$name
    set out $CONFIG_OUT/$name
    file mkdir $out
    if {[file exists $out/timing.rpt]} {
        puts "skip: $out/timing.rpt exists"
        continue
    }
    cd $src
    set top [expr {[file exists $src/top.txt] ? [slurp $src/top.txt] : $name}]
    set part [expr {[file exists $src/part.txt] ? [slurp $src/part.txt] : $CONFIG_PART}]
    close_project -quiet
    create_project -in_memory -part $part
    set v [lsort [glob -nocomplain $src/*.v]]
    set sv [lsort [glob -nocomplain $src/*.sv]]
    if {[llength $sv]} { read_verilog -sv [concat $sv $v] } else { read_verilog $v }
    read_xdc $src/constraints.xdc
    set t0 [clock seconds]
    set args [list -top $top -part $part]
    if {[file exists $src/defines.txt]} { lappend args -verilog_define [slurp $src/defines.txt] }
    if {[file exists $src/incdirs.txt]} { lappend args -include_dirs [slurp $src/incdirs.txt] }
    synth_design {*}$args
    set t1 [clock seconds]
    report_utilization -file $out/synth_util.rpt
    opt_design
    place_design
    route_design
    set t2 [clock seconds]
    report_utilization -file $out/util.rpt
    report_utilization -hierarchical -file $out/util_hier.rpt
    report_timing_summary -file $out/timing.rpt
    report_timing -delay_type min_max -max_paths 40 -nworst 1 -from [all_inputs] -file $out/io_in.rpt
    report_timing -delay_type min_max -max_paths 40 -nworst 1 -to [all_outputs] -file $out/io_out.rpt
    write_checkpoint -force $out/${name}_routed.dcp
    if {[file exists $src/bitstream.txt]} { write_bitstream -force $out/$name.bit }
    set fh [open $out/times.txt w]
    puts $fh "synth [expr {$t1 - $t0}]\nimpl [expr {$t2 - $t1}]"
    close $fh
    set fh [open $out/version.txt w]
    puts $fh [version]
    close $fh
}
