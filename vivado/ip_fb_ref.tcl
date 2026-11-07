set CONFIG_PART xc7a35tcsg324-1
set CONFIG_FIFO [lindex $argv 0]
set CONFIG_BRAM [lindex $argv 1]
set CONFIG_BSRC [lindex $argv 2]
set CONFIG_OUT  [lindex $argv 3]
set CONFIG_JOBS 4
file mkdir $CONFIG_OUT

proc read_cfg {f} {
    set out {}
    if {$f eq "-"} { return $out }
    set fh [open $f r]
    foreach ln [split [read $fh] "\n"] {
        set ln [string trim $ln]
        if {$ln eq "" || [string index $ln 0] eq "#"} { continue }
        set props {}
        foreach kv [lrange $ln 1 end] {
            set i [string first = $kv]
            lappend props CONFIG.[string range $kv 0 [expr {$i - 1}]] [string range $kv [expr {$i + 1}] end]
        }
        lappend out [list [lindex $ln 0] $props]
    }
    close $fh
    return $out
}

proc dump_cells {fname pat} {
    set f [open $fname w]
    foreach c [lsort [get_cells -hier -filter "REF_NAME =~ $pat"]] {
        puts $f "CELL $c [get_property REF_NAME $c] LOC=[get_property LOC $c]"
        foreach p [list_property $c] {
            if {[regexp {^(INIT|INITP|SRVAL|EN_|DATA_WIDTH|DO_REG|FIRST_WORD|ALMOST_|FIFO_MODE|READ_WIDTH|WRITE_WIDTH|RAM_MODE|DOA_REG|DOB_REG|WRITE_MODE|RSTREG|RAM_EXTENSION|RDADDR|SIM_|IS_)} $p]} {
                puts $f "  $p=[get_property $p $c]"
            }
        }
    }
    close $f
}

set fifos [read_cfg $CONFIG_FIFO]
if {[llength $fifos]} {
    set pd $CONFIG_OUT/fifo_proj
    create_project -force -part $CONFIG_PART fifo_ref $pd
    set todo {}
    foreach e $fifos {
        lassign $e name props
        if {[file exists $CONFIG_OUT/fifo/$name.cells]} { continue }
        create_ip -name fifo_generator -vendor xilinx.com -library ip -module_name $name
        set_property -dict $props [get_ips $name]
        generate_target {instantiation_template simulation synthesis} [get_ips $name]
        lappend todo $name
    }
    file mkdir $CONFIG_OUT/fifo
    foreach name $todo {
        set ip [get_ips $name]
        set f [open $CONFIG_OUT/fifo/$name.props w]
        foreach p [lsort [list_property $ip CONFIG.*]] { puts $f "$p [get_property $p $ip]" }
        close $f
        set d [file dirname [get_files -of_objects $ip *.xci]]
        foreach v [glob -nocomplain $d/sim/*.v] { file copy -force $v $CONFIG_OUT/fifo/ }
        create_ip_run $ip
    }
    if {[llength $todo]} {
        set runs {}
        foreach name $todo { lappend runs ${name}_synth_1 }
        launch_runs $runs -jobs $CONFIG_JOBS
        foreach r $runs { wait_on_run $r }
        foreach name $todo {
            set rc [catch {
                open_run ${name}_synth_1 -name n_$name
                report_utilization -file $CONFIG_OUT/fifo/$name.util
                dump_cells $CONFIG_OUT/fifo/$name.cells "FIFO*"
                set f [open $CONFIG_OUT/fifo/$name.refs w]
                foreach c [get_cells -hier -filter {IS_PRIMITIVE}] { puts $f [get_property REF_NAME $c] }
                close $f
                close_design
            } err]
            if {$rc} { set f [open $CONFIG_OUT/fifo/$name.cells w]; puts $f "ERROR $err"; close $f }
        }
    }
    close_project
}

foreach e [read_cfg $CONFIG_BRAM] {
    lassign $e name props
    set od $CONFIG_OUT/bram/$name
    if {[file exists $od/$name.bit]} { continue }
    file mkdir $od
    set rc [catch {
        create_project -force -part $CONFIG_PART bram_$name $od/proj
        create_ip -name blk_mem_gen -vendor xilinx.com -library ip -module_name ${name}_mem
        lappend props CONFIG.Load_Init_File true CONFIG.Coe_File [file normalize $CONFIG_BSRC/$name.coe]
        set_property -dict $props [get_ips ${name}_mem]
        generate_target all [get_ips ${name}_mem]
        set ip [get_ips ${name}_mem]
        set f [open $od/$name.props w]
        foreach p [lsort [list_property $ip CONFIG.*]] { puts $f "$p [get_property $p $ip]" }
        close $f
        add_files $CONFIG_BSRC/${name}_top.v
        add_files -fileset constrs_1 $CONFIG_BSRC/top.xdc
        set_property top ${name}_top [current_fileset]
        launch_runs impl_1 -to_step write_bitstream -jobs $CONFIG_JOBS
        wait_on_run impl_1
        open_run impl_1
        dump_cells $od/$name.cells "RAMB*"
        report_utilization -file $od/$name.util
        file copy -force [glob $od/proj/bram_$name.runs/impl_1/*.bit] $od/$name.bit
        close_project
    } err]
    if {$rc} { set f [open $od/ERROR.txt w]; puts $f $err; close $f; catch {close_project} }
}
puts "FBREF_DONE"
