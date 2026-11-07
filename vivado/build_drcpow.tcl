set CONFIG_PART    xc7a35tcsg324-1
set CONFIG_SRCROOT [lindex $argv 0]
set CONFIG_OUTROOT [lindex $argv 1]
set CONFIG_NAMES   [lrange $argv 2 end]

file mkdir $CONFIG_OUTROOT

set ck $CONFIG_OUTROOT/drc_checks.txt
if {![file exists $ck]} {
    create_project -in_memory -part $CONFIG_PART
    set fh [open $ck w]
    foreach c [get_drc_checks] {
        puts $fh [format "%s\t%s\t%s\t%s" $c [get_property SEVERITY $c] [get_property IS_ENABLED $c] [get_property -quiet DESCRIPTION $c]]
    }
    close $fh
    set fh [open $CONFIG_OUTROOT/drc_decks.txt w]
    foreach d [get_drc_ruledecks] {
        puts $fh "DECK $d [join [get_drc_checks -quiet -of_objects [get_drc_ruledecks $d]] { }]"
    }
    close $fh
    close_project
}

proc step {fh name script} {
    set ::cur_step $name
    set t0 [clock milliseconds]
    uplevel 1 $script
    puts $fh [format "%s %.2f" $name [expr {([clock milliseconds] - $t0) / 1000.0}]]
    flush $fh
}

proc stamp {out what msg} {
    set sf [open $out/status.txt a]
    puts $sf "$what [string map {"\n" " | "} $msg]"
    close $sf
}

foreach entry $CONFIG_NAMES {
    set src $CONFIG_SRCROOT/$entry
    set name [file tail $entry]
    set out $CONFIG_OUTROOT/$name
    file mkdir $out
    if {[file exists $out/done.txt]} { puts "skip: $out/done.txt exists"; continue }
    file delete -force $out/status.txt
    puts "DRCPOW_BEGIN $name"
    set top $name
    if {[file exists $src/top.txt]} { set top [string trim [read [open $src/top.txt]]] }
    set tf [open $out/times.txt w]
    set ::cur_step read
    set rc [catch {
        create_project -in_memory -part $CONFIG_PART
        foreach f [concat [glob -nocomplain $src/*.v] [glob -nocomplain $src/*.sv]] { read_verilog -sv $f }
        read_xdc [glob $src/*.xdc]
        cd $src
        step $tf synth { synth_design -top $top -part $CONFIG_PART }
        step $tf opt { opt_design }
        report_drc -file $out/drc_opt.rpt
        if {[catch { step $tf place { place_design } } perr]} {
            stamp $out place_error $perr
            report_drc -file $out/drc_place_fail.rpt
            error "place: $perr"
        }
        if {![file exists $src/noroute.txt]} {
            step $tf route { route_design }
        }
        report_utilization -file $out/util.rpt
        report_drc -file $out/drc.rpt
        step $tf power { report_power -file $out/power.rpt }
        catch { report_power -format xml -file $out/power.xml }
        if {![catch { set_units -power mW }]} { catch { report_power -file $out/power_mw.rpt }; catch { set_units -power W } }
        catch { report_power -advisory -file $out/power_adv.rpt }
        report_clocks -file $out/clocks.rpt
        if {[string match drc_* $name] && [catch { step $tf bitstream { write_bitstream -force $out/$name.bit } } berr]} {
            stamp $out bitstream_error $berr
        }
    } err]
    close $tf
    stamp $out rc $rc
    if {$rc} { stamp $out step $::cur_step; stamp $out error $err }
    puts "DRCPOW_END $name rc=$rc"
    set df [open $out/done.txt w]; puts $df $rc; close $df
    catch { close_project }
}
set fh [open $CONFIG_OUTROOT/version.txt w]
puts $fh [version]
close $fh
