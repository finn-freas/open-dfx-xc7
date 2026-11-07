set_property LOC R4 [get_ports {clk100}]
set_property IOSTANDARD LVCMOS33 [get_ports {clk100}]

set_property LOC G4 [get_ports {cpu_reset_n}]
set_property IOSTANDARD LVCMOS15 [get_ports {cpu_reset_n}]

set_property LOC AA19 [get_ports {serial_tx}]
set_property IOSTANDARD LVCMOS33 [get_ports {serial_tx}]

set_property LOC V18 [get_ports {serial_rx}]
set_property IOSTANDARD LVCMOS33 [get_ports {serial_rx}]

set_property LOC AA14 [get_ports {eth_clocks_tx}]
set_property IOSTANDARD LVCMOS25 [get_ports {eth_clocks_tx}]

set_property LOC V13 [get_ports {eth_clocks_rx}]
set_property IOSTANDARD LVCMOS25 [get_ports {eth_clocks_rx}]

set_property LOC U7 [get_ports {eth_rst_n}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_rst_n}]

set_property LOC Y14 [get_ports {eth_int_n}]
set_property IOSTANDARD LVCMOS25 [get_ports {eth_int_n}]

set_property LOC W14 [get_ports {eth_pme_n}]
set_property IOSTANDARD LVCMOS25 [get_ports {eth_pme_n}]

set_property LOC Y16 [get_ports {eth_mdio}]
set_property IOSTANDARD LVCMOS25 [get_ports {eth_mdio}]

set_property LOC AA16 [get_ports {eth_mdc}]
set_property IOSTANDARD LVCMOS25 [get_ports {eth_mdc}]

set_property LOC W10 [get_ports {eth_rx_ctl}]
set_property IOSTANDARD LVCMOS25 [get_ports {eth_rx_ctl}]

set_property LOC AB16 [get_ports {eth_rx_data[0]}]
set_property IOSTANDARD LVCMOS25 [get_ports {eth_rx_data[0]}]

set_property LOC AA15 [get_ports {eth_rx_data[1]}]
set_property IOSTANDARD LVCMOS25 [get_ports {eth_rx_data[1]}]

set_property LOC AB15 [get_ports {eth_rx_data[2]}]
set_property IOSTANDARD LVCMOS25 [get_ports {eth_rx_data[2]}]

set_property LOC AB11 [get_ports {eth_rx_data[3]}]
set_property IOSTANDARD LVCMOS25 [get_ports {eth_rx_data[3]}]

set_property LOC V10 [get_ports {eth_tx_ctl}]
set_property IOSTANDARD LVCMOS25 [get_ports {eth_tx_ctl}]

set_property LOC Y12 [get_ports {eth_tx_data[0]}]
set_property IOSTANDARD LVCMOS25 [get_ports {eth_tx_data[0]}]

set_property LOC W12 [get_ports {eth_tx_data[1]}]
set_property IOSTANDARD LVCMOS25 [get_ports {eth_tx_data[1]}]

set_property LOC W11 [get_ports {eth_tx_data[2]}]
set_property IOSTANDARD LVCMOS25 [get_ports {eth_tx_data[2]}]

set_property LOC Y11 [get_ports {eth_tx_data[3]}]
set_property IOSTANDARD LVCMOS25 [get_ports {eth_tx_data[3]}]

set_property LOC T14 [get_ports {user_led0}]
set_property IOSTANDARD LVCMOS25 [get_ports {user_led0}]

set_property LOC T15 [get_ports {user_led1}]
set_property IOSTANDARD LVCMOS25 [get_ports {user_led1}]

set_property LOC T16 [get_ports {user_led2}]
set_property IOSTANDARD LVCMOS25 [get_ports {user_led2}]

set_property LOC U16 [get_ports {user_led3}]
set_property IOSTANDARD LVCMOS25 [get_ports {user_led3}]

set_property LOC V15 [get_ports {user_led4}]
set_property IOSTANDARD LVCMOS25 [get_ports {user_led4}]

set_property LOC W16 [get_ports {user_led5}]
set_property IOSTANDARD LVCMOS25 [get_ports {user_led5}]

set_property LOC W15 [get_ports {user_led6}]
set_property IOSTANDARD LVCMOS25 [get_ports {user_led6}]

set_property LOC Y13 [get_ports {user_led7}]
set_property IOSTANDARD LVCMOS25 [get_ports {user_led7}]

set_property LOC AA13 [get_ports {vadj0[0]}]
set_property IOSTANDARD LVCMOS25 [get_ports {vadj0[0]}]

set_property LOC AB17 [get_ports {vadj0[1]}]
set_property IOSTANDARD LVCMOS25 [get_ports {vadj0[1]}]





create_clock -name clk100 -period 10.0 [get_ports clk100]

create_clock -name eth_clocks_rx -period 8.0 [get_ports eth_clocks_rx]

create_clock -name eth_rx_clk -period 8.0 [get_nets eth_rx_clk]

create_clock -name eth_tx_clk -period 8.0 [get_nets eth_tx_clk]









