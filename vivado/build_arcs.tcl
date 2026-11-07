set CONFIG_PART    xc7a35tcsg324-1
set CONFIG_SRCROOT [lindex $argv 0]
set CONFIG_OUTROOT [lindex $argv 1]
set CONFIG_NAMES   [lrange $argv 2 end]
set CONFIG_MAX_PER_TYPE 400
set CONFIG_ARC_PROPS {DELAY_SLOW_MAX_RISE DELAY_SLOW_MAX_FALL DELAY_FAST_MIN_RISE DELAY_FAST_MIN_FALL}

proc arc_line {kind cell from to arc} {
    set bel [get_bels -quiet -of_objects $cell]
    set fbp [get_bel_pins -quiet -of_objects $from]
    set vals {}
    foreach p $::CONFIG_ARC_PROPS {
        set v [get_property -quiet $p $arc]
        if {$v eq ""} { set v - }
        lappend vals $v
    }
    set bp [lindex [split $fbp /] end]
    if {$bp eq ""} { set bp - }
    set bn [lindex [split $bel /] end]
    if {$bn eq ""} { set bn - }
    set ty [string map {" " _} [get_property TYPE $arc]]
    if {$ty eq ""} { set ty - }
    set site [get_sites -quiet -of_objects $cell]
    set ext 0
    if {$ty eq "combinational"} {
        set net [get_nets -quiet -of_objects $to]
        foreach l [get_pins -quiet -leaf -of_objects $net -filter {DIRECTION == IN}] {
            if {[get_sites -quiet -of_objects [get_cells -of_objects $l]] ne $site} { incr ext }
        }
    } else {
        set net [get_nets -quiet -of_objects $to]
        set drv [get_pins -quiet -leaf -of_objects $net -filter {DIRECTION == OUT}]
        if {$drv ne "" && [get_sites -quiet -of_objects [get_cells -of_objects $drv]] ne $site} { set ext 1 }
    }
    set sense [string map {" " _} [get_property -quiet SENSE $arc]]
    if {$sense eq ""} { set sense - }
    set stype [get_property -quiet SITE_TYPE $site]
    if {$stype eq ""} { set stype - }
    set spins {}
    if {$ty eq "combinational"} {
        foreach sp [get_site_pins -quiet -of_objects [get_nets -quiet -of_objects $to]] {
            if {[string first $site/ $sp] == 0} { lappend spins [lindex [split $sp /] end] }
        }
    }
    if {![llength $spins]} { set spins - }
    set other -
    if {[string match {[A-D][56]LUT} $bn]} {
        set peer [string map {6LUT 5LUT 5LUT 6LUT} $bn]
        set other [expr {[llength [get_cells -quiet -of_objects [get_bels -quiet $site/$peer]]] ? "pair" : "single"}]
    }
    return [format "%s %s %s %s %s %s %s %s %s %s %s %s %s" $kind [get_property REF_NAME $cell] [get_property REF_PIN_NAME $from] \
        [get_property REF_PIN_NAME $to] $bp $ty $bn $vals $ext $sense $stype [join $spins ,] $other]
}

file mkdir $CONFIG_OUTROOT
foreach name $CONFIG_NAMES {
    set src $CONFIG_SRCROOT/$name
    set out $CONFIG_OUTROOT/$name
    file mkdir $out
    if {[file exists $out/status.txt]} { puts "skip: $out/status.txt exists"; continue }
    set top [string trim [read [open $src/top.txt]]]
    set rc [catch {
        create_project -in_memory -part $CONFIG_PART
        file copy -force $src/netlist.edf $out/$top.edf
        read_edif $out/$top.edf
        link_design -top $top -part $CONFIG_PART
        read_xdc $src/constraints.xdc
        if {[file exists $src/place.txt]} {
            set pf [open $src/place.txt]
            set fixed {}
            while {[gets $pf line] >= 0} {
                lassign $line cell loc
                set c [get_cells -quiet $cell]
                if {$c eq ""} { continue }
                if {[catch { place_cell $c $loc }]} { continue }
                lappend fixed $c
            }
            close $pf
            if {[llength $fixed]} { set_property IS_LOC_FIXED 1 $fixed; set_property IS_BEL_FIXED 1 $fixed }
        }
        place_design
        route_design
        set af [open $out/arcs.txt w]
        foreach pat {LUT1 LUT2 LUT3 LUT4 LUT5 LUT6 FDRE FDSE FDCE FDPE CARRY4 MUXF7 MUXF8} {
            set cells [lrange [get_cells -hier -quiet -filter "REF_NAME == $pat"] 0 [expr {$::CONFIG_MAX_PER_TYPE - 1}]]
            foreach c $cells {
                foreach a [get_timing_arcs -quiet -of_objects $c] {
                    set f [get_property FROM_PIN $a]
                    set t [get_property TO_PIN $a]
                    if {$f eq "" || $t eq ""} { continue }
                    puts $af [arc_line ARC $c $f $t $a]
                }
            }
        }
        close $af
        report_timing -max_paths 200 -nworst 1 -input_pins -file $out/paths.rpt
    } err]
    set sf [open $out/status.txt w]
    puts $sf "rc $rc"
    if {$rc} { puts $sf "error $err" }
    close $sf
    catch { close_project }
}
