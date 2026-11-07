set_property -dict {PACKAGE_PIN E3 IOSTANDARD LVCMOS33} [get_ports clk]
set_property -dict {PACKAGE_PIN A8 IOSTANDARD LVCMOS33} [get_ports sw]
set_property -dict {PACKAGE_PIN H5 IOSTANDARD LVCMOS33} [get_ports led]
create_clock -name clk -period 10.000 [get_ports clk]
