set CONFIG_DESIGN [lindex $argv 0]
set CONFIG_TOP    [lindex $argv 1]
set CONFIG_SRC    [lindex $argv 2]
set CONFIG_XDC    [lindex $argv 3]
set CONFIG_OUT    [lindex $argv 4]
set CONFIG_RPS    {u_rm u_rp1 u_rp2}
set CONFIG_DIR    pips

cd $CONFIG_OUT
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
