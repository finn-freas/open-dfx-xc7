set CONFIG_SRCROOT [lindex $argv 0]
set CONFIG_OUTROOT [lindex $argv 1]
set CONFIG_JOBS    [lindex $argv 2]
set CONFIG_BUDGET  [expr {[llength $argv] > 3 ? [lindex $argv 3] : 1e9}]
set CONFIG_T0      [clock seconds]
set CONFIG_DUMP_RUN 0

proc step {name script} {
    set ::cur_step $name
    set t0 [clock milliseconds]
    uplevel 1 $script
    set ::t($name) [expr {([clock milliseconds] - $t0) / 1000.0}]
}

proc readf {f} { set h [open $f]; set s [string trim [read $h]]; close $h; return $s }

proc write_xdc_for {src period dst} {
    set t [readf $src/constraints.xdc.tpl]
    set h [open $dst w]
    puts $h [string map [list @PERIOD@ [format %.3f $period]] $t]
    close $h
}

proc wns {} {
    set p [get_timing_paths -setup -max_paths 1 -nworst 1]
    if {$p eq ""} { return "" }
    return [get_property SLACK $p]
}

proc util {} {
    set r {}
    lappend r LUT [llength [get_cells -quiet -hier -filter {PRIMITIVE_GROUP == LUT}]]
    lappend r FF [llength [get_cells -quiet -hier -filter {PRIMITIVE_GROUP == FLOP_LATCH}]]
    lappend r LUTRAM [llength [get_cells -quiet -hier -filter {PRIMITIVE_GROUP == DISTRIBUTED_MEMORY || PRIMITIVE_SUBGROUP == SRL}]]
    set b36 [llength [get_cells -quiet -hier -filter {REF_NAME =~ RAMB36* || REF_NAME =~ FIFO36*}]]
    set b18 [llength [get_cells -quiet -hier -filter {REF_NAME =~ RAMB18* || REF_NAME =~ FIFO18*}]]
    lappend r BRAM36 [expr {$b36 + 0.5 * $b18}]
    lappend r DSP [llength [get_cells -quiet -hier -filter {REF_NAME =~ DSP48*}]]
    lappend r CARRY4 [llength [get_cells -quiet -hier -filter {REF_NAME == CARRY4}]]
    return $r
}

proc power {} {
    set s [report_power -return_string]
    set tot ""; set dyn ""
    regexp {Total On-Chip Power \(W\)\s*\|\s*([0-9.]+)} $s -> tot
    regexp {Dynamic \(W\)\s*\|\s*([0-9.]+)} $s -> dyn
    return [list $tot $dyn]
}

proc dump_place {out} {
    set seen [dict create]
    set nets {}
    foreach n [get_nets -quiet -hier -filter {TYPE == SIGNAL}] {
        set p [get_property PARENT $n]
        if {[dict exists $seen $p]} { continue }
        dict set seen $p 1
        lappend nets $n
    }
    set fh [open $out/nets_sites.txt w]
    foreach n $nets {
        set ss [lsort -unique [get_sites -quiet -of_objects [get_cells -quiet -of_objects [get_pins -quiet -leaf -of_objects $n]]]]
        if {[llength $ss] >= 2} { puts $fh "n [join $ss]" }
    }
    close $fh
    set cnt [dict create]
    foreach pp [get_pips -quiet -of_objects $nets] {
        set tile [lindex [split $pp /] 0]
        if {[string match INT_* $tile]} { dict incr cnt $tile }
    }
    set fh [open $out/pips_int.txt w]
    dict for {k v} $cnt { puts $fh "$k $v" }
    close $fh
}

proc write_result {out kv} {
    set h [open $out/result.txt w]
    foreach {k v} $kv { puts $h "$k $v" }
    close $h
}

proc read_result {out} {
    set r [dict create]
    foreach line [split [readf $out/result.txt] \n] {
        set k [lindex $line 0]
        dict set r $k [lrange $line 1 end]
    }
    return $r
}

proc run_free {name period i} {
    set src $::CONFIG_SRCROOT/$name
    set out $::CONFIG_OUTROOT/${name}__free/run$i
    if {[file exists $out/result.txt]} { puts "skip: $out/result.txt"; return [read_result $out] }
    file mkdir $out
    set part [readf $src/part.txt]
    set top [readf $src/top.txt]
    array unset ::t
    set ::cur_step read
    set t0 [clock milliseconds]
    set rc [catch {
        create_project -in_memory -part $part
        cd $src
        foreach f [split [readf $src/files.txt] \n] { if {$f ne ""} { read_verilog $src/$f } }
        write_xdc_for $src $period $out/constraints.xdc
        read_xdc $out/constraints.xdc
        step synth { synth_design -top $top -part $part }
        step place { opt_design; place_design }
        step route { route_design }
        set w [wns]
        set u [util]
        report_utilization -file $out/util.rpt
        report_timing_summary -file $out/timing.rpt
        set pw [power]
        step bitstream { write_bitstream -force $out/$top.bit }
        if {$i == $::CONFIG_DUMP_RUN} { step dump { dump_place $out } }
    } err]
    set total [expr {([clock milliseconds] - $t0) / 1000.0}]
    if {[info exists ::t(dump)]} { set total [expr {$total - $::t(dump)}] }
    set kv [list rc $rc period $period part $part threads [get_param general.maxThreads] t_total $total]
    foreach s {synth place route bitstream dump} { if {[info exists ::t($s)]} { lappend kv t_$s $::t($s) } }
    if {!$rc} {
        lappend kv wns $w
        foreach {k v} $u { lappend kv $k $v }
        lappend kv power_total [lindex $pw 0] power_dynamic [lindex $pw 1]
    } else {
        lappend kv step $::cur_step error [string map {\n " "} $err]
    }
    write_result $out $kv
    catch { close_project }
    return [dict create {*}$kv]
}

proc run_placed {name period tag} {
    set src $::CONFIG_SRCROOT/${name}__placed_$tag
    set out $::CONFIG_OUTROOT/${name}__placed_$tag/run0
    if {[file exists $out/result.txt]} { puts "skip: $out/result.txt"; return }
    file mkdir $out
    set part [readf $src/part.txt]
    set top [readf $src/top.txt]
    array unset ::t
    set ::cur_step read
    set t0 [clock milliseconds]
    set rc [catch {
        create_project -in_memory -part $part
        read_edif $src/netlist.edf
        link_design -top $top -part $part
        write_xdc_for $src $period $out/constraints.xdc
        read_xdc $out/constraints.xdc
        set placed 0
        set missed 0
        set fixed {}
        set pf [open $src/place.txt]
        while {[gets $pf line] >= 0} {
            lassign $line cell loc
            set c [get_cells -quiet $cell]
            if {$c eq ""} { incr missed; continue }
            if {[catch { place_cell $c $loc }]} { incr missed; continue }
            incr placed
            lappend fixed $c
        }
        close $pf
        if {[llength $fixed]} { set_property IS_LOC_FIXED 1 $fixed; set_property IS_BEL_FIXED 1 $fixed }
        step place { place_design }
        step route { route_design }
        set w [wns]
        report_timing_summary -file $out/timing.rpt
    } err]
    set kv [list rc $rc period $period part $part t_total [expr {([clock milliseconds] - $t0) / 1000.0}]]
    if {!$rc} { lappend kv wns $w placed $placed missed $missed } else { lappend kv step $::cur_step error [string map {\n " "} $err] }
    write_result $out $kv
    catch { close_project }
}

file mkdir $CONFIG_OUTROOT
foreach line [split [readf $CONFIG_JOBS] \n] {
    if {[string trim $line] eq ""} { continue }
    lassign $line name mode period runs tag
    puts "QOR_SUITE_BEGIN $name $mode $period"
    if {$mode eq "free"} {
        set p $period
        for {set i 0} {$i < $runs} {incr i} {
            set cached [file exists $CONFIG_OUTROOT/${name}__free/run$i/result.txt]
            if {!$cached && $i > 0 && [clock seconds] - $CONFIG_T0 > $CONFIG_BUDGET / 2} {
                set bh [open $CONFIG_OUTROOT/budget_hit.txt w]; puts $bh "$name run$i"; close $bh
                break
            }
            set r [run_free $name $p $i]
            if {[dict get $r rc] != 0 || ![dict exists $r wns] || [dict get $r wns] eq ""} { break }
            set np [expr {round(($p - [dict get $r wns]) * 100) / 100.0}]
            if {abs($np - $p) < 0.05} { break }
            set p $np
        }
    } else {
        run_placed $name $period $tag
    }
}
set fh [open $CONFIG_OUTROOT/version.txt w]
puts $fh [version]
close $fh
