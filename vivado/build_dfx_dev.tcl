set CONFIG_DESIGN [lindex $argv 0]
set CONFIG_TOP    [lindex $argv 1]
set CONFIG_SRC    [lindex $argv 2]
set CONFIG_XDC    [lindex $argv 3]
set CONFIG_OUT    [lindex $argv 4]
set CONFIG_PART   [lindex $argv 5]
set CONFIG_RP     u_rm
set CONFIG_PBLOCK pblock_rm
set CONFIG_RMS    {rm_count rm_shift}
if {$argc > 6} { set CONFIG_RMS [split [join [lrange $argv 6 end] ,] ,] }

file mkdir $CONFIG_OUT
cd $CONFIG_OUT

proc have {f} {
    if {[file exists $f]} { puts "skip: $f exists"; return 1 }
    return 0
}

if {![have static_synth.dcp]} {
    create_project -in_memory -part $CONFIG_PART
    read_verilog [list $CONFIG_SRC/$CONFIG_TOP.v $CONFIG_SRC/rm_stub.v]
    synth_design -top $CONFIG_TOP -part $CONFIG_PART
    write_checkpoint -force static_synth.dcp
    close_project
}

foreach rm $CONFIG_RMS {
    if {[have ${rm}_synth.dcp]} { continue }
    create_project -in_memory -part $CONFIG_PART
    read_verilog $CONFIG_SRC/$rm.v
    synth_design -mode out_of_context -top rm_slot -part $CONFIG_PART
    write_checkpoint -force ${rm}_synth.dcp
    close_project
}

set first [lindex $CONFIG_RMS 0]
if {![have static_routed.dcp]} {
    open_checkpoint static_synth.dcp
    read_checkpoint -cell [get_cells $CONFIG_RP] ${first}_synth.dcp
    set_property HD.RECONFIGURABLE 1 [get_cells $CONFIG_RP]
    read_xdc $CONFIG_XDC
    read_xdc $CONFIG_SRC/pblock.xdc
    opt_design
    place_design
    route_design
    write_checkpoint -force cfg_${first}_routed.dcp
    report_utilization -pblocks [get_pblocks $CONFIG_PBLOCK] -file cfg_${first}_pblock_util.rpt
    report_timing_summary -file cfg_${first}_timing.rpt
    update_design -cell [get_cells $CONFIG_RP] -black_box
    lock_design -level routing
    write_checkpoint -force static_routed.dcp
    close_project
}

foreach rm [lrange $CONFIG_RMS 1 end] {
    if {[have cfg_${rm}_routed.dcp]} { continue }
    open_checkpoint static_routed.dcp
    read_checkpoint -cell [get_cells $CONFIG_RP] ${rm}_synth.dcp
    opt_design
    place_design
    route_design
    write_checkpoint -force cfg_${rm}_routed.dcp
    report_timing_summary -file cfg_${rm}_timing.rpt
    close_project
}

if {![have cfg_grey_routed.dcp]} {
    open_checkpoint static_routed.dcp
    update_design -cell [get_cells $CONFIG_RP] -buffer_ports
    place_design
    route_design
    write_checkpoint -force cfg_grey_routed.dcp
    close_project
}

set cfgs {}
foreach rm $CONFIG_RMS { lappend cfgs cfg_${rm} }
lappend cfgs cfg_grey

if {![have pr_verify.rpt]} {
    set extra {}
    foreach c [lrange $cfgs 1 end] { lappend extra ${c}_routed.dcp }
    pr_verify -initial [lindex $cfgs 0]_routed.dcp -additional $extra -file pr_verify.rpt
}

foreach c $cfgs {
    if {[have $c.bit]} { continue }
    open_checkpoint ${c}_routed.dcp
    write_bitstream -force -bin_file -logic_location_file $c
    close_project
}

set fh [open version.txt w]
puts $fh [version]
close $fh

set CONFIG_RPS {u_rm}
set CONFIG_DIR pips
file mkdir $CONFIG_DIR
set dcps [concat [list static_routed.dcp] [lsort [glob cfg_*_routed.dcp]]]

foreach d $dcps {
    set name [string range $d 0 end-4]
    if {[file exists $CONFIG_DIR/$name.pips.txt]} { puts "skip: $name"; continue }
    open_checkpoint $d
    set fh [open $CONFIG_DIR/$name.pips.txt w]
    foreach n [get_nets -hierarchical -top_net_of_hierarchical_group -filter {ROUTE_STATUS != NOLOADS}] {
        set owner static
        foreach rp $CONFIG_RPS { if {[string match "$rp/*" $n]} { set owner [expr {$rp eq "u_rm" ? "rm" : $rp}] } }
        foreach p [get_pips -quiet -of_objects $n] {
            puts $fh "$owner\t$n\t$p"
        }
    }
    close $fh
    set fh [open $CONFIG_DIR/$name.pplocs.txt w]
    foreach rp $CONFIG_RPS {
        foreach pin [get_pins -quiet $rp/*] {
            puts $fh "$pin\t[get_property HD.PARTPIN_LOCS $pin]\t[get_pplocs -quiet -pins $pin]"
        }
    }
    close $fh
    close_project
}
