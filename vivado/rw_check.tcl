set CONFIG_PAIRS [lrange $argv 0 end]
set CONFIG_DIAG_NETS 40

foreach {dcp out} $CONFIG_PAIRS {
    file mkdir $out
    set sf [open $out/status.txt w]
    set t0 [clock milliseconds]
    set rc [catch {
        open_checkpoint $dcp
        puts $sf "open_s [expr {([clock milliseconds] - $t0) / 1000.0}]"
        report_route_status -file $out/route_status.rpt
        set bad [get_nets -quiet -hierarchical -top_net_of_hierarchical_group -filter {ROUTE_STATUS != ROUTED && ROUTE_STATUS != NOLOADS && ROUTE_STATUS != INTRASITE}]
        set bf [open $out/bad_nets.txt w]
        foreach n $bad { puts $bf "$n\t[get_property ROUTE_STATUS $n]" }
        close $bf
        set df [open $out/route_diag.txt w]
        foreach n [lrange $bad 0 [expr {$::CONFIG_DIAG_NETS - 1}]] {
            puts $df [report_route_status -of_objects $n -return_string]
        }
        close $df
        set pf [open $out/vpips.txt w]
        foreach n [get_nets -hierarchical -top_net_of_hierarchical_group -filter {ROUTE_STATUS != NOLOADS}] {
            foreach p [get_pips -quiet -of_objects $n] { puts $pf "$n\t$p" }
        }
        close $pf
        report_utilization -file $out/util.rpt
        report_drc -file $out/drc.rpt
        report_timing_summary -file $out/timing.rpt
    } err]
    puts $sf "rc $rc"
    if {$rc} { puts $sf "error $err" }
    close $sf
    catch { close_design }
}
