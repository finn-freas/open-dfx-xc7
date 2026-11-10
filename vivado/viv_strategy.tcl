set CONFIG_SRCROOT [lindex $argv 0]
set CONFIG_OUTROOT [lindex $argv 1]
set CONFIG_NAMES   [lrange $argv 2 end]
set CONFIG_NPATHS  1000

proc readf {f} { set h [open $f]; set s [string trim [read $h]]; close $h; return $s }

proc job {src} {
    array set j {mode rtl top top part xc7a35tcsg324-1 period 5 directives Default route 1}
    foreach line [split [readf $src/job.txt] \n] {
        set line [string trim $line]
        if {$line eq "" || [string index $line 0] eq "#"} { continue }
        set j([lindex $line 0]) [lrange $line 1 end]
    }
    return [array get j]
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
        set cells {}
        foreach c [get_cells -of_objects $p] { lappend cells [get_property NAME $c] }
        set pins {}
        foreach q [get_pins -of_objects $p] {
            set bp ""
            catch { set bp [lindex [get_bel_pins -quiet -of_objects $q] 0] }
            lappend pins "[get_property NAME $q]=$bp"
        }
        puts $f [join [list [get_property SLACK $p] [get_property DATAPATH_DELAY $p] [get_property DATAPATH_LOGIC_DELAY $p] \
                           [get_property DATAPATH_NET_DELAY $p] [get_property STARTPOINT_PIN $p] [get_property ENDPOINT_PIN $p] \
                           [join $cells " "] [get_property LOGIC_LEVELS $p] [join $pins " "]] "\t"]
    }
    close $f
}

proc slack_of {paths} {
    if {[llength $paths] == 0} { return "none" }
    return [get_property SLACK [lindex $paths 0]]
}

proc write_slack {fn} {
    set f [open $fn w]
    set seq [get_cells -hierarchical -filter {IS_SEQUENTIAL && REF_NAME != ICAPE2}]
    puts $f "wns [slack_of [get_timing_paths -setup -max_paths 1]]"
    puts $f "wns_noicap [slack_of [get_timing_paths -setup -max_paths 1 -from $seq -to $seq]]"
    puts $f "whs [slack_of [get_timing_paths -hold -max_paths 1]]"
    set tns 0.0
    set nfail 0
    foreach q [get_timing_paths -setup -max_paths 100000 -nworst 1 -unique_pins -slack_lesser_than 0 -from $seq -to $seq] {
        set tns [expr {$tns + [get_property SLACK $q]}]
        incr nfail
    }
    puts $f "tns_noicap $tns"
    puts $f "failing_endpoints_noicap $nfail"
    close $f
}

proc step {fh name script} {
    set t0 [clock milliseconds]
    uplevel 1 $script
    puts $fh [format "%s %.2f" $name [expr {([clock milliseconds] - $t0) / 1000.0}]]
    flush $fh
}

foreach name $CONFIG_NAMES {
    set src $CONFIG_SRCROOT/$name
    set out $CONFIG_OUTROOT/$name
    if {[file exists $out/status.txt]} { puts "skip $name"; continue }
    file mkdir $out
    array unset J
    array set J [job $src]
    set rc [catch {
        set tf [open $out/times.txt w]
        set xdc $out/constraints.xdc
        if {[file exists $src/constraints.xdc.tpl]} {
            set h [open $xdc w]
            puts $h [string map [list @PERIOD@ [format %.3f $J(period)]] [readf $src/constraints.xdc.tpl]]
            close $h
        } else {
            file copy -force $src/constraints.xdc $xdc
        }
        if {$J(mode) eq "edif"} {
            file copy -force $src/netlist.edf $out/$J(top).edf
            read_edif $out/$J(top).edf
            step $tf link { link_design -top $J(top) -part $J(part) }
            read_xdc $xdc
        } else {
            if {[file exists $src/files.txt]} {
                foreach f [split [readf $src/files.txt] \n] { if {$f ne ""} { read_verilog -sv $src/$f } }
            } else {
                foreach f [concat [glob -nocomplain $src/*.v] [glob -nocomplain $src/*.sv]] { read_verilog -sv $f }
            }
            if {[file exists $src/main.hex]} { file copy -force $src/main.hex [pwd]/main.hex }
            read_xdc $xdc
            step $tf synth { synth_design -top $J(top) -part $J(part) }
            report_utilization -hierarchical -hierarchical_depth 4 -file $out/hier_util_synth.rpt
            step $tf opt { opt_design }
        }
        report_utilization -hierarchical -hierarchical_depth 4 -file $out/hier_util.rpt
        report_control_sets -verbose -file $out/control_sets.rpt
        write_checkpoint -force $out/pre_place.dcp
        set first 1
        foreach d $J(directives) {
            if {!$first} { open_checkpoint $out/pre_place.dcp }
            set first 0
            puts "VS_BEGIN $name $d"
            if {$d eq "Default_nopsip"} {
                step $tf place_$d { place_design -no_psip }
            } else {
                step $tf place_$d { place_design -directive $d }
            }
            puts "VS_END_PLACE $name $d"
            dump_cells $out/cells_$d.txt
            dump_paths $out/paths_place_$d.txt $CONFIG_NPATHS
            write_slack $out/place_est_$d.txt
            report_utilization -file $out/util_$d.rpt
            report_design_analysis -timing -logic_level_distribution -max_paths 200 -file $out/rda_timing_$d.rpt
            report_design_analysis -complexity -congestion -file $out/rda_cong_$d.rpt
            if {$J(route) eq "1"} {
                step $tf route_$d { route_design }
                write_slack $out/slack_$d.txt
                dump_paths $out/paths_route_$d.txt $CONFIG_NPATHS
                report_design_analysis -timing -max_paths 200 -file $out/rda_route_$d.rpt
            }
            puts "VS_END $name $d"
            close_design
        }
        close $tf
    } err]
    set f [open $out/status.txt w]
    puts $f "rc $rc"
    if {$rc} { puts $f $err; puts $::errorInfo }
    close $f
    catch { close_design }
}
