set CONFIG_DESIGN [lindex $argv 0]
set CONFIG_TOP    [lindex $argv 1]
set CONFIG_SRC    [lindex $argv 2]
set CONFIG_XDC    [lindex $argv 3]
set CONFIG_OUT    [lindex $argv 4]
set CONFIG_PART   xc7a35tcsg324-1
set CONFIG_RP1    {u_rp1 rm_rp1 pblock_rp1 {count shift}}
set CONFIG_RP2    {u_rp2 rm_rp2 pblock_rp2 {count shift}}
set CONFIG_STOP   [expr {$argc > 5 ? [lindex $argv 5] : "bitstreams"}]

file mkdir $CONFIG_OUT
cd $CONFIG_OUT
lassign $CONFIG_RP1 i1 m1 p1 rms1
lassign $CONFIG_RP2 i2 m2 p2 rms2
lassign $rms1 a1 a2
lassign $rms2 b1 b2

proc have {f} {
    if {[file exists $f]} { puts "skip: $f exists"; return 1 }
    return 0
}

proc hook {} {
    global CONFIG_SRC
    if {[file exists $CONFIG_SRC/hook.tcl]} { puts "hook: sourcing $CONFIG_SRC/hook.tcl"; source $CONFIG_SRC/hook.tcl }
}

proc short {inst} { return [string range $inst 2 end] }

proc impl {name} {
    opt_design
    place_design
    route_design
    write_checkpoint -force ${name}_routed.dcp
    report_drc -file ${name}_drc.rpt
    report_timing_summary -file ${name}_timing.rpt
}

proc lock_keep {src blackbox out} {
    if {[have $out]} { return }
    open_checkpoint $src
    hook
    foreach i $blackbox { update_design -cell [get_cells $i] -black_box }
    lock_design -level routing
    write_checkpoint -force $out
    close_project
}

proc rm_into {from inst rm name {cellout ""}} {
    if {[have ${name}_routed.dcp]} { return }
    open_checkpoint $from
    hook
    read_checkpoint -cell [get_cells $inst] [short $inst]_${rm}_synth.dcp
    impl $name
    if {$cellout ne ""} { write_checkpoint -force -cell [get_cells $inst] $cellout }
    close_project
}

proc grey_into {from insts name} {
    if {[have ${name}_routed.dcp]} { return }
    open_checkpoint $from
    hook
    foreach i $insts { update_design -cell [get_cells $i] -buffer_ports }
    place_design
    route_design
    write_checkpoint -force ${name}_routed.dcp
    report_drc -file ${name}_drc.rpt
    close_project
}

if {![have static_synth.dcp]} {
    create_project -in_memory -part $CONFIG_PART
    read_verilog [list $CONFIG_SRC/$CONFIG_TOP.v $CONFIG_SRC/rm_stub.v]
    synth_design -top $CONFIG_TOP -part $CONFIG_PART
    write_checkpoint -force static_synth.dcp
    close_project
}

foreach r [list $CONFIG_RP1 $CONFIG_RP2] {
    lassign $r inst mod pb rms
    foreach rm $rms {
        set n [short $inst]_$rm
        if {[have ${n}_synth.dcp]} { continue }
        create_project -in_memory -part $CONFIG_PART
        read_verilog $CONFIG_SRC/$n.v
        synth_design -mode out_of_context -top $mod -part $CONFIG_PART
        write_checkpoint -force ${n}_synth.dcp
        close_project
    }
}

set first cfg_${a1}_${b1}
if {![have ${first}_routed.dcp]} {
    open_checkpoint static_synth.dcp
    hook
    read_checkpoint -cell [get_cells $i1] [short $i1]_${a1}_synth.dcp
    read_checkpoint -cell [get_cells $i2] [short $i2]_${b1}_synth.dcp
    set_property HD.RECONFIGURABLE 1 [get_cells [list $i1 $i2]]
    read_xdc $CONFIG_XDC
    read_xdc $CONFIG_SRC/pblock.xdc
    report_drc -file ${first}_pre_place_drc.rpt
    impl $first
    foreach pb [list $p1 $p2] { report_utilization -pblocks [get_pblocks $pb] -file ${first}_${pb}_util.rpt }
    close_project
}
if {$CONFIG_STOP eq "first"} { return }

lock_keep ${first}_routed.dcp [list $i1 $i2] static_routed.dcp
lock_keep ${first}_routed.dcp [list $i1] keep_[short $i2]_${b1}.dcp
lock_keep ${first}_routed.dcp [list $i2] keep_[short $i1]_${a1}.dcp

rm_into keep_[short $i2]_${b1}.dcp $i1 $a2 cfg_${a2}_${b1} [short $i1]_${a2}_routed_cell.dcp
rm_into keep_[short $i1]_${a1}.dcp $i2 $b2 cfg_${a1}_${b2} [short $i2]_${b2}_routed_cell.dcp

set last cfg_${a2}_${b2}
if {![have ${last}_routed.dcp]} {
    open_checkpoint static_routed.dcp
    hook
    read_checkpoint -cell [get_cells $i1] [short $i1]_${a2}_routed_cell.dcp
    read_checkpoint -cell [get_cells $i2] [short $i2]_${b2}_routed_cell.dcp
    place_design
    route_design
    write_checkpoint -force ${last}_routed.dcp
    report_drc -file ${last}_drc.rpt
    close_project
}

grey_into static_routed.dcp [list $i1 $i2] cfg_grey_grey
grey_into keep_[short $i2]_${b1}.dcp [list $i1] cfg_grey_${b1}
grey_into keep_[short $i1]_${a1}.dcp [list $i2] cfg_${a1}_grey
if {$CONFIG_STOP eq "routed"} { return }

set cfgs [lsort [glob cfg_*_routed.dcp]]
hook
if {![have pr_verify_all.rpt]} {
    if {[catch {pr_verify -initial [lindex $cfgs 0] -additional [lrange $cfgs 1 end] -file pr_verify_all.rpt} err]} {
        puts "PR_VERIFY_ERROR: $err"
    }
}

foreach d $cfgs {
    set c [string range $d 0 end-11]
    if {[have $c.bit]} { continue }
    open_checkpoint $d
    hook
    if {[catch {write_bitstream -force -bin_file -logic_location_file $c} err]} { puts "WRITE_BITSTREAM_ERROR $c: $err" }
    close_project
}

set fh [open version.txt w]
puts $fh [version]
close $fh
