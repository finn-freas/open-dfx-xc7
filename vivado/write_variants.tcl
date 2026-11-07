set CONFIG_DESIGN [lindex $argv 0]
set CONFIG_TOP    [lindex $argv 1]
set CONFIG_SRC    [lindex $argv 2]
set CONFIG_XDC    [lindex $argv 3]
set CONFIG_OUT    [lindex $argv 4]
set CONFIG_PBLOCKS {pblock_rm pblock_rp1 pblock_rp2}
set CONFIG_VARIANTS {rar cmp rarcmp}
if {$argc > 5} { set CONFIG_VARIANTS [split [join [lrange $argv 5 end] ,] ,] }
array set CONFIG_PROPS {
    rar    {RESET_AFTER_RECONFIG TRUE COMPRESS FALSE}
    cmp    {RESET_AFTER_RECONFIG FALSE COMPRESS TRUE}
    rarcmp {RESET_AFTER_RECONFIG TRUE COMPRESS TRUE}
}

cd $CONFIG_OUT
set cfgs {}
foreach f [lsort [glob cfg_*_routed.dcp]] { lappend cfgs [string range $f 0 end-11] }
puts "configurations: $cfgs"

foreach v $CONFIG_VARIANTS {
    array set p $CONFIG_PROPS($v)
    file mkdir $v
    foreach c $cfgs {
        if {[file exists $v/$c.bit]} { puts "skip: $v/$c.bit exists"; continue }
        open_checkpoint ${c}_routed.dcp
        set pbs [get_pblocks -quiet $CONFIG_PBLOCKS]
        foreach pb $pbs { set_property RESET_AFTER_RECONFIG $p(RESET_AFTER_RECONFIG) $pb }
        set_property BITSTREAM.GENERAL.COMPRESS $p(COMPRESS) [current_design]
        foreach pb $pbs {
            puts "variant $v $c $pb: RESET_AFTER_RECONFIG=[get_property RESET_AFTER_RECONFIG $pb] COMPRESS=[get_property BITSTREAM.GENERAL.COMPRESS [current_design]] SNAPPING_MODE=[get_property SNAPPING_MODE $pb] GRID_RANGES=[get_property GRID_RANGES $pb]"
        }
        report_drc -file $v/${c}_drc.rpt
        if {[catch {write_bitstream -force -bin_file -logic_location_file $v/$c} err]} { puts "WRITE_BITSTREAM_ERROR $v $c: $err" }
        close_project
    }
}
