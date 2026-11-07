set_property LOC E3 [get_ports {clk100}]
set_property IOSTANDARD LVCMOS33 [get_ports {clk100}]

set_property LOC C2 [get_ports {cpu_reset_n}]
set_property IOSTANDARD LVCMOS33 [get_ports {cpu_reset_n}]

set_property LOC G18 [get_ports {eth_ref_clk}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_ref_clk}]

set_property LOC D10 [get_ports {serial_tx}]
set_property IOSTANDARD LVCMOS33 [get_ports {serial_tx}]

set_property LOC A9 [get_ports {serial_rx}]
set_property IOSTANDARD LVCMOS33 [get_ports {serial_rx}]

set_property LOC H16 [get_ports {eth_clocks_tx}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_clocks_tx}]

set_property LOC F15 [get_ports {eth_clocks_rx}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_clocks_rx}]

set_property LOC C16 [get_ports {eth_rst_n}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_rst_n}]

set_property LOC K13 [get_ports {eth_mdio}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_mdio}]

set_property LOC F16 [get_ports {eth_mdc}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_mdc}]

set_property LOC G16 [get_ports {eth_rx_dv}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_rx_dv}]

set_property LOC C17 [get_ports {eth_rx_er}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_rx_er}]

set_property LOC D18 [get_ports {eth_rx_data[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_rx_data[0]}]

set_property LOC E17 [get_ports {eth_rx_data[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_rx_data[1]}]

set_property LOC E18 [get_ports {eth_rx_data[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_rx_data[2]}]

set_property LOC G17 [get_ports {eth_rx_data[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_rx_data[3]}]

set_property LOC H15 [get_ports {eth_tx_en}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_tx_en}]

set_property LOC H14 [get_ports {eth_tx_data[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_tx_data[0]}]

set_property LOC J14 [get_ports {eth_tx_data[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_tx_data[1]}]

set_property LOC J13 [get_ports {eth_tx_data[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_tx_data[2]}]

set_property LOC H17 [get_ports {eth_tx_data[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_tx_data[3]}]

set_property LOC D17 [get_ports {eth_col}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_col}]

set_property LOC G14 [get_ports {eth_crs}]
set_property IOSTANDARD LVCMOS33 [get_ports {eth_crs}]

set_property LOC H5 [get_ports {user_led0}]
set_property IOSTANDARD LVCMOS33 [get_ports {user_led0}]

set_property LOC J5 [get_ports {user_led1}]
set_property IOSTANDARD LVCMOS33 [get_ports {user_led1}]

set_property LOC T9 [get_ports {user_led2}]
set_property IOSTANDARD LVCMOS33 [get_ports {user_led2}]

set_property LOC T10 [get_ports {user_led3}]
set_property IOSTANDARD LVCMOS33 [get_ports {user_led3}]


set_property INTERNAL_VREF 0.675 [get_iobanks 34]



create_clock -name clk100 -period 10.0 [get_ports clk100]

create_clock -name eth_rx_clk -period 40.0 [get_nets eth_rx_clk]

create_clock -name eth_tx_clk -period 40.0 [get_nets eth_tx_clk]



set_false_path -quiet -to [get_cells -hierarchical -filter {mr_ff == TRUE}]

set_false_path -quiet -to [get_pins -filter {REF_PIN_NAME == PRE} -of_objects [get_cells -hierarchical -filter {ars_ff1 == TRUE || ars_ff2 == TRUE}]]

set_max_delay 2 -quiet -from [get_pins -filter {REF_PIN_NAME == C} -of_objects [get_cells -hierarchical -filter {ars_ff1 == TRUE}]] -to [get_pins -filter {REF_PIN_NAME == D} -of_objects [get_cells -hierarchical -filter {ars_ff2 == TRUE}]]

set_clock_groups -group [get_clocks -of [get_nets eth_rx_clk]] -group [get_clocks -of [get_nets eth_tx_clk]] -asynchronous

set_clock_groups -group [get_clocks -of [get_nets eth_rx_clk]] -group [get_clocks -of [get_nets sys_clk]] -asynchronous

set_clock_groups -group [get_clocks -of [get_nets eth_tx_clk]] -group [get_clocks -of [get_nets sys_clk]] -asynchronous

set_clock_groups -group [get_clocks -of [get_nets sys_clk]] -group [get_clocks -of [get_nets main_crg_clkin_signal]] -asynchronous