set CONFIG_PART    xc7a35tcsg324-1
set CONFIG_SRCROOT [lindex $argv 0]
set CONFIG_OUTROOT [lindex $argv 1]
set CONFIG_NAMES   [lrange $argv 2 end]
set CONFIG_SITES   {GTPE2_CHANNEL GTPE2_COMMON IBUFDS_GTE2 ODELAYE2 IDELAYE2 IDELAYCTRL ISERDESE2 OSERDESE2 XADC \
                    BUFGCTRL BUFHCE BUFR BUFIO MMCME2_ADV PLLE2_ADV RAMB36E1 RAMB18E1 FIFO18E1 DSP48E1 PCIE_2_1 \
                    ICAP BSCAN STARTUP FRAME_ECC DNA_PORT USR_ACCESS EFUSE_USR CAPTURE}

file mkdir $CONFIG_OUTROOT
set qf $CONFIG_OUTROOT/device_sites.txt
if {![file exists $qf]} {
    link_design -part $CONFIG_PART
    set fh [open $qf w]
    puts $fh "part $CONFIG_PART"
    foreach t $CONFIG_SITES {
        puts $fh [format "%-14s %d" $t [llength [get_sites -quiet -filter "SITE_TYPE == $t"]]]
    }
    puts $fh "site_types [lsort -unique [get_property SITE_TYPE [get_sites]]]"
    close $fh
    close_design
}

proc step {fh name script} {
    set ::cur_step $name
    set t0 [clock milliseconds]
    uplevel 1 $script
    puts $fh [format "%s %.2f" $name [expr {([clock milliseconds] - $t0) / 1000.0}]]
    flush $fh
}

foreach name $CONFIG_NAMES {
    set src $CONFIG_SRCROOT/$name
    set out $CONFIG_OUTROOT/$name
    file mkdir $out
    if {[file exists $out/$name.bit]} { puts "skip: $out/$name.bit exists"; continue }
    puts "GAP_BEGIN $name"
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
        report_utilization -file $out/synth_util.rpt
        step $tf opt { opt_design }
        step $tf place { place_design }
        step $tf route { route_design }
        report_utilization -file $out/util.rpt
        report_timing_summary -file $out/timing.rpt
        report_drc -file $out/drc.rpt
        set paths [get_timing_paths -setup -max_paths 2000 -nworst 1 -unique_pins]
        set wf [open $out/worst_paths.txt w]
        foreach p $paths {
            puts $wf [format "%s %s %s" [get_property SLACK $p] [get_property STARTPOINT_PIN $p] [get_property ENDPOINT_PIN $p]]
        }
        close $wf
        step $tf bitstream { write_bitstream -force -logic_location_file $out/$name.bit }
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
