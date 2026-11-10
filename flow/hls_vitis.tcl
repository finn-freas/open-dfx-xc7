set W [pwd]
set clk_ns 10
if {[info exists ::env(HLS_CLK_NS)]} { set clk_ns $::env(HLS_CLK_NS) }
set part xc7a35tcsg324-1
if {[info exists ::env(HLS_PART)]} { set part $::env(HLS_PART) }
set kernels $::env(HLS_KERNELS)
set cosim 1
if {[info exists ::env(HLS_COSIM)]} { set cosim $::env(HLS_COSIM) }
foreach k $kernels {
  cd $W
  set t0 [clock seconds]
  if {[catch {
    open_project -reset prj_$k
    set_top $k
    add_files src/$k/$k.c
    add_files -tb src/$k/tb.c -cflags "-Isrc/$k"
    open_solution -reset sol -flow_target vivado
    set_part $part
    if {[info exists ::env(HLS_DF_STRICT)]} { config_dataflow -strict_mode $::env(HLS_DF_STRICT) }
    create_clock -period $clk_ns -name default
    csim_design
    csynth_design
    if {$cosim} { cosim_design -rtl verilog }
    close_project
  } err]} {
    puts "HLS_RESULT $k FAIL $err"
    catch close_project
  } else {
    puts "HLS_RESULT $k OK [expr {[clock seconds] - $t0}]s"
  }
}
exit
