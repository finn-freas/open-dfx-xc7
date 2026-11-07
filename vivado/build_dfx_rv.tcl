set CONFIG_DESIGN [lindex $argv 0]
set CONFIG_TOP    [lindex $argv 1]
set CONFIG_SRC    [lindex $argv 2]
set CONFIG_XDC    [lindex $argv 3]
set CONFIG_OUT    [lindex $argv 4]
set CONFIG_PERIOD [expr {$argc > 5 ? [lindex $argv 5] : 10.0}]
set CONFIG_RMS    [expr {$argc > 6 ? [split [lindex $argv 6] ,] : {xor andn add rot}}]
set CONFIG_PART   xc7a35tcsg324-1
set CONFIG_RP     u_rm
set CONFIG_PBLOCK pblock_rm

file mkdir $CONFIG_OUT
cd $CONFIG_OUT
set tf [open times.txt a]
set ::budget_end [expr {[clock seconds] + (([info exists ::env(DFX_BUDGET_S)]) ? $::env(DFX_BUDGET_S) : 900)}]
proc step {name script} {
    global tf
    if {[clock seconds] > $::budget_end} {
        puts "DFX_RV_BUDGET: stopping before $name (resume by running again)"
        close $tf
        exit 0
    }
    set t0 [clock milliseconds]
    uplevel 1 $script
    puts $tf [format "%s %.2f" $name [expr {([clock milliseconds] - $t0) / 1000.0}]]
    flush $tf
}
proc have {f} {
    if {[file exists $f]} { puts "skip: $f exists"; return 1 }
    return 0
}
set xdc_p [file normalize clock_period.xdc]
set fh [open $xdc_p w]
puts $fh "create_clock -name sys_clk -period $CONFIG_PERIOD \[get_ports clk\]"
close $fh

proc timing_record {cfg} {
    global CONFIG_RP CONFIG_PBLOCK CONFIG_PERIOD
    report_timing_summary -max_paths 10 -file ${cfg}_timing.rpt
    report_utilization -pblocks [get_pblocks $CONFIG_PBLOCK] -file ${cfg}_pblock_util.rpt
    report_utilization -file ${cfg}_util.rpt
    set fh [open ${cfg}_wns.txt w]
    set all [get_timing_paths -setup -max_paths 1 -nworst 1]
    puts $fh "period $CONFIG_PERIOD"
    puts $fh "wns_all [get_property SLACK $all] [get_property STARTPOINT_PIN $all] -> [get_property ENDPOINT_PIN $all]"
    set best ""
    foreach p [get_timing_paths -setup -max_paths 4000 -nworst 1 -unique_pins] {
        set s [get_property STARTPOINT_PIN $p]
        set e [get_property ENDPOINT_PIN $p]
        if {[string match "u_icap*" $s] || [string match "u_icap*" $e]} { continue }
        set best $p
        break
    }
    if {$best ne ""} {
        puts $fh "wns_noicap [get_property SLACK $best] [get_property STARTPOINT_PIN $best] -> [get_property ENDPOINT_PIN $best]"
    }
    set rm [get_timing_paths -setup -max_paths 1 -nworst 1 -through [get_cells $CONFIG_RP]]
    if {[llength $rm]} {
        puts $fh "wns_through_rm [get_property SLACK $rm] [get_property STARTPOINT_PIN $rm] -> [get_property ENDPOINT_PIN $rm]"
    }
    set h [get_timing_paths -hold -max_paths 1 -nworst 1]
    puts $fh "whs_all [get_property SLACK $h]"
    close $fh
}

if {![have static_synth.dcp]} {
    step synth_static {
        create_project -in_memory -part $CONFIG_PART
        read_verilog [list $CONFIG_SRC/rv_soc.v $CONFIG_SRC/uart.v $CONFIG_SRC/picorv32.v $CONFIG_SRC/rm_stub.v]
        synth_design -top $CONFIG_TOP -part $CONFIG_PART -generic MEM_INIT=$CONFIG_SRC/main.hex
        write_checkpoint -force static_synth.dcp
        close_project
    }
}
foreach rm $CONFIG_RMS {
    if {[have ${rm}_synth.dcp]} { continue }
    step synth_$rm {
        create_project -in_memory -part $CONFIG_PART
        read_verilog [list $CONFIG_SRC/rm_slot_pp.v $CONFIG_SRC/rm_core_$rm.v]
        synth_design -mode out_of_context -top rm_slot -part $CONFIG_PART
        write_checkpoint -force ${rm}_synth.dcp
        close_project
    }
}
set first [lindex $CONFIG_RMS 0]
if {![have static_routed.dcp]} {
    step impl_$first {
        open_checkpoint static_synth.dcp
        read_checkpoint -cell [get_cells $CONFIG_RP] ${first}_synth.dcp
        set_property HD.RECONFIGURABLE 1 [get_cells $CONFIG_RP]
        read_xdc $CONFIG_XDC
        read_xdc $xdc_p
        read_xdc $CONFIG_SRC/pblock.xdc
        if {[file exists $CONFIG_SRC/partpin.xdc]} { read_xdc $CONFIG_SRC/partpin.xdc }
        opt_design
        place_design
        route_design
        write_checkpoint -force cfg_${first}_routed.dcp
        timing_record cfg_${first}
        update_design -cell [get_cells $CONFIG_RP] -black_box
        lock_design -level routing
        write_checkpoint -force static_routed.dcp
        close_project
    }
}
foreach rm [lrange $CONFIG_RMS 1 end] {
    if {[have cfg_${rm}_routed.dcp]} { continue }
    step impl_$rm {
        open_checkpoint static_routed.dcp
        read_checkpoint -cell [get_cells $CONFIG_RP] ${rm}_synth.dcp
        opt_design
        place_design
        route_design
        write_checkpoint -force cfg_${rm}_routed.dcp
        timing_record cfg_${rm}
        close_project
    }
}
if {![have cfg_grey_routed.dcp]} {
    step impl_grey {
        open_checkpoint static_routed.dcp
        update_design -cell [get_cells $CONFIG_RP] -buffer_ports
        place_design
        route_design
        write_checkpoint -force cfg_grey_routed.dcp
        timing_record cfg_grey
        close_project
    }
}
set cfgs {}
foreach rm $CONFIG_RMS { lappend cfgs cfg_${rm} }
lappend cfgs cfg_grey
if {![have pr_verify.rpt]} {
    step pr_verify {
        set dcps {}
        foreach c $cfgs { lappend dcps ${c}_routed.dcp }
        pr_verify -initial [lindex $dcps 0] -additional [lrange $dcps 1 end] -file pr_verify.rpt
    }
}
foreach c $cfgs {
    if {[have $c.bit]} { continue }
    step bit_$c {
        open_checkpoint ${c}_routed.dcp
        write_bitstream -force -bin_file $c
        close_project
    }
}
close $tf
puts "DFX_RV_DONE"
