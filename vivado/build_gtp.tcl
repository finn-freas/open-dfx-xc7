set srcroot [lindex $argv 0]
set outroot [lindex $argv 1]
foreach job [lrange $argv 2 end] {
    lassign [split $job :] name top part
    set src $srcroot/$name
    set out $outroot/$name
    file mkdir $out
    if {[catch {
        create_project -in_memory -part $part
        read_verilog [glob $src/*.v]
        read_xdc [glob $src/*.xdc]
        synth_design -top $top -part $part
        if {[string match fz_* $name]} {
            # Fuzz specimens use GT inputs Vivado reserves for test (GTGREFCLK0/1); prjxray fuzzers downgrade the same
            # DRC to get a bitstream. Reference designs keep every DRC at its default severity.
            set_property SEVERITY Warning [get_drc_checks REQP-49]
        }
        opt_design
        place_design
        route_design
        set fh [open $out/cells.txt w]
        foreach c [get_cells -hier -filter {REF_NAME =~ GTPE2_* || REF_NAME == IBUFDS_GTE2 || REF_NAME == PCIE_2_1}] {
            puts $fh "CELL $c [get_property REF_NAME $c] [get_property LOC $c]"
            foreach p [lsort [list_property $c]] { puts $fh "  $p=[get_property $p $c]" }
        }
        close $fh
        report_utilization -file $out/util.txt
        report_timing_summary -file $out/timing.txt
        set_property BITSTREAM.GENERAL.COMPRESS FALSE [current_design]
        write_bitstream -force $out/$name.bit
        write_checkpoint -force $out/$name.dcp
        close_project
        puts "JOB_OK $name"
    } err]} {
        puts "JOB_FAIL $name: $err"
        catch {close_project}
    }
}
puts "BUILD_GTP_DONE"
