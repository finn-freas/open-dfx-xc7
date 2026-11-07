set out [lindex $argv 0]
file mkdir $out
create_project -in_memory -part xc7a35tcpg236-1
set_property target_language Verilog [current_project]
set ipdir $out/ip
file delete -force $ipdir
file mkdir $ipdir
create_ip -name pcie_7x -vendor xilinx.com -library ip -module_name pcie_ep -dir $ipdir
set ip [get_ips pcie_ep]
proc dump {ip f} {
    set fh [open $f w]
    foreach p [lsort [list_property $ip]] { puts $fh "$p=[get_property $p $ip]" }
    close $fh
}
dump $ip $out/props_default.txt
set want {
    CONFIG.Maximum_Link_Width X1
    CONFIG.Link_Speed 2.5_GT/s
    CONFIG.Device_Port_Type PCI_Express_Endpoint_device
    CONFIG.Bar0_Enabled true
    CONFIG.Bar0_Size 4
    CONFIG.Bar0_Scale Kilobytes
}
set fh [open $out/set_log.txt w]
foreach {k v} $want {
    if {[catch {set_property $k $v $ip} err]} { puts $fh "FAIL $k=$v : $err" } else { puts $fh "ok $k=$v -> [get_property $k $ip]" }
}
close $fh
dump $ip $out/props_set.txt
generate_target {instantiation_template synthesis} $ip
set fh [open $out/files.txt w]
foreach f [get_files -of_objects [get_files pcie_ep.xci]] { puts $fh $f }
close $fh
file mkdir $out/src
foreach f [get_files -of_objects [get_files pcie_ep.xci]] {
    if {[string match *.v $f] || [string match *.xdc $f]} { file copy -force $f $out/src/ }
}
puts "PCIE_IP_DONE"
