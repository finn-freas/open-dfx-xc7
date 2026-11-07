set CONFIG_PART      xc7a35tcsg324-1
set CONFIG_DESIGN    [lindex $argv 0]
set CONFIG_TOP       [lindex $argv 1]
set CONFIG_SRC       [lindex $argv 2]
set CONFIG_XDC       [lindex $argv 3]
set CONFIG_OUT       [lindex $argv 4]

file mkdir $CONFIG_OUT
if {[file exists $CONFIG_OUT/$CONFIG_TOP.bit]} {
    puts "skip: $CONFIG_OUT/$CONFIG_TOP.bit exists"
    exit 0
}
foreach f [concat [glob -nocomplain $CONFIG_SRC/*.v] [glob -nocomplain $CONFIG_SRC/*.sv]] {
    read_verilog -sv $f
}
read_xdc $CONFIG_XDC
synth_design -top $CONFIG_TOP -part $CONFIG_PART
report_utilization -file $CONFIG_OUT/synth_util.rpt
opt_design
place_design
route_design
report_utilization -file $CONFIG_OUT/util.rpt
report_timing_summary -file $CONFIG_OUT/timing.rpt
write_checkpoint -force $CONFIG_OUT/routed.dcp
write_bitstream -force -logic_location_file $CONFIG_OUT/$CONFIG_TOP.bit
set fh [open $CONFIG_OUT/version.txt w]
puts $fh [version]
close $fh
