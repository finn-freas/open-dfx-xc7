set CONFIG_DESIGN [lindex $argv 0]
set CONFIG_TOP    [lindex $argv 1]
set CONFIG_SRC    [lindex $argv 2]
set CONFIG_XDC    [lindex $argv 3]
set CONFIG_OUT    [lindex $argv 4]
set CONFIG_RP     u_rm
set CONFIG_DIR    sitepips

cd $CONFIG_OUT
file mkdir $CONFIG_DIR
foreach d [lsort [glob cfg_*_routed.dcp]] {
    set name [string range $d 0 end-4]
    if {[file exists $CONFIG_DIR/$name.txt]} { puts "skip: $name"; continue }
    open_checkpoint $d
    set fh [open $CONFIG_DIR/$name.txt w]
    foreach c [get_cells -hierarchical -filter "REF_NAME == DSP48E1 || REF_NAME == CARRY4"] {
        set site [get_sites -of_objects $c]
        set props {}
        foreach p {AREG BREG ACASCREG BCASCREG A_INPUT B_INPUT USE_MULT MREG PREG} {
            if {[get_property REF_NAME $c] eq "DSP48E1"} { lappend props "$p=[get_property $p $c]" }
        }
        puts $fh "cell\t$c\t[get_property REF_NAME $c]\t$site\t[join $props { }]"
        foreach sp [get_site_pips -quiet -of_objects $site] {
            if {[get_property IS_USED $sp]} {
                set nets [get_nets -quiet -of_objects $sp]
                puts $fh "sitepip\t$site\t$sp\t$nets"
            }
        }
    }
    close $fh
    close_project
}
