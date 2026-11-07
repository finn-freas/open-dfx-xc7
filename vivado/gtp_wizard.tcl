set out [lindex $argv 0]
file mkdir $out
create_project -in_memory -part xc7a35tcpg236-1
set_property target_language Verilog [current_project]
set ipdir $out/ip
file delete -force $ipdir
file mkdir $ipdir
create_ip -name gtwizard -vendor xilinx.com -library ip -module_name gtp_w -dir $ipdir
set ip [get_ips gtp_w]

proc dump {ip f} {
    set fh [open $f w]
    foreach p [lsort [list_property $ip]] { puts $fh "$p=[get_property $p $ip]" }
    close $fh
}
dump $ip $out/props_default.txt

set want {
    CONFIG.identical_val_tx_line_rate 2.5
    CONFIG.identical_val_rx_line_rate 2.5
    CONFIG.identical_val_tx_reference_clock 125.000
    CONFIG.identical_val_rx_reference_clock 125.000
    CONFIG.gt0_val_tx_line_rate 2.5
    CONFIG.gt0_val_rx_line_rate 2.5
    CONFIG.gt0_val_tx_reference_clock 125.000
    CONFIG.gt0_val_rx_reference_clock 125.000
    CONFIG.gt0_val_encoding 8B/10B
    CONFIG.gt0_val_decoding 8B/10B
    CONFIG.gt0_val_tx_data_width 16
    CONFIG.gt0_val_rx_data_width 16
    CONFIG.gt0_val_tx_int_datawidth 20
    CONFIG.gt0_val_rx_int_datawidth 20
    CONFIG.gt0_val_tx_refclk REFCLK0_Q0
    CONFIG.gt0_val_rx_refclk REFCLK0_Q0
    CONFIG.gt0_val_port_rxcommadet true
    CONFIG.gt0_val_port_rxpcommaalignen true
    CONFIG.gt0_val_port_rxmcommaalignen true
    CONFIG.gt0_val_comma_preset K28.5
    CONFIG.gt0_val_port_loopback true
    CONFIG.gt0_val_port_rxbyteisaligned true
}
set fh [open $out/set_log.txt w]
foreach {k v} $want {
    if {[catch {set_property $k $v $ip} err]} { puts $fh "FAIL $k=$v : $err" } else { puts $fh "ok $k=$v -> [get_property $k $ip]" }
}
close $fh
dump $ip $out/props_set.txt
generate_target {instantiation_template synthesis} $ip
set fh [open $out/files.txt w]
foreach f [get_files -of_objects [get_files gtp_w.xci]] { puts $fh $f }
close $fh
foreach f [glob -nocomplain -directory $ipdir/gtp_w *.v] { file copy -force $f $out/ }
puts "GTP_WIZARD_DONE"
