set CONFIG_PART      xc7a35tcsg324-1
set CONFIG_SRCROOT   [lindex $argv 0]
set CONFIG_OUTROOT   [lindex $argv 1]
set CONFIG_NAMES     [lrange $argv 2 end]
set CONFIG_MAX_PATHS 1000

proc step {fh name script} {
    set ::cur_step $name
    set t0 [clock milliseconds]
    uplevel 1 $script
    puts $fh [format "%s %.2f" $name [expr {([clock milliseconds] - $t0) / 1000.0}]]
    flush $fh
}

proc dump_cells {fn} {
    set f [open $fn w]
    foreach c [get_cells -hierarchical -filter {IS_PRIMITIVE}] {
        puts $f [join [list [get_property NAME $c] [get_property REF_NAME $c] [get_property LOC $c] [get_property BEL $c]] "\t"]
    }
    close $f
}

proc dump_paths {fn n} {
    set f [open $fn w]
    foreach p [get_timing_paths -setup -max_paths $n -nworst 1 -unique_pins] {
        set pins {}
        foreach q [get_pins -quiet -of_objects $p] { lappend pins [get_property NAME $q] }
        puts $f [join [list [get_property SLACK $p] [get_property DATAPATH_DELAY $p] [get_property DATAPATH_LOGIC_DELAY $p] \
                           [get_property DATAPATH_NET_DELAY $p] [get_property STARTPOINT_PIN $p] [get_property ENDPOINT_PIN $p] \
                           [get_property STARTPOINT_CLOCK $p] [join $pins " "]] "\t"]
    }
    close $f
}

proc dump_sites {fn} {
    if {[file exists $fn]} { return }
    set f [open $fn w]
    foreach s [get_sites -filter {SITE_TYPE == SLICEL || SITE_TYPE == SLICEM || SITE_TYPE == RAMB36E1 || SITE_TYPE == DSP48E1}] {
        puts $f "[get_property NAME $s]\t[get_property SITE_TYPE $s]\t[get_property CLOCK_REGION $s]"
    }
    close $f
}

file mkdir $CONFIG_OUTROOT
foreach name $CONFIG_NAMES {
    set src $CONFIG_SRCROOT/$name
    set out $CONFIG_OUTROOT/$name
    file mkdir $out
    if {[file exists $out/status.txt]} { puts "skip: $out/status.txt exists"; continue }
    puts "DPL_DUMP_BEGIN $name"
    set top [string trim [read [open $src/top.txt]]]
    set mode [string trim [read [open $src/mode.txt]]]
    set tf [open $out/times.txt w]
    set ::cur_step read
    set rc [catch {
        create_project -in_memory -part $CONFIG_PART
        file copy -force $src/netlist.edf $out/$top.edf
        read_edif $out/$top.edf
        link_design -top $top -part $CONFIG_PART
        read_xdc $src/constraints.xdc
        dump_sites $CONFIG_OUTROOT/sites.txt
        if {$mode eq "free"} {
            step $tf opt { opt_design }
        }
        if {[file exists $src/place.txt]} {
            set placed 0
            set missed {}
            set fixed {}
            set pf [open $src/place.txt]
            while {[gets $pf line] >= 0} {
                lassign $line cell loc
                set c [get_cells -quiet $cell]
                if {$c eq ""} { lappend missed $cell; continue }
                if {[catch { place_cell $c $loc } err]} { lappend missed "$cell $loc $err"; continue }
                incr placed
                lappend fixed $c
            }
            close $pf
            set mf [open $out/place_missed.txt w]
            puts $mf "placed $placed"
            foreach m $missed { puts $mf $m }
            close $mf
            if {[llength $fixed]} {
                set_property IS_LOC_FIXED 1 $fixed
                set_property IS_BEL_FIXED 1 $fixed
            }
        }
        step $tf place { place_design }
        dump_cells $out/cells_placed.txt
        step $tf route { route_design }
        report_utilization -file $out/util.rpt
        report_timing_summary -file $out/timing.rpt
        report_route_status -file $out/route_status.rpt
        catch { report_design_analysis -congestion -file $out/congestion.rpt }
        dump_cells $out/cells.txt
        dump_paths $out/paths.txt $CONFIG_MAX_PATHS
        set wf [open $out/worst_paths.txt w]
        foreach p [get_timing_paths -setup -max_paths 2000 -nworst 1 -unique_pins] {
            puts $wf [format "%s %s %s" [get_property SLACK $p] [get_property STARTPOINT_PIN $p] [get_property ENDPOINT_PIN $p]]
        }
        close $wf
        set nets [get_nets -hierarchical -filter {TYPE == SIGNAL}]
        set pf [open $out/wirelength.txt w]
        puts $pf "signal_nets [llength $nets]"
        puts $pf "signal_pips [llength [get_pips -quiet -of_objects $nets]]"
        puts $pf "signal_nodes [llength [get_nodes -quiet -of_objects $nets]]"
        close $pf
    } err]
    close $tf
    set sf [open $out/status.txt w]
    puts $sf "rc $rc"
    if {$rc} { puts $sf "step $::cur_step"; puts $sf "error $err" }
    close $sf
    catch { close_project }
}
set fh [open $CONFIG_OUTROOT/version.txt w]
puts $fh [version]
close $fh
