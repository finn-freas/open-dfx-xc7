set CONFIG_PART    xc7a35tcsg324-1
set CONFIG_SRCROOT [lindex $argv 0]
set CONFIG_OUTROOT [lindex $argv 1]
set CONFIG_CELLS   [lindex $argv 2]
set CONFIG_NAMES   [lrange $argv 3 end]

file mkdir $CONFIG_OUTROOT
foreach name $CONFIG_NAMES {
    set src $CONFIG_SRCROOT/$name
    set out $CONFIG_OUTROOT/$name.pinmap.txt
    if {[file exists $out]} { puts "skip: $out exists"; continue }
    set rc [catch {
        create_project -in_memory -part $CONFIG_PART
        foreach f [glob -nocomplain $src/*.v] { read_verilog -sv $f }
        read_xdc [glob $src/*.xdc]
        synth_design -top $name -part $CONFIG_PART
        opt_design
        place_design
        set fh [open $out w]
        foreach c [get_cells -quiet $CONFIG_CELLS] {
            puts $fh "cell [get_property NAME $c] [get_property REF_NAME $c] site [get_property SITE $c] bel [get_property BEL $c]"
            foreach p [lsort -dictionary [get_pins -of $c]] {
                set bp [get_bel_pins -quiet -of $p]
                set sp [get_site_pins -quiet -of $p]
                if {$sp eq ""} { catch { set sp [get_site_pins -quiet -of $bp] } }
                set nt [get_nets -quiet -of $p]
                puts $fh [format "pin %s %s bel_pin %s site_pin %s net %s" [get_property REF_PIN_NAME $p] \
                    [get_property DIRECTION $p] [lsort $bp] [lsort $sp] $nt]
            }
            foreach prop [list_property $c] {
                if {[string match "IS_*" $prop] || [string match "INIT_4*" $prop] || [string match "*OFFSET" $prop]} {
                    puts $fh "prop $prop [get_property $prop $c]"
                }
            }
        }
        close $fh
    } err]
    if {$rc} { set fh [open $out.err w]; puts $fh $err; close $fh }
    catch { close_project }
}
