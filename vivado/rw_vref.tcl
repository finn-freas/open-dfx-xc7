set CONFIG_PART [lindex $argv 0]
set CONFIG_SRC  [lindex $argv 1]
set CONFIG_OUT  [lindex $argv 2]

file mkdir $CONFIG_OUT
set sf [open $CONFIG_OUT/status.txt w]
set rc [catch {
    set top [string trim [read [open $CONFIG_SRC/top.txt]]]
    create_project -in_memory -part $CONFIG_PART
    read_edif $CONFIG_SRC/netlist.edf
    link_design -top $top -part $CONFIG_PART
    read_xdc $CONFIG_SRC/constraints.xdc
    place_design
    route_design
    report_route_status -file $CONFIG_OUT/route_status.rpt
    report_timing_summary -file $CONFIG_OUT/timing.rpt
    write_checkpoint -force $CONFIG_OUT/routed.dcp
    write_edif -force $CONFIG_OUT/routed.edf
    set pf [open $CONFIG_OUT/vpips.txt w]
    foreach n [get_nets -hierarchical -top_net_of_hierarchical_group -filter {ROUTE_STATUS != NOLOADS}] {
        foreach p [get_pips -quiet -of_objects $n] { puts $pf "$n\t$p" }
    }
    close $pf
    set cf [open $CONFIG_OUT/cells.txt w]
    foreach c [get_cells -hierarchical -filter {IS_PRIMITIVE}] {
        puts $cf [join [list [get_property NAME $c] [get_property REF_NAME $c] [get_property LOC $c] [get_property BEL $c]] "\t"]
    }
    close $cf
} err]
puts $sf "rc $rc"
if {$rc} { puts $sf "error $err" }
close $sf
