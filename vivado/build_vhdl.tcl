set CONFIG_PART xc7a35tcsg324-1
set CONFIG_SRC  [lindex $argv 0]
set CONFIG_OUT  [lindex $argv 1]
set CONFIG_NAMES [lrange $argv 2 end]

foreach name $CONFIG_NAMES {
    set src $CONFIG_SRC/$name
    set out $CONFIG_OUT/$name
    file mkdir $out
    if {[file exists $out/timing.rpt]} {
        puts "skip: $out/timing.rpt exists"
        continue
    }
    close_project -quiet
    create_project -in_memory -part $CONFIG_PART
    set vhd [lsort [glob -nocomplain $src/*.vhd]]
    if {[llength $vhd]} {
        read_vhdl -vhdl2008 $vhd
    }
    foreach f [lsort [glob -nocomplain $src/*.v]] {
        read_verilog $f
    }
    read_xdc $src/constraints.xdc
    synth_design -top $name -part $CONFIG_PART
    report_utilization -file $out/synth_util.rpt
    opt_design
    place_design
    route_design
    report_utilization -file $out/util.rpt
    report_timing_summary -file $out/timing.rpt
    set fh [open $out/version.txt w]
    puts $fh [version]
    close $fh
}
