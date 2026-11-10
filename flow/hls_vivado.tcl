set W [pwd]
set part xc7a35tcsg324-1
set fp [open designs.txt r]
set names [split [string trim [read $fp]] "\n"]
close $fp
foreach n $names {
  if {[file exists $W/$n/status.txt]} { continue }
  cd $W/$n
  set t0 [clock seconds]
  if {[catch {
    set fp [open top.txt r]; lassign [split [string trim [read $fp]]] top kernel; close $fp
    foreach f [glob -nocomplain *.v] { read_verilog $f }
    read_xdc hlsw.xdc
    synth_design -top $top -part $part -verilog_define HLSW_KEEP
    report_utilization -hierarchical -file util_hier_synth.rpt
    opt_design
    place_design
    phys_opt_design
    route_design
    report_utilization -hierarchical -file util_hier.rpt
    report_utilization -file util.rpt
    report_timing_summary -file timing.rpt
    set fo [open result.txt w]
    puts $fo "wns [get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 -setup]]"
    close $fo
    set counts [dict create]
    foreach c [get_cells -hier -filter {IS_PRIMITIVE && NAME =~ u_k/*}] {
      dict incr counts [get_property REF_NAME $c]
    }
    set fo [open kcells.txt w]
    dict for {r n} $counts { puts $fo "$r $n" }
    close $fo
  } err]} {
    set fo [open status.txt w]; puts $fo "FAIL $err"; close $fo
  } else {
    set fo [open status.txt w]; puts $fo "OK [expr {[clock seconds] - $t0}]s"; close $fo
  }
  close_project -quiet
}
exit
