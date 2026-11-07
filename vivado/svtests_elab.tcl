set manifest [lindex $argv 0]
set part [expr {[llength $argv] > 1 ? [lindex $argv 1] : "xc7a35tcsg324-1"}]
set fh [open $manifest r]
set lines [split [read $fh] "\n"]
close $fh
if {[llength $argv] > 3} {
    set first [lindex $argv 2]
    set lines [lrange $lines $first [expr {$first + [lindex $argv 3] - 1}]]
}
foreach line $lines {
    if {[string trim $line] eq ""} { continue }
    lassign [split $line "\t"] name top files incdirs defines
    puts "SVT_BEGIN $name"
    set t0 [clock milliseconds]
    catch {close_project -quiet}
    create_project -in_memory -part $part
    set rc 0
    if {[catch {read_verilog -sv $files} err]} {
        puts "ERROR: read_verilog: $err"
        set rc 1
    }
    if {$rc == 0} {
        set args [list -rtl -part $part]
        if {$top ne ""} { lappend args -top $top }
        if {[llength $incdirs]} { lappend args -include_dirs $incdirs }
        if {[llength $defines]} { lappend args -verilog_define $defines }
        if {[catch {synth_design {*}$args} err]} {
            puts "ERROR: synth_design: $err"
            set rc 1
        }
    }
    set secs [format %.1f [expr {([clock milliseconds] - $t0) / 1000.0}]]
    puts "SVT_END $name $rc $secs"
}
catch {close_project -quiet}
