set CONFIG_PART [lindex $argv 0]
set CONFIG_OUT  [lindex $argv 1]

file mkdir [file dirname $CONFIG_OUT]
if {[file exists $CONFIG_OUT]} { puts "skip: $CONFIG_OUT exists"; exit 0 }

link_design -part $CONFIG_PART
set fh [open $CONFIG_OUT w]
foreach cr [lsort [get_clock_regions]] {
    set sl [get_sites -quiet -of_objects $cr -filter {SITE_TYPE =~ SLICE*}]
    set xs {}; set ys {}
    foreach s $sl { regexp {SLICE_X(\d+)Y(\d+)} $s -> x y; lappend xs $x; lappend ys $y }
    set ml [llength [get_sites -quiet -of_objects $cr -filter {SITE_TYPE == SLICEM}]]
    set br [llength [get_sites -quiet -of_objects $cr -filter {SITE_TYPE =~ RAMB36*}]]
    set dsp [llength [get_sites -quiet -of_objects $cr -filter {SITE_TYPE =~ DSP48*}]]
    set banks [lsort -unique [get_property -quiet IOBANK [get_sites -quiet -of_objects $cr -filter {IS_PAD}]]]
    if {[llength $xs]} {
        puts $fh [format "%s SLICE_X%d:%d Y%d:%d slices=%d slicem=%d ramb36=%d dsp=%d banks={%s}" $cr \
            [tcl::mathfunc::min {*}$xs] [tcl::mathfunc::max {*}$xs] [tcl::mathfunc::min {*}$ys] [tcl::mathfunc::max {*}$ys] \
            [llength $sl] $ml $br $dsp $banks]
    } else {
        puts $fh "$cr no slices"
    }
}
foreach p {E3 H5 J5 T9 T10} {
    set s [get_package_pins $p]
    puts $fh "pin $p bank [get_property BANK $s] site [get_sites -of_objects $s] cr [get_clock_regions -of_objects [get_sites -of_objects $s]]"
}
close $fh
puts "wrote $CONFIG_OUT"
