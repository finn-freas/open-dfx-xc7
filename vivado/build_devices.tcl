set CONFIG_SRC  [lindex $argv 0]
set CONFIG_OUT  [lindex $argv 1]
set CONFIG_JOBS [lrange $argv 2 end]
set CONFIG_FAMILIES {xc7a* xc7s* xc7z* xc7k* xc7v*}

file mkdir $CONFIG_OUT
set fh [open $CONFIG_OUT/parts.txt w]
foreach pat $CONFIG_FAMILIES {
    puts $fh "$pat [llength [get_parts -quiet $pat]] [lsort -unique [get_property DEVICE [get_parts -quiet $pat]]]"
}
close $fh

foreach job $CONFIG_JOBS {
    lassign [split $job :] name part
    set src $CONFIG_SRC/$name
    set out $CONFIG_OUT/$name
    file mkdir $out
    if {[file exists $out/$name.bit]} {
        puts "skip: $out/$name.bit exists"
        continue
    }
    close_project -quiet
    create_project -in_memory -part $part
    foreach f [lsort [glob -nocomplain $src/*.v]] {
        read_verilog $f
    }
    foreach f [lsort [glob -nocomplain $src/*.xdc]] {
        read_xdc $f
    }
    synth_design -top $name -part $part
    opt_design
    place_design
    route_design
    report_utilization -file $out/util.rpt
    report_timing_summary -file $out/timing.rpt
    write_bitstream -force $out/$name.bit
    set fh [open $out/version.txt w]
    puts $fh "[version]\npart $part\nidcode [get_property IDCODE_HEX [get_parts $part]]"
    close $fh
}
