set manifest [lindex $argv 0]
set outdir [lindex $argv 1]
set part xc7a35tcsg324-1
set fh [open $manifest r]
set lines [split [read $fh] "\n"]
close $fh
foreach line $lines {
    if {[string trim $line] eq ""} { continue }
    lassign [split $line "\t"] name top files incdirs defines
    file mkdir $outdir/$name
    puts "CORE_BEGIN $name"
    set t0 [clock seconds]
    catch {close_project -quiet}
    create_project -in_memory -part $part
    set rc [catch {
        read_verilog -sv $files
        synth_design -top $top -part $part -mode out_of_context -include_dirs $incdirs -verilog_define $defines
        report_utilization -file $outdir/$name/util.rpt
        report_utilization -hierarchical -file $outdir/$name/util_hier.rpt
    } err]
    if {$rc} { puts "ERROR: $err" }
    puts "CORE_END $name $rc [expr {[clock seconds] - $t0}]"
}
