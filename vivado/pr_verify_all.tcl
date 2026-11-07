set CONFIG_OUT    [lindex $argv 4]
set CONFIG_REPORT pr_verify_all.rpt

cd $CONFIG_OUT
set cfgs [lsort [glob cfg_*_routed.dcp]]
pr_verify -initial [lindex $cfgs 0] -additional [lrange $cfgs 1 end] -file $CONFIG_REPORT
