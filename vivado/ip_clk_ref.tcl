set CONFIG_REQ [lindex $argv 0]
set CONFIG_OUT [lindex $argv 1]
file mkdir $CONFIG_OUT

set fh [open $CONFIG_REQ r]
set lines [split [read $fh] "\n"]
close $fh

set cur_part ""
foreach ln $lines {
    set ln [string trim $ln]
    if {$ln eq "" || [string index $ln 0] eq "#"} { continue }
    set name [lindex $ln 0]
    set part [lindex $ln 1]
    set prim [lindex $ln 2]
    set fin  [lindex $ln 3]
    set outs [lrange $ln 4 end]
    set res $CONFIG_OUT/$name.txt
    if {[file exists $res]} { puts "skip $name"; continue }
    if {$part ne $cur_part} {
        catch {close_project}
        create_project -force -part $part ipref_$name $CONFIG_OUT/proj_$name
        set cur_part $part
    }
    set rc [catch {
        create_ip -name clk_wiz -vendor xilinx.com -library ip -module_name $name
        set ip [get_ips $name]
        set cfg [list CONFIG.PRIMITIVE $prim CONFIG.PRIM_IN_FREQ $fin CONFIG.NUM_OUT_CLKS [llength $outs] \
                      CONFIG.USE_LOCKED true CONFIG.USE_RESET true]
        set i 1
        foreach o $outs {
            lappend cfg CONFIG.CLKOUT${i}_USED true CONFIG.CLKOUT${i}_REQUESTED_OUT_FREQ [lindex $o 0] \
                        CONFIG.CLKOUT${i}_REQUESTED_PHASE [lindex $o 1] CONFIG.CLKOUT${i}_REQUESTED_DUTY_CYCLE [lindex $o 2]
            incr i
        }
        set_property -dict $cfg $ip
        generate_target {instantiation_template synthesis} $ip
        set f [open $res w]
        puts $f "part $part"
        foreach p [lsort [list_property $ip CONFIG.*]] {
            if {[regexp {^CONFIG\.(MMCM_|PLL_|CLKOUT[1-7]_|CLKIN1_|PRIMITIVE|PRIM_IN_FREQ|NUM_OUT_CLKS|JITTER|CLKFB)} $p]} {
                puts $f "$p [get_property $p $ip]"
            }
        }
        close $f
        set v [glob -nocomplain [file dirname [get_files -of_objects $ip *.xci]]/${name}_clk_wiz.v]
        if {$v ne ""} { file copy -force $v $CONFIG_OUT/${name}_clk_wiz.v }
    } err]
    if {$rc} {
        set f [open $res w]
        puts $f "part $part"
        puts $f "ERROR [string map {"\n" " "} $err]"
        close $f
    }
}
catch {close_project}
puts "CLKREF_DONE"
