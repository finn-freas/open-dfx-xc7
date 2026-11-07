set CONFIG_PART    xc7a35tcsg324-1
set CONFIG_OUTROOT [lindex $argv 0]
set CONFIG_SITES   [lrange $argv 1 end]

proc jstr {s} { return "\"$s\"" }

file mkdir $CONFIG_OUTROOT
link_design -part $CONFIG_PART
foreach sname $CONFIG_SITES {
    set site [get_sites $sname]
    set stype [get_property SITE_TYPE $site]
    set fh [open $CONFIG_OUTROOT/site_type_$stype.json w]
    puts $fh "\{\n  [jstr $stype]: \{\n    \"bels\": \{"
    set bels [get_bels -include_routing_bels -of $site]
    set first 1
    foreach b $bels {
        set bn [lindex [split $b /] end]
        set cls [expr {[get_property CLASS $b] eq "routing_bel" ? "RBEL" : "BEL"}]
        set bt [get_property TYPE $b]
        if {!$first} { puts $fh "," }
        set first 0
        puts -nonewline $fh "      [jstr $bn]: \{\"type\": [jstr ${stype}_$bt], \"class\": [jstr $cls], \"pins\": \{"
        set pf 1
        foreach p [get_bel_pins -of $b] {
            set pn [lindex [split $p /] end]
            set w [get_site_wires -quiet -of $p]
            set wn [lindex [split $w /] end]
            set dir [get_property DIRECTION $p]
            if {!$pf} { puts -nonewline $fh ", " }
            set pf 0
            puts -nonewline $fh "[jstr $pn]: \{\"dir\": [jstr $dir], \"wire\": [jstr $wn]\}"
        }
        puts -nonewline $fh "\}\}"
    }
    puts $fh "\n    \},\n    \"pips\": \["
    set first 1
    foreach sp [get_site_pips -quiet -of $site] {
        set n [lindex [split $sp /] end]
        if {![regexp {^([^:]+):([^-]+)->(.+)$} $n -> bel from to]} { continue }
        if {!$first} { puts $fh "," }
        set first 0
        puts -nonewline $fh "      \{\"bel\": [jstr $bel], \"from_pin\": [jstr $from], \"to_pin\": [jstr $to]\}"
    }
    puts $fh "\n    \],\n    \"pins\": \{"
    set first 1
    foreach p [get_site_pins -of $site] {
        set pn [lindex [split $p /] end]
        set w [get_site_wires -quiet -of $p]
        set wn [lindex [split $w /] end]
        set dir [get_property DIRECTION $p]
        if {!$first} { puts $fh "," }
        set first 0
        puts -nonewline $fh "      [jstr $pn]: \{\"primary\": [jstr $pn], \"wire\": [jstr $wn], \"dir\": [jstr $dir]\}"
    }
    puts $fh "\n    \}\n  \}\n\}"
    close $fh
}
