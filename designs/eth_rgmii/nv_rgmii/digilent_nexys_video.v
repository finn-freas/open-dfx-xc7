
`timescale 1ns / 1ps


module digilent_nexys_video (
    (* dont_touch = "true" *)
    input  wire          clk100,
    input  wire          cpu_reset_n,
    (* dont_touch = "true" *)
    input  wire          eth_clocks_rx,
    output wire          eth_clocks_tx,
    input  wire          eth_int_n,
    output wire          eth_mdc,
    inout  wire          eth_mdio,
    input  wire          eth_pme_n,
    output wire          eth_rst_n,
    input  wire          eth_rx_ctl,
    input  wire    [3:0] eth_rx_data,
    output wire          eth_tx_ctl,
    output wire    [3:0] eth_tx_data,
    input  wire          serial_rx,
    output reg           serial_tx,
    output wire          user_led0,
    output wire          user_led1,
    output wire          user_led2,
    output wire          user_led3,
    output wire          user_led4,
    output wire          user_led5,
    output wire          user_led6,
    output wire          user_led7,
    input  wire    [1:0] vadj0
);





reg    [31:0] builder_basiclowerer_self = 32'd0;
reg     [1:0] builder_clockdomainsrenamer_fsm_next_state = 2'd0;
reg     [1:0] builder_clockdomainsrenamer_fsm_state = 2'd0;
reg     [1:0] builder_clockdomainsrenamer_liteethmacpacketreader_next_state = 2'd0;
reg     [1:0] builder_clockdomainsrenamer_liteethmacpacketreader_state = 2'd0;
reg     [2:0] builder_clockdomainsrenamer_next_state = 3'd0;
reg     [1:0] builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_next_state = 2'd0;
reg     [1:0] builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state = 2'd0;
reg           builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_next_state = 1'd0;
reg           builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_state = 1'd0;
reg     [2:0] builder_clockdomainsrenamer_state = 3'd0;
reg     [1:0] builder_clockdomainsrenamer_txdatapath_bufferizeendpoints_next_state = 2'd0;
reg     [1:0] builder_clockdomainsrenamer_txdatapath_bufferizeendpoints_state = 2'd0;
reg           builder_clockdomainsrenamer_txdatapath_liteethmacgap_next_state = 1'd0;
reg           builder_clockdomainsrenamer_txdatapath_liteethmacgap_state = 1'd0;
reg           builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_next_state = 1'd0;
reg           builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_state = 1'd0;
reg     [1:0] builder_clockdomainsrenamer_txdatapath_liteethmacpreambleinserter_next_state = 2'd0;
reg     [1:0] builder_clockdomainsrenamer_txdatapath_liteethmacpreambleinserter_state = 2'd0;
reg    [19:0] builder_count = 20'd1000000;
wire          builder_crg_mmcm_fb;
wire          builder_crg_reset0;
wire          builder_crg_reset1;
wire          builder_crg_reset2;
wire          builder_crg_reset3;
wire          builder_crg_reset4;
wire          builder_crg_reset5;
wire          builder_crg_reset6;
wire          builder_crg_reset7;
wire    [5:0] builder_csr_bankarray_adr;
wire   [31:0] builder_csr_bankarray_csrbank0_bus_errors_r;
reg           builder_csr_bankarray_csrbank0_bus_errors_re = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank0_bus_errors_w;
reg           builder_csr_bankarray_csrbank0_bus_errors_we = 1'd0;
wire    [1:0] builder_csr_bankarray_csrbank0_reset_r;
reg           builder_csr_bankarray_csrbank0_reset_re = 1'd0;
wire    [1:0] builder_csr_bankarray_csrbank0_reset_w;
reg           builder_csr_bankarray_csrbank0_reset_we = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank0_scratch_r;
reg           builder_csr_bankarray_csrbank0_scratch_re = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank0_scratch_w;
reg           builder_csr_bankarray_csrbank0_scratch_we = 1'd0;
wire          builder_csr_bankarray_csrbank0_sel;
wire          builder_csr_bankarray_csrbank1_preamble_crc_r;
reg           builder_csr_bankarray_csrbank1_preamble_crc_re = 1'd0;
wire          builder_csr_bankarray_csrbank1_preamble_crc_w;
reg           builder_csr_bankarray_csrbank1_preamble_crc_we = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank1_rx_datapath_crc_errors_r;
reg           builder_csr_bankarray_csrbank1_rx_datapath_crc_errors_re = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank1_rx_datapath_crc_errors_w;
reg           builder_csr_bankarray_csrbank1_rx_datapath_crc_errors_we = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank1_rx_datapath_preamble_errors_r;
reg           builder_csr_bankarray_csrbank1_rx_datapath_preamble_errors_re = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank1_rx_datapath_preamble_errors_w;
reg           builder_csr_bankarray_csrbank1_rx_datapath_preamble_errors_we = 1'd0;
wire          builder_csr_bankarray_csrbank1_sel;
wire          builder_csr_bankarray_csrbank1_sram_reader_ev_enable_r;
reg           builder_csr_bankarray_csrbank1_sram_reader_ev_enable_re = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_reader_ev_enable_w;
reg           builder_csr_bankarray_csrbank1_sram_reader_ev_enable_we = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_reader_ev_pending_r;
reg           builder_csr_bankarray_csrbank1_sram_reader_ev_pending_re = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_reader_ev_pending_w;
reg           builder_csr_bankarray_csrbank1_sram_reader_ev_pending_we = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_reader_ev_status_r;
reg           builder_csr_bankarray_csrbank1_sram_reader_ev_status_re = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_reader_ev_status_w;
reg           builder_csr_bankarray_csrbank1_sram_reader_ev_status_we = 1'd0;
wire   [10:0] builder_csr_bankarray_csrbank1_sram_reader_length_r;
reg           builder_csr_bankarray_csrbank1_sram_reader_length_re = 1'd0;
wire   [10:0] builder_csr_bankarray_csrbank1_sram_reader_length_w;
reg           builder_csr_bankarray_csrbank1_sram_reader_length_we = 1'd0;
wire    [1:0] builder_csr_bankarray_csrbank1_sram_reader_level_r;
reg           builder_csr_bankarray_csrbank1_sram_reader_level_re = 1'd0;
wire    [1:0] builder_csr_bankarray_csrbank1_sram_reader_level_w;
reg           builder_csr_bankarray_csrbank1_sram_reader_level_we = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_reader_ready_r;
reg           builder_csr_bankarray_csrbank1_sram_reader_ready_re = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_reader_ready_w;
reg           builder_csr_bankarray_csrbank1_sram_reader_ready_we = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_reader_slot_r;
reg           builder_csr_bankarray_csrbank1_sram_reader_slot_re = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_reader_slot_w;
reg           builder_csr_bankarray_csrbank1_sram_reader_slot_we = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank1_sram_writer_errors_r;
reg           builder_csr_bankarray_csrbank1_sram_writer_errors_re = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank1_sram_writer_errors_w;
reg           builder_csr_bankarray_csrbank1_sram_writer_errors_we = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_writer_ev_enable_r;
reg           builder_csr_bankarray_csrbank1_sram_writer_ev_enable_re = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_writer_ev_enable_w;
reg           builder_csr_bankarray_csrbank1_sram_writer_ev_enable_we = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_writer_ev_pending_r;
reg           builder_csr_bankarray_csrbank1_sram_writer_ev_pending_re = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_writer_ev_pending_w;
reg           builder_csr_bankarray_csrbank1_sram_writer_ev_pending_we = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_writer_ev_status_r;
reg           builder_csr_bankarray_csrbank1_sram_writer_ev_status_re = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_writer_ev_status_w;
reg           builder_csr_bankarray_csrbank1_sram_writer_ev_status_we = 1'd0;
wire   [10:0] builder_csr_bankarray_csrbank1_sram_writer_length_r;
reg           builder_csr_bankarray_csrbank1_sram_writer_length_re = 1'd0;
wire   [10:0] builder_csr_bankarray_csrbank1_sram_writer_length_w;
reg           builder_csr_bankarray_csrbank1_sram_writer_length_we = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_writer_slot_r;
reg           builder_csr_bankarray_csrbank1_sram_writer_slot_re = 1'd0;
wire          builder_csr_bankarray_csrbank1_sram_writer_slot_w;
reg           builder_csr_bankarray_csrbank1_sram_writer_slot_we = 1'd0;
wire          builder_csr_bankarray_csrbank2_crg_reset_r;
reg           builder_csr_bankarray_csrbank2_crg_reset_re = 1'd0;
wire          builder_csr_bankarray_csrbank2_crg_reset_w;
reg           builder_csr_bankarray_csrbank2_crg_reset_we = 1'd0;
wire          builder_csr_bankarray_csrbank2_mdio_r_r;
reg           builder_csr_bankarray_csrbank2_mdio_r_re = 1'd0;
wire          builder_csr_bankarray_csrbank2_mdio_r_w;
reg           builder_csr_bankarray_csrbank2_mdio_r_we = 1'd0;
wire    [2:0] builder_csr_bankarray_csrbank2_mdio_w_r;
reg           builder_csr_bankarray_csrbank2_mdio_w_re = 1'd0;
wire    [2:0] builder_csr_bankarray_csrbank2_mdio_w_w;
reg           builder_csr_bankarray_csrbank2_mdio_w_we = 1'd0;
wire          builder_csr_bankarray_csrbank2_sel;
wire    [7:0] builder_csr_bankarray_csrbank3_out_r;
reg           builder_csr_bankarray_csrbank3_out_re = 1'd0;
wire    [7:0] builder_csr_bankarray_csrbank3_out_w;
reg           builder_csr_bankarray_csrbank3_out_we = 1'd0;
wire          builder_csr_bankarray_csrbank3_sel;
wire          builder_csr_bankarray_csrbank4_en_r;
reg           builder_csr_bankarray_csrbank4_en_re = 1'd0;
wire          builder_csr_bankarray_csrbank4_en_w;
reg           builder_csr_bankarray_csrbank4_en_we = 1'd0;
wire          builder_csr_bankarray_csrbank4_ev_enable_r;
reg           builder_csr_bankarray_csrbank4_ev_enable_re = 1'd0;
wire          builder_csr_bankarray_csrbank4_ev_enable_w;
reg           builder_csr_bankarray_csrbank4_ev_enable_we = 1'd0;
wire          builder_csr_bankarray_csrbank4_ev_pending_r;
reg           builder_csr_bankarray_csrbank4_ev_pending_re = 1'd0;
wire          builder_csr_bankarray_csrbank4_ev_pending_w;
reg           builder_csr_bankarray_csrbank4_ev_pending_we = 1'd0;
wire          builder_csr_bankarray_csrbank4_ev_status_r;
reg           builder_csr_bankarray_csrbank4_ev_status_re = 1'd0;
wire          builder_csr_bankarray_csrbank4_ev_status_w;
reg           builder_csr_bankarray_csrbank4_ev_status_we = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank4_load_r;
reg           builder_csr_bankarray_csrbank4_load_re = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank4_load_w;
reg           builder_csr_bankarray_csrbank4_load_we = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank4_reload_r;
reg           builder_csr_bankarray_csrbank4_reload_re = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank4_reload_w;
reg           builder_csr_bankarray_csrbank4_reload_we = 1'd0;
wire          builder_csr_bankarray_csrbank4_sel;
wire          builder_csr_bankarray_csrbank4_update_value_r;
reg           builder_csr_bankarray_csrbank4_update_value_re = 1'd0;
wire          builder_csr_bankarray_csrbank4_update_value_w;
reg           builder_csr_bankarray_csrbank4_update_value_we = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank4_value_r;
reg           builder_csr_bankarray_csrbank4_value_re = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank4_value_w;
reg           builder_csr_bankarray_csrbank4_value_we = 1'd0;
wire    [1:0] builder_csr_bankarray_csrbank5_ev_enable_r;
reg           builder_csr_bankarray_csrbank5_ev_enable_re = 1'd0;
wire    [1:0] builder_csr_bankarray_csrbank5_ev_enable_w;
reg           builder_csr_bankarray_csrbank5_ev_enable_we = 1'd0;
wire    [1:0] builder_csr_bankarray_csrbank5_ev_pending_r;
reg           builder_csr_bankarray_csrbank5_ev_pending_re = 1'd0;
wire    [1:0] builder_csr_bankarray_csrbank5_ev_pending_w;
reg           builder_csr_bankarray_csrbank5_ev_pending_we = 1'd0;
wire    [1:0] builder_csr_bankarray_csrbank5_ev_status_r;
reg           builder_csr_bankarray_csrbank5_ev_status_re = 1'd0;
wire    [1:0] builder_csr_bankarray_csrbank5_ev_status_w;
reg           builder_csr_bankarray_csrbank5_ev_status_we = 1'd0;
wire          builder_csr_bankarray_csrbank5_rxempty_r;
reg           builder_csr_bankarray_csrbank5_rxempty_re = 1'd0;
wire          builder_csr_bankarray_csrbank5_rxempty_w;
reg           builder_csr_bankarray_csrbank5_rxempty_we = 1'd0;
wire          builder_csr_bankarray_csrbank5_rxfull_r;
reg           builder_csr_bankarray_csrbank5_rxfull_re = 1'd0;
wire          builder_csr_bankarray_csrbank5_rxfull_w;
reg           builder_csr_bankarray_csrbank5_rxfull_we = 1'd0;
wire          builder_csr_bankarray_csrbank5_sel;
wire          builder_csr_bankarray_csrbank5_txempty_r;
reg           builder_csr_bankarray_csrbank5_txempty_re = 1'd0;
wire          builder_csr_bankarray_csrbank5_txempty_w;
reg           builder_csr_bankarray_csrbank5_txempty_we = 1'd0;
wire          builder_csr_bankarray_csrbank5_txfull_r;
reg           builder_csr_bankarray_csrbank5_txfull_re = 1'd0;
wire          builder_csr_bankarray_csrbank5_txfull_w;
reg           builder_csr_bankarray_csrbank5_txfull_we = 1'd0;
wire    [7:0] builder_csr_bankarray_dat_r;
wire   [13:0] builder_csr_bankarray_interface0_bank_bus_adr;
reg    [31:0] builder_csr_bankarray_interface0_bank_bus_dat_r = 32'd0;
wire   [31:0] builder_csr_bankarray_interface0_bank_bus_dat_w;
wire          builder_csr_bankarray_interface0_bank_bus_re;
wire          builder_csr_bankarray_interface0_bank_bus_we;
wire   [13:0] builder_csr_bankarray_interface1_bank_bus_adr;
reg    [31:0] builder_csr_bankarray_interface1_bank_bus_dat_r = 32'd0;
wire   [31:0] builder_csr_bankarray_interface1_bank_bus_dat_w;
wire          builder_csr_bankarray_interface1_bank_bus_re;
wire          builder_csr_bankarray_interface1_bank_bus_we;
wire   [13:0] builder_csr_bankarray_interface2_bank_bus_adr;
reg    [31:0] builder_csr_bankarray_interface2_bank_bus_dat_r = 32'd0;
wire   [31:0] builder_csr_bankarray_interface2_bank_bus_dat_w;
wire          builder_csr_bankarray_interface2_bank_bus_re;
wire          builder_csr_bankarray_interface2_bank_bus_we;
wire   [13:0] builder_csr_bankarray_interface3_bank_bus_adr;
reg    [31:0] builder_csr_bankarray_interface3_bank_bus_dat_r = 32'd0;
wire   [31:0] builder_csr_bankarray_interface3_bank_bus_dat_w;
wire          builder_csr_bankarray_interface3_bank_bus_re;
wire          builder_csr_bankarray_interface3_bank_bus_we;
wire   [13:0] builder_csr_bankarray_interface4_bank_bus_adr;
reg    [31:0] builder_csr_bankarray_interface4_bank_bus_dat_r = 32'd0;
wire   [31:0] builder_csr_bankarray_interface4_bank_bus_dat_w;
wire          builder_csr_bankarray_interface4_bank_bus_re;
wire          builder_csr_bankarray_interface4_bank_bus_we;
wire   [13:0] builder_csr_bankarray_interface5_bank_bus_adr;
reg    [31:0] builder_csr_bankarray_interface5_bank_bus_dat_r = 32'd0;
wire   [31:0] builder_csr_bankarray_interface5_bank_bus_dat_w;
wire          builder_csr_bankarray_interface5_bank_bus_re;
wire          builder_csr_bankarray_interface5_bank_bus_we;
wire          builder_csr_bankarray_sel;
reg           builder_csr_bankarray_sel_r = 1'd0;
wire   [13:0] builder_csr_bankarray_sram_bus_adr;
reg    [31:0] builder_csr_bankarray_sram_bus_dat_r = 32'd0;
wire   [31:0] builder_csr_bankarray_sram_bus_dat_w;
wire          builder_csr_bankarray_sram_bus_re;
wire          builder_csr_bankarray_sram_bus_we;
reg           builder_csr_data_width = 1'd0;
wire   [13:0] builder_csr_interconnect_adr;
wire   [31:0] builder_csr_interconnect_dat_r;
wire   [31:0] builder_csr_interconnect_dat_w;
wire          builder_csr_interconnect_re;
wire          builder_csr_interconnect_we;
wire          builder_done;
reg           builder_error = 1'd0;
reg           builder_grant = 1'd0;
reg           builder_interface0_ack = 1'd0;
wire   [29:0] builder_interface0_adr;
wire    [1:0] builder_interface0_bte;
wire    [2:0] builder_interface0_cti;
wire          builder_interface0_cyc;
reg    [31:0] builder_interface0_dat_r = 32'd0;
wire   [31:0] builder_interface0_dat_w;
reg           builder_interface0_err = 1'd0;
wire    [3:0] builder_interface0_sel;
wire          builder_interface0_stb;
wire          builder_interface0_we;
reg    [13:0] builder_interface1_adr = 14'd0;
wire   [31:0] builder_interface1_dat_r;
reg    [31:0] builder_interface1_dat_w = 32'd0;
reg           builder_interface1_re = 1'd0;
reg           builder_interface1_we = 1'd0;
wire          builder_liteethphyrgmii_pll_fb;
wire          builder_liteethphyrgmii_reset0;
wire          builder_liteethphyrgmii_reset1;
wire          builder_liteethphyrgmii_reset2;
wire          builder_liteethphyrgmii_reset3;
wire          builder_liteethphyrgmii_reset4;
wire          builder_liteethphyrgmii_reset5;
wire          builder_liteethphyrgmii_reset6;
wire          builder_liteethphyrgmii_reset7;
wire    [1:0] builder_request;
reg    [29:0] builder_rhs_self0 = 30'd0;
reg    [31:0] builder_rhs_self1 = 32'd0;
reg     [3:0] builder_rhs_self2 = 4'd0;
reg           builder_rhs_self3 = 1'd0;
reg           builder_rhs_self4 = 1'd0;
reg           builder_rhs_self5 = 1'd0;
reg     [2:0] builder_rhs_self6 = 3'd0;
reg     [1:0] builder_rhs_self7 = 2'd0;
reg           builder_rs232phyrx_next_state = 1'd0;
reg           builder_rs232phyrx_state = 1'd0;
reg           builder_rs232phytx_next_state = 1'd0;
reg           builder_rs232phytx_state = 1'd0;
reg           builder_shared_ack = 1'd0;
wire   [29:0] builder_shared_adr;
wire    [1:0] builder_shared_bte;
wire    [2:0] builder_shared_cti;
wire          builder_shared_cyc;
reg    [31:0] builder_shared_dat_r = 32'd0;
wire   [31:0] builder_shared_dat_w;
wire          builder_shared_err;
wire    [3:0] builder_shared_sel;
wire          builder_shared_stb;
wire          builder_shared_we;
reg     [5:0] builder_slave_sel = 6'd0;
reg     [5:0] builder_slave_sel_r = 6'd0;
wire          builder_wait;
reg           builder_wishbone2csr_next_state = 1'd0;
reg           builder_wishbone2csr_state = 1'd0;
wire          builder_xilinxasyncresetsynchronizerimpl0_async_reset;
wire          builder_xilinxasyncresetsynchronizerimpl0_rst_buf;
wire          builder_xilinxasyncresetsynchronizerimpl0_rst_meta;
wire          builder_xilinxasyncresetsynchronizerimpl1_async_reset;
wire          builder_xilinxasyncresetsynchronizerimpl1_rst_meta;
wire          builder_xilinxasyncresetsynchronizerimpl2_async_reset;
wire          builder_xilinxasyncresetsynchronizerimpl2_rst_meta;
wire          builder_xilinxasyncresetsynchronizerimpl3_async_reset;
wire          builder_xilinxasyncresetsynchronizerimpl3_rst_meta;
wire          builder_xilinxasyncresetsynchronizerimpl4_async_reset;
wire          builder_xilinxasyncresetsynchronizerimpl4_rst_meta;
wire          builder_xilinxasyncresetsynchronizerimpl5_async_reset;
wire          builder_xilinxasyncresetsynchronizerimpl5_expr;
wire          builder_xilinxasyncresetsynchronizerimpl5_rst_meta;
wire          builder_xilinxasyncresetsynchronizerimpl6_rst_meta;
wire          builder_xilinxasyncresetsynchronizerimpl7_rst_meta;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl00 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl01 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl10 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg     [5:0] builder_xilinxmultiregimpl100 = 6'd0;
(* async_reg = "true", dont_touch = "true" *)
reg     [5:0] builder_xilinxmultiregimpl101 = 6'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl11 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg     [5:0] builder_xilinxmultiregimpl110 = 6'd0;
(* async_reg = "true", dont_touch = "true" *)
reg     [5:0] builder_xilinxmultiregimpl111 = 6'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl20 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl21 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl30 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl31 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg     [5:0] builder_xilinxmultiregimpl40 = 6'd0;
(* async_reg = "true", dont_touch = "true" *)
reg     [5:0] builder_xilinxmultiregimpl41 = 6'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg     [5:0] builder_xilinxmultiregimpl50 = 6'd0;
(* async_reg = "true", dont_touch = "true" *)
reg     [5:0] builder_xilinxmultiregimpl51 = 6'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl60 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl61 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl70 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl71 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl80 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl81 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl90 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl91 = 1'd0;
wire          clk100_clk;
wire          clk100_rst;
(* dont_touch = "true" *)
wire          eth_rx_clk;
wire          eth_rx_rst;
(* dont_touch = "true" *)
wire          eth_tx_clk;
wire          eth_tx_delayed_clk;
wire          eth_tx_rst;
wire          idelay_clk;
wire          idelay_rst;
wire   [14:0] main_basesoc_adr;
reg           main_basesoc_adr_burst = 1'd0;
wire          main_basesoc_bus_error;
reg    [31:0] main_basesoc_bus_errors = 32'd0;
wire          main_basesoc_bus_errors_rd_stb;
wire   [31:0] main_basesoc_bus_errors_status;
reg           main_basesoc_bus_errors_wr_stb = 1'd0;
wire          main_basesoc_core_bufferizeendpoints_pipe_valid_sink_first;
wire          main_basesoc_core_bufferizeendpoints_pipe_valid_sink_last;
wire          main_basesoc_core_bufferizeendpoints_pipe_valid_sink_payload_be;
wire    [7:0] main_basesoc_core_bufferizeendpoints_pipe_valid_sink_payload_data;
wire          main_basesoc_core_bufferizeendpoints_pipe_valid_sink_payload_error;
wire          main_basesoc_core_bufferizeendpoints_pipe_valid_sink_ready;
wire          main_basesoc_core_bufferizeendpoints_pipe_valid_sink_valid;
reg           main_basesoc_core_bufferizeendpoints_pipe_valid_source_first = 1'd0;
reg           main_basesoc_core_bufferizeendpoints_pipe_valid_source_last = 1'd0;
reg           main_basesoc_core_bufferizeendpoints_pipe_valid_source_payload_be = 1'd0;
reg     [7:0] main_basesoc_core_bufferizeendpoints_pipe_valid_source_payload_data = 8'd0;
reg           main_basesoc_core_bufferizeendpoints_pipe_valid_source_payload_error = 1'd0;
wire          main_basesoc_core_bufferizeendpoints_pipe_valid_source_ready;
reg           main_basesoc_core_bufferizeendpoints_pipe_valid_source_valid = 1'd0;
wire          main_basesoc_core_bufferizeendpoints_sink_sink_first;
wire          main_basesoc_core_bufferizeendpoints_sink_sink_last;
wire          main_basesoc_core_bufferizeendpoints_sink_sink_payload_be;
wire    [7:0] main_basesoc_core_bufferizeendpoints_sink_sink_payload_data;
wire          main_basesoc_core_bufferizeendpoints_sink_sink_payload_error;
wire          main_basesoc_core_bufferizeendpoints_sink_sink_ready;
wire          main_basesoc_core_bufferizeendpoints_sink_sink_valid;
wire          main_basesoc_core_bufferizeendpoints_source_source_first;
wire          main_basesoc_core_bufferizeendpoints_source_source_last;
wire          main_basesoc_core_bufferizeendpoints_source_source_payload_be;
wire    [7:0] main_basesoc_core_bufferizeendpoints_source_source_payload_data;
wire          main_basesoc_core_bufferizeendpoints_source_source_payload_error;
wire          main_basesoc_core_bufferizeendpoints_source_source_ready;
wire          main_basesoc_core_bufferizeendpoints_source_source_valid;
wire          main_basesoc_core_cdc_rst;
wire          main_basesoc_core_crc_errors_rd_stb;
reg    [31:0] main_basesoc_core_crc_errors_status = 32'd0;
reg           main_basesoc_core_crc_errors_wr_stb = 1'd0;
reg           main_basesoc_core_liteethmaccrc32checker_be = 1'd0;
reg           main_basesoc_core_liteethmaccrc32checker_be_next_value0 = 1'd0;
reg           main_basesoc_core_liteethmaccrc32checker_be_next_value_ce0 = 1'd0;
wire          main_basesoc_core_liteethmaccrc32checker_crc_be;
reg           main_basesoc_core_liteethmaccrc32checker_crc_ce = 1'd0;
reg    [31:0] main_basesoc_core_liteethmaccrc32checker_crc_crc_next = 32'd0;
wire   [31:0] main_basesoc_core_liteethmaccrc32checker_crc_crc_prev;
wire    [7:0] main_basesoc_core_liteethmaccrc32checker_crc_data0;
reg     [7:0] main_basesoc_core_liteethmaccrc32checker_crc_data1 = 8'd0;
reg           main_basesoc_core_liteethmaccrc32checker_crc_error = 1'd0;
reg    [31:0] main_basesoc_core_liteethmaccrc32checker_crc_reg = 32'hffffffff;
reg           main_basesoc_core_liteethmaccrc32checker_crc_reset = 1'd0;
reg           main_basesoc_core_liteethmaccrc32checker_error = 1'd0;
wire          main_basesoc_core_liteethmaccrc32checker_fifo_full;
wire          main_basesoc_core_liteethmaccrc32checker_fifo_in;
wire          main_basesoc_core_liteethmaccrc32checker_fifo_out;
reg           main_basesoc_core_liteethmaccrc32checker_fifo_reset = 1'd0;
reg           main_basesoc_core_liteethmaccrc32checker_is_ongoing0 = 1'd0;
reg           main_basesoc_core_liteethmaccrc32checker_is_ongoing1 = 1'd0;
reg           main_basesoc_core_liteethmaccrc32checker_is_ongoing2 = 1'd0;
reg           main_basesoc_core_liteethmaccrc32checker_last_error = 1'd0;
reg           main_basesoc_core_liteethmaccrc32checker_last_error_next_value1 = 1'd0;
reg           main_basesoc_core_liteethmaccrc32checker_last_error_next_value_ce1 = 1'd0;
wire          main_basesoc_core_liteethmaccrc32checker_last_word_error;
reg           main_basesoc_core_liteethmaccrc32checker_packet_error = 1'd0;
wire          main_basesoc_core_liteethmaccrc32checker_sink_sink_first;
wire          main_basesoc_core_liteethmaccrc32checker_sink_sink_last;
wire          main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_be;
wire    [7:0] main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_data;
wire          main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_error;
reg           main_basesoc_core_liteethmaccrc32checker_sink_sink_ready = 1'd0;
wire          main_basesoc_core_liteethmaccrc32checker_sink_sink_valid;
wire          main_basesoc_core_liteethmaccrc32checker_source_source_first;
reg           main_basesoc_core_liteethmaccrc32checker_source_source_last = 1'd0;
reg           main_basesoc_core_liteethmaccrc32checker_source_source_payload_be = 1'd0;
wire    [7:0] main_basesoc_core_liteethmaccrc32checker_source_source_payload_data;
reg           main_basesoc_core_liteethmaccrc32checker_source_source_payload_error = 1'd0;
wire          main_basesoc_core_liteethmaccrc32checker_source_source_ready;
reg           main_basesoc_core_liteethmaccrc32checker_source_source_valid = 1'd0;
reg     [2:0] main_basesoc_core_liteethmaccrc32checker_syncfifo_consume = 3'd0;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_do_read;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_in_first;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_in_last;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_in_payload_be;
wire    [7:0] main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_in_payload_data;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_in_payload_error;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_out_first;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_out_last;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_out_payload_be;
wire    [7:0] main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_out_payload_data;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_out_payload_error;
reg     [2:0] main_basesoc_core_liteethmaccrc32checker_syncfifo_level = 3'd0;
reg     [2:0] main_basesoc_core_liteethmaccrc32checker_syncfifo_produce = 3'd0;
wire    [2:0] main_basesoc_core_liteethmaccrc32checker_syncfifo_rdport_adr;
wire   [11:0] main_basesoc_core_liteethmaccrc32checker_syncfifo_rdport_dat_r;
reg           main_basesoc_core_liteethmaccrc32checker_syncfifo_replace = 1'd0;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_first;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_last;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_payload_be;
wire    [7:0] main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_payload_data;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_payload_error;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_ready;
reg           main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_valid = 1'd0;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_source_first;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_source_last;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_source_payload_be;
wire    [7:0] main_basesoc_core_liteethmaccrc32checker_syncfifo_source_payload_data;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_source_payload_error;
reg           main_basesoc_core_liteethmaccrc32checker_syncfifo_source_ready = 1'd0;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_source_valid;
wire   [11:0] main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_din;
wire   [11:0] main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_dout;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_re;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_readable;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_we;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_writable;
reg     [2:0] main_basesoc_core_liteethmaccrc32checker_syncfifo_wrport_adr = 3'd0;
wire   [11:0] main_basesoc_core_liteethmaccrc32checker_syncfifo_wrport_dat_r;
wire   [11:0] main_basesoc_core_liteethmaccrc32checker_syncfifo_wrport_dat_w;
wire          main_basesoc_core_liteethmaccrc32checker_syncfifo_wrport_we;
reg           main_basesoc_core_liteethmaccrc32inserter_be0 = 1'd0;
reg           main_basesoc_core_liteethmaccrc32inserter_be0_clockdomainsrenamer1_next_value1 = 1'd0;
reg           main_basesoc_core_liteethmaccrc32inserter_be0_clockdomainsrenamer1_next_value_ce1 = 1'd0;
wire          main_basesoc_core_liteethmaccrc32inserter_be1;
reg           main_basesoc_core_liteethmaccrc32inserter_ce = 1'd0;
reg     [1:0] main_basesoc_core_liteethmaccrc32inserter_cnt = 2'd3;
wire          main_basesoc_core_liteethmaccrc32inserter_cnt_done;
reg    [31:0] main_basesoc_core_liteethmaccrc32inserter_crc_next = 32'd0;
reg    [31:0] main_basesoc_core_liteethmaccrc32inserter_crc_packet = 32'd0;
reg    [31:0] main_basesoc_core_liteethmaccrc32inserter_crc_packet_clockdomainsrenamer1_next_value0 = 32'd0;
reg           main_basesoc_core_liteethmaccrc32inserter_crc_packet_clockdomainsrenamer1_next_value_ce0 = 1'd0;
wire   [31:0] main_basesoc_core_liteethmaccrc32inserter_crc_prev;
wire    [7:0] main_basesoc_core_liteethmaccrc32inserter_data0;
wire    [7:0] main_basesoc_core_liteethmaccrc32inserter_data1;
reg           main_basesoc_core_liteethmaccrc32inserter_error = 1'd0;
reg           main_basesoc_core_liteethmaccrc32inserter_is_ongoing0 = 1'd0;
reg           main_basesoc_core_liteethmaccrc32inserter_is_ongoing1 = 1'd0;
reg    [31:0] main_basesoc_core_liteethmaccrc32inserter_reg = 32'hffffffff;
reg           main_basesoc_core_liteethmaccrc32inserter_reset = 1'd0;
wire          main_basesoc_core_liteethmaccrc32inserter_sink_first;
wire          main_basesoc_core_liteethmaccrc32inserter_sink_last;
wire          main_basesoc_core_liteethmaccrc32inserter_sink_payload_be;
wire    [7:0] main_basesoc_core_liteethmaccrc32inserter_sink_payload_data;
wire          main_basesoc_core_liteethmaccrc32inserter_sink_payload_error;
reg           main_basesoc_core_liteethmaccrc32inserter_sink_ready = 1'd0;
wire          main_basesoc_core_liteethmaccrc32inserter_sink_valid;
reg           main_basesoc_core_liteethmaccrc32inserter_source_first = 1'd0;
reg           main_basesoc_core_liteethmaccrc32inserter_source_last = 1'd0;
reg           main_basesoc_core_liteethmaccrc32inserter_source_payload_be = 1'd0;
reg     [7:0] main_basesoc_core_liteethmaccrc32inserter_source_payload_data = 8'd0;
reg           main_basesoc_core_liteethmaccrc32inserter_source_payload_error = 1'd0;
wire          main_basesoc_core_liteethmaccrc32inserter_source_ready;
reg           main_basesoc_core_liteethmaccrc32inserter_source_valid = 1'd0;
reg    [31:0] main_basesoc_core_liteethmaccrc32inserter_value = 32'd0;
wire          main_basesoc_core_pipe_valid_sink_first;
wire          main_basesoc_core_pipe_valid_sink_last;
wire          main_basesoc_core_pipe_valid_sink_payload_be;
wire    [7:0] main_basesoc_core_pipe_valid_sink_payload_data;
wire          main_basesoc_core_pipe_valid_sink_payload_error;
wire          main_basesoc_core_pipe_valid_sink_ready;
wire          main_basesoc_core_pipe_valid_sink_valid;
reg           main_basesoc_core_pipe_valid_source_first = 1'd0;
reg           main_basesoc_core_pipe_valid_source_last = 1'd0;
reg           main_basesoc_core_pipe_valid_source_payload_be = 1'd0;
reg     [7:0] main_basesoc_core_pipe_valid_source_payload_data = 8'd0;
reg           main_basesoc_core_pipe_valid_source_payload_error = 1'd0;
wire          main_basesoc_core_pipe_valid_source_ready;
reg           main_basesoc_core_pipe_valid_source_valid = 1'd0;
wire          main_basesoc_core_preamble_errors_rd_stb;
reg    [31:0] main_basesoc_core_preamble_errors_status = 32'd0;
reg           main_basesoc_core_preamble_errors_wr_stb = 1'd0;
wire          main_basesoc_core_pulsesynchronizer0_i;
wire          main_basesoc_core_pulsesynchronizer0_o;
reg           main_basesoc_core_pulsesynchronizer0_toggle_i = 1'd0;
wire          main_basesoc_core_pulsesynchronizer0_toggle_o;
reg           main_basesoc_core_pulsesynchronizer0_toggle_o_r = 1'd0;
wire          main_basesoc_core_pulsesynchronizer1_i;
wire          main_basesoc_core_pulsesynchronizer1_o;
reg           main_basesoc_core_pulsesynchronizer1_toggle_i = 1'd0;
wire          main_basesoc_core_pulsesynchronizer1_toggle_o;
reg           main_basesoc_core_pulsesynchronizer1_toggle_o_r = 1'd0;
wire          main_basesoc_core_rd_stb;
wire   [41:0] main_basesoc_core_rx_cdc_cdc_asyncfifo_din;
wire   [41:0] main_basesoc_core_rx_cdc_cdc_asyncfifo_dout;
wire          main_basesoc_core_rx_cdc_cdc_asyncfifo_re;
wire          main_basesoc_core_rx_cdc_cdc_asyncfifo_readable;
wire          main_basesoc_core_rx_cdc_cdc_asyncfifo_we;
wire          main_basesoc_core_rx_cdc_cdc_asyncfifo_writable;
wire    [5:0] main_basesoc_core_rx_cdc_cdc_consume_wdomain;
wire          main_basesoc_core_rx_cdc_cdc_fifo_in_first;
wire          main_basesoc_core_rx_cdc_cdc_fifo_in_last;
wire    [3:0] main_basesoc_core_rx_cdc_cdc_fifo_in_payload_be;
wire   [31:0] main_basesoc_core_rx_cdc_cdc_fifo_in_payload_data;
wire    [3:0] main_basesoc_core_rx_cdc_cdc_fifo_in_payload_error;
wire          main_basesoc_core_rx_cdc_cdc_fifo_out_first;
wire          main_basesoc_core_rx_cdc_cdc_fifo_out_last;
wire    [3:0] main_basesoc_core_rx_cdc_cdc_fifo_out_payload_be;
wire   [31:0] main_basesoc_core_rx_cdc_cdc_fifo_out_payload_data;
wire    [3:0] main_basesoc_core_rx_cdc_cdc_fifo_out_payload_error;
wire          main_basesoc_core_rx_cdc_cdc_graycounter0_ce;
(* dont_touch = "true" *)
reg     [5:0] main_basesoc_core_rx_cdc_cdc_graycounter0_q = 6'd0;
reg     [5:0] main_basesoc_core_rx_cdc_cdc_graycounter0_q_binary = 6'd0;
wire    [5:0] main_basesoc_core_rx_cdc_cdc_graycounter0_q_next;
reg     [5:0] main_basesoc_core_rx_cdc_cdc_graycounter0_q_next_binary = 6'd0;
wire          main_basesoc_core_rx_cdc_cdc_graycounter1_ce;
(* dont_touch = "true" *)
reg     [5:0] main_basesoc_core_rx_cdc_cdc_graycounter1_q = 6'd0;
reg     [5:0] main_basesoc_core_rx_cdc_cdc_graycounter1_q_binary = 6'd0;
wire    [5:0] main_basesoc_core_rx_cdc_cdc_graycounter1_q_next;
reg     [5:0] main_basesoc_core_rx_cdc_cdc_graycounter1_q_next_binary = 6'd0;
wire    [5:0] main_basesoc_core_rx_cdc_cdc_produce_rdomain;
wire    [4:0] main_basesoc_core_rx_cdc_cdc_rdport_adr;
wire   [41:0] main_basesoc_core_rx_cdc_cdc_rdport_dat_r;
wire          main_basesoc_core_rx_cdc_cdc_reset_read;
wire          main_basesoc_core_rx_cdc_cdc_reset_write;
wire          main_basesoc_core_rx_cdc_cdc_sink_first;
wire          main_basesoc_core_rx_cdc_cdc_sink_last;
wire    [3:0] main_basesoc_core_rx_cdc_cdc_sink_payload_be;
wire   [31:0] main_basesoc_core_rx_cdc_cdc_sink_payload_data;
wire    [3:0] main_basesoc_core_rx_cdc_cdc_sink_payload_error;
wire          main_basesoc_core_rx_cdc_cdc_sink_ready;
wire          main_basesoc_core_rx_cdc_cdc_sink_valid;
wire          main_basesoc_core_rx_cdc_cdc_source_first;
wire          main_basesoc_core_rx_cdc_cdc_source_last;
wire    [3:0] main_basesoc_core_rx_cdc_cdc_source_payload_be;
wire   [31:0] main_basesoc_core_rx_cdc_cdc_source_payload_data;
wire    [3:0] main_basesoc_core_rx_cdc_cdc_source_payload_error;
wire          main_basesoc_core_rx_cdc_cdc_source_ready;
wire          main_basesoc_core_rx_cdc_cdc_source_valid;
wire    [4:0] main_basesoc_core_rx_cdc_cdc_wrport_adr;
wire   [41:0] main_basesoc_core_rx_cdc_cdc_wrport_dat_r;
wire   [41:0] main_basesoc_core_rx_cdc_cdc_wrport_dat_w;
wire          main_basesoc_core_rx_cdc_cdc_wrport_we;
wire          main_basesoc_core_rx_cdc_ext_rst_to;
wire          main_basesoc_core_rx_cdc_sink_sink_first;
wire          main_basesoc_core_rx_cdc_sink_sink_last;
wire    [3:0] main_basesoc_core_rx_cdc_sink_sink_payload_be;
wire   [31:0] main_basesoc_core_rx_cdc_sink_sink_payload_data;
wire    [3:0] main_basesoc_core_rx_cdc_sink_sink_payload_error;
wire          main_basesoc_core_rx_cdc_sink_sink_ready;
wire          main_basesoc_core_rx_cdc_sink_sink_valid;
wire          main_basesoc_core_rx_cdc_source_source_first;
wire          main_basesoc_core_rx_cdc_source_source_last;
wire    [3:0] main_basesoc_core_rx_cdc_source_source_payload_be;
wire   [31:0] main_basesoc_core_rx_cdc_source_source_payload_data;
wire    [3:0] main_basesoc_core_rx_cdc_source_source_payload_error;
wire          main_basesoc_core_rx_cdc_source_source_ready;
wire          main_basesoc_core_rx_cdc_source_source_valid;
wire          main_basesoc_core_rx_cdc_write_ext_rst;
wire          main_basesoc_core_rx_cdc_write_rst;
reg     [1:0] main_basesoc_core_rx_converter_converter_demux = 2'd0;
wire          main_basesoc_core_rx_converter_converter_load_part;
wire          main_basesoc_core_rx_converter_converter_sink_first;
wire          main_basesoc_core_rx_converter_converter_sink_last;
wire    [9:0] main_basesoc_core_rx_converter_converter_sink_payload_data;
wire          main_basesoc_core_rx_converter_converter_sink_ready;
wire          main_basesoc_core_rx_converter_converter_sink_valid;
reg           main_basesoc_core_rx_converter_converter_source_first = 1'd0;
reg           main_basesoc_core_rx_converter_converter_source_last = 1'd0;
reg    [39:0] main_basesoc_core_rx_converter_converter_source_payload_data = 40'd0;
reg     [2:0] main_basesoc_core_rx_converter_converter_source_payload_valid_token_count = 3'd0;
wire          main_basesoc_core_rx_converter_converter_source_ready;
wire          main_basesoc_core_rx_converter_converter_source_valid;
reg           main_basesoc_core_rx_converter_converter_strobe_all = 1'd0;
wire          main_basesoc_core_rx_converter_sink_sink_first;
wire          main_basesoc_core_rx_converter_sink_sink_last;
wire          main_basesoc_core_rx_converter_sink_sink_payload_be;
wire    [7:0] main_basesoc_core_rx_converter_sink_sink_payload_data;
wire          main_basesoc_core_rx_converter_sink_sink_payload_error;
wire          main_basesoc_core_rx_converter_sink_sink_ready;
wire          main_basesoc_core_rx_converter_sink_sink_valid;
wire          main_basesoc_core_rx_converter_source_source_first;
wire          main_basesoc_core_rx_converter_source_source_last;
reg     [3:0] main_basesoc_core_rx_converter_source_source_payload_be = 4'd0;
reg    [31:0] main_basesoc_core_rx_converter_source_source_payload_data = 32'd0;
reg     [3:0] main_basesoc_core_rx_converter_source_source_payload_error = 4'd0;
wire          main_basesoc_core_rx_converter_source_source_ready;
wire          main_basesoc_core_rx_converter_source_source_valid;
reg    [10:0] main_basesoc_core_rx_padding_length = 11'd0;
wire    [3:0] main_basesoc_core_rx_padding_length_inc;
wire          main_basesoc_core_rx_padding_sink_first;
wire          main_basesoc_core_rx_padding_sink_last;
wire          main_basesoc_core_rx_padding_sink_payload_be;
wire    [7:0] main_basesoc_core_rx_padding_sink_payload_data;
wire          main_basesoc_core_rx_padding_sink_payload_error;
wire          main_basesoc_core_rx_padding_sink_ready;
wire          main_basesoc_core_rx_padding_sink_valid;
wire          main_basesoc_core_rx_padding_source_first;
wire          main_basesoc_core_rx_padding_source_last;
wire          main_basesoc_core_rx_padding_source_payload_be;
wire    [7:0] main_basesoc_core_rx_padding_source_payload_data;
reg           main_basesoc_core_rx_padding_source_payload_error = 1'd0;
wire          main_basesoc_core_rx_padding_source_ready;
wire          main_basesoc_core_rx_padding_source_valid;
reg           main_basesoc_core_rx_preamble_error = 1'd0;
reg    [63:0] main_basesoc_core_rx_preamble_preamble = 64'hd555555555555555;
wire          main_basesoc_core_rx_preamble_sink_first;
wire          main_basesoc_core_rx_preamble_sink_last;
wire          main_basesoc_core_rx_preamble_sink_payload_be;
wire    [7:0] main_basesoc_core_rx_preamble_sink_payload_data;
wire          main_basesoc_core_rx_preamble_sink_payload_error;
reg           main_basesoc_core_rx_preamble_sink_ready = 1'd0;
wire          main_basesoc_core_rx_preamble_sink_valid;
reg           main_basesoc_core_rx_preamble_source_first = 1'd0;
reg           main_basesoc_core_rx_preamble_source_last = 1'd0;
wire          main_basesoc_core_rx_preamble_source_payload_be;
wire    [7:0] main_basesoc_core_rx_preamble_source_payload_data;
reg           main_basesoc_core_rx_preamble_source_payload_error = 1'd0;
wire          main_basesoc_core_rx_preamble_source_ready;
reg           main_basesoc_core_rx_preamble_source_valid = 1'd0;
wire          main_basesoc_core_sink_first;
wire          main_basesoc_core_sink_last;
wire    [3:0] main_basesoc_core_sink_payload_be;
wire   [31:0] main_basesoc_core_sink_payload_data;
wire    [3:0] main_basesoc_core_sink_payload_error;
wire          main_basesoc_core_sink_ready;
wire          main_basesoc_core_sink_sink_first;
wire          main_basesoc_core_sink_sink_last;
wire          main_basesoc_core_sink_sink_payload_be;
wire    [7:0] main_basesoc_core_sink_sink_payload_data;
wire          main_basesoc_core_sink_sink_payload_error;
wire          main_basesoc_core_sink_sink_ready;
wire          main_basesoc_core_sink_sink_valid;
wire          main_basesoc_core_sink_valid;
wire          main_basesoc_core_source_first;
wire          main_basesoc_core_source_last;
wire    [3:0] main_basesoc_core_source_payload_be;
wire   [31:0] main_basesoc_core_source_payload_data;
wire    [3:0] main_basesoc_core_source_payload_error;
wire          main_basesoc_core_source_ready;
wire          main_basesoc_core_source_source_first;
wire          main_basesoc_core_source_source_last;
wire          main_basesoc_core_source_source_payload_be;
wire    [7:0] main_basesoc_core_source_source_payload_data;
wire          main_basesoc_core_source_source_payload_error;
wire          main_basesoc_core_source_source_ready;
wire          main_basesoc_core_source_source_valid;
wire          main_basesoc_core_source_valid;
reg           main_basesoc_core_status = 1'd1;
wire   [41:0] main_basesoc_core_tx_cdc_cdc_asyncfifo_din;
wire   [41:0] main_basesoc_core_tx_cdc_cdc_asyncfifo_dout;
wire          main_basesoc_core_tx_cdc_cdc_asyncfifo_re;
wire          main_basesoc_core_tx_cdc_cdc_asyncfifo_readable;
wire          main_basesoc_core_tx_cdc_cdc_asyncfifo_we;
wire          main_basesoc_core_tx_cdc_cdc_asyncfifo_writable;
wire    [5:0] main_basesoc_core_tx_cdc_cdc_consume_wdomain;
wire          main_basesoc_core_tx_cdc_cdc_fifo_in_first;
wire          main_basesoc_core_tx_cdc_cdc_fifo_in_last;
wire    [3:0] main_basesoc_core_tx_cdc_cdc_fifo_in_payload_be;
wire   [31:0] main_basesoc_core_tx_cdc_cdc_fifo_in_payload_data;
wire    [3:0] main_basesoc_core_tx_cdc_cdc_fifo_in_payload_error;
wire          main_basesoc_core_tx_cdc_cdc_fifo_out_first;
wire          main_basesoc_core_tx_cdc_cdc_fifo_out_last;
wire    [3:0] main_basesoc_core_tx_cdc_cdc_fifo_out_payload_be;
wire   [31:0] main_basesoc_core_tx_cdc_cdc_fifo_out_payload_data;
wire    [3:0] main_basesoc_core_tx_cdc_cdc_fifo_out_payload_error;
wire          main_basesoc_core_tx_cdc_cdc_graycounter0_ce;
(* dont_touch = "true" *)
reg     [5:0] main_basesoc_core_tx_cdc_cdc_graycounter0_q = 6'd0;
reg     [5:0] main_basesoc_core_tx_cdc_cdc_graycounter0_q_binary = 6'd0;
wire    [5:0] main_basesoc_core_tx_cdc_cdc_graycounter0_q_next;
reg     [5:0] main_basesoc_core_tx_cdc_cdc_graycounter0_q_next_binary = 6'd0;
wire          main_basesoc_core_tx_cdc_cdc_graycounter1_ce;
(* dont_touch = "true" *)
reg     [5:0] main_basesoc_core_tx_cdc_cdc_graycounter1_q = 6'd0;
reg     [5:0] main_basesoc_core_tx_cdc_cdc_graycounter1_q_binary = 6'd0;
wire    [5:0] main_basesoc_core_tx_cdc_cdc_graycounter1_q_next;
reg     [5:0] main_basesoc_core_tx_cdc_cdc_graycounter1_q_next_binary = 6'd0;
wire    [5:0] main_basesoc_core_tx_cdc_cdc_produce_rdomain;
wire    [4:0] main_basesoc_core_tx_cdc_cdc_rdport_adr;
wire   [41:0] main_basesoc_core_tx_cdc_cdc_rdport_dat_r;
wire          main_basesoc_core_tx_cdc_cdc_reset_read;
wire          main_basesoc_core_tx_cdc_cdc_reset_write;
wire          main_basesoc_core_tx_cdc_cdc_sink_first;
wire          main_basesoc_core_tx_cdc_cdc_sink_last;
wire    [3:0] main_basesoc_core_tx_cdc_cdc_sink_payload_be;
wire   [31:0] main_basesoc_core_tx_cdc_cdc_sink_payload_data;
wire    [3:0] main_basesoc_core_tx_cdc_cdc_sink_payload_error;
wire          main_basesoc_core_tx_cdc_cdc_sink_ready;
wire          main_basesoc_core_tx_cdc_cdc_sink_valid;
wire          main_basesoc_core_tx_cdc_cdc_source_first;
wire          main_basesoc_core_tx_cdc_cdc_source_last;
wire    [3:0] main_basesoc_core_tx_cdc_cdc_source_payload_be;
wire   [31:0] main_basesoc_core_tx_cdc_cdc_source_payload_data;
wire    [3:0] main_basesoc_core_tx_cdc_cdc_source_payload_error;
wire          main_basesoc_core_tx_cdc_cdc_source_ready;
wire          main_basesoc_core_tx_cdc_cdc_source_valid;
wire    [4:0] main_basesoc_core_tx_cdc_cdc_wrport_adr;
wire   [41:0] main_basesoc_core_tx_cdc_cdc_wrport_dat_r;
wire   [41:0] main_basesoc_core_tx_cdc_cdc_wrport_dat_w;
wire          main_basesoc_core_tx_cdc_cdc_wrport_we;
wire          main_basesoc_core_tx_cdc_ext_rst_to;
wire          main_basesoc_core_tx_cdc_sink_sink_first;
wire          main_basesoc_core_tx_cdc_sink_sink_last;
wire    [3:0] main_basesoc_core_tx_cdc_sink_sink_payload_be;
wire   [31:0] main_basesoc_core_tx_cdc_sink_sink_payload_data;
wire    [3:0] main_basesoc_core_tx_cdc_sink_sink_payload_error;
wire          main_basesoc_core_tx_cdc_sink_sink_ready;
wire          main_basesoc_core_tx_cdc_sink_sink_valid;
wire          main_basesoc_core_tx_cdc_source_source_first;
wire          main_basesoc_core_tx_cdc_source_source_last;
wire    [3:0] main_basesoc_core_tx_cdc_source_source_payload_be;
wire   [31:0] main_basesoc_core_tx_cdc_source_source_payload_data;
wire    [3:0] main_basesoc_core_tx_cdc_source_source_payload_error;
wire          main_basesoc_core_tx_cdc_source_source_ready;
wire          main_basesoc_core_tx_cdc_source_source_valid;
wire          main_basesoc_core_tx_cdc_write_ext_rst;
wire          main_basesoc_core_tx_cdc_write_rst;
wire          main_basesoc_core_tx_converter_converter_first;
wire          main_basesoc_core_tx_converter_converter_last;
reg     [1:0] main_basesoc_core_tx_converter_converter_mux = 2'd0;
wire          main_basesoc_core_tx_converter_converter_sink_first;
wire          main_basesoc_core_tx_converter_converter_sink_last;
reg    [39:0] main_basesoc_core_tx_converter_converter_sink_payload_data = 40'd0;
wire          main_basesoc_core_tx_converter_converter_sink_ready;
wire          main_basesoc_core_tx_converter_converter_sink_valid;
wire          main_basesoc_core_tx_converter_converter_source_first;
wire          main_basesoc_core_tx_converter_converter_source_last;
reg     [9:0] main_basesoc_core_tx_converter_converter_source_payload_data = 10'd0;
wire          main_basesoc_core_tx_converter_converter_source_payload_valid_token_count;
wire          main_basesoc_core_tx_converter_converter_source_ready;
wire          main_basesoc_core_tx_converter_converter_source_valid;
reg           main_basesoc_core_tx_converter_drop = 1'd0;
reg     [1:0] main_basesoc_core_tx_converter_index = 2'd0;
reg           main_basesoc_core_tx_converter_packet_end = 1'd0;
wire          main_basesoc_core_tx_converter_reset;
wire          main_basesoc_core_tx_converter_sink_sink_first;
wire          main_basesoc_core_tx_converter_sink_sink_last;
wire    [3:0] main_basesoc_core_tx_converter_sink_sink_payload_be;
wire   [31:0] main_basesoc_core_tx_converter_sink_sink_payload_data;
wire    [3:0] main_basesoc_core_tx_converter_sink_sink_payload_error;
wire          main_basesoc_core_tx_converter_sink_sink_ready;
wire          main_basesoc_core_tx_converter_sink_sink_valid;
wire          main_basesoc_core_tx_converter_source_source_first;
wire          main_basesoc_core_tx_converter_source_source_last;
wire          main_basesoc_core_tx_converter_source_source_payload_be;
wire    [7:0] main_basesoc_core_tx_converter_source_source_payload_data;
wire          main_basesoc_core_tx_converter_source_source_payload_error;
wire          main_basesoc_core_tx_converter_source_source_ready;
wire          main_basesoc_core_tx_converter_source_source_valid;
reg     [3:0] main_basesoc_core_tx_gap_counter = 4'd0;
reg     [3:0] main_basesoc_core_tx_gap_counter_clockdomainsrenamer3_next_value = 4'd0;
reg           main_basesoc_core_tx_gap_counter_clockdomainsrenamer3_next_value_ce = 1'd0;
wire          main_basesoc_core_tx_gap_reset;
wire          main_basesoc_core_tx_gap_sink_first;
wire          main_basesoc_core_tx_gap_sink_last;
wire          main_basesoc_core_tx_gap_sink_payload_be;
wire    [7:0] main_basesoc_core_tx_gap_sink_payload_data;
wire          main_basesoc_core_tx_gap_sink_payload_error;
reg           main_basesoc_core_tx_gap_sink_ready = 1'd0;
wire          main_basesoc_core_tx_gap_sink_valid;
reg           main_basesoc_core_tx_gap_source_first = 1'd0;
reg           main_basesoc_core_tx_gap_source_last = 1'd0;
reg           main_basesoc_core_tx_gap_source_payload_be = 1'd0;
reg     [7:0] main_basesoc_core_tx_gap_source_payload_data = 8'd0;
reg           main_basesoc_core_tx_gap_source_payload_error = 1'd0;
wire          main_basesoc_core_tx_gap_source_ready;
reg           main_basesoc_core_tx_gap_source_valid = 1'd0;
reg    [15:0] main_basesoc_core_tx_padding_counter = 16'd0;
reg    [15:0] main_basesoc_core_tx_padding_counter_clockdomainsrenamer0_next_value = 16'd0;
reg           main_basesoc_core_tx_padding_counter_clockdomainsrenamer0_next_value_ce = 1'd0;
wire          main_basesoc_core_tx_padding_counter_done;
wire          main_basesoc_core_tx_padding_reset;
wire          main_basesoc_core_tx_padding_sink_first;
wire          main_basesoc_core_tx_padding_sink_last;
wire          main_basesoc_core_tx_padding_sink_payload_be;
wire    [7:0] main_basesoc_core_tx_padding_sink_payload_data;
wire          main_basesoc_core_tx_padding_sink_payload_error;
reg           main_basesoc_core_tx_padding_sink_ready = 1'd0;
wire          main_basesoc_core_tx_padding_sink_valid;
reg           main_basesoc_core_tx_padding_source_first = 1'd0;
reg           main_basesoc_core_tx_padding_source_last = 1'd0;
reg           main_basesoc_core_tx_padding_source_payload_be = 1'd0;
reg     [7:0] main_basesoc_core_tx_padding_source_payload_data = 8'd0;
reg           main_basesoc_core_tx_padding_source_payload_error = 1'd0;
wire          main_basesoc_core_tx_padding_source_ready;
reg           main_basesoc_core_tx_padding_source_valid = 1'd0;
reg     [2:0] main_basesoc_core_tx_preamble_count = 3'd0;
reg     [2:0] main_basesoc_core_tx_preamble_count_clockdomainsrenamer2_next_value = 3'd0;
reg           main_basesoc_core_tx_preamble_count_clockdomainsrenamer2_next_value_ce = 1'd0;
reg    [63:0] main_basesoc_core_tx_preamble_preamble = 64'hd555555555555555;
wire          main_basesoc_core_tx_preamble_reset;
wire          main_basesoc_core_tx_preamble_sink_first;
wire          main_basesoc_core_tx_preamble_sink_last;
wire          main_basesoc_core_tx_preamble_sink_payload_be;
wire    [7:0] main_basesoc_core_tx_preamble_sink_payload_data;
wire          main_basesoc_core_tx_preamble_sink_payload_error;
reg           main_basesoc_core_tx_preamble_sink_ready = 1'd0;
wire          main_basesoc_core_tx_preamble_sink_valid;
reg           main_basesoc_core_tx_preamble_source_first = 1'd0;
reg           main_basesoc_core_tx_preamble_source_last = 1'd0;
reg           main_basesoc_core_tx_preamble_source_payload_be = 1'd0;
reg     [7:0] main_basesoc_core_tx_preamble_source_payload_data = 8'd0;
reg           main_basesoc_core_tx_preamble_source_payload_error = 1'd0;
wire          main_basesoc_core_tx_preamble_source_ready;
reg           main_basesoc_core_tx_preamble_source_valid = 1'd0;
wire          main_basesoc_core_txdatapath_reset;
reg           main_basesoc_core_wr_stb = 1'd0;
wire          main_basesoc_cpu_rst;
wire   [31:0] main_basesoc_dat_r;
wire          main_basesoc_dbus_ack;
wire   [29:0] main_basesoc_dbus_adr;
wire    [1:0] main_basesoc_dbus_bte;
wire    [2:0] main_basesoc_dbus_cti;
wire          main_basesoc_dbus_cyc;
wire   [31:0] main_basesoc_dbus_dat_r;
wire   [31:0] main_basesoc_dbus_dat_w;
wire          main_basesoc_dbus_err;
wire    [3:0] main_basesoc_dbus_sel;
wire          main_basesoc_dbus_stb;
wire          main_basesoc_dbus_we;
wire          main_basesoc_ibus_ack;
wire   [29:0] main_basesoc_ibus_adr;
wire    [1:0] main_basesoc_ibus_bte;
wire    [2:0] main_basesoc_ibus_cti;
wire          main_basesoc_ibus_cyc;
wire   [31:0] main_basesoc_ibus_dat_r;
wire   [31:0] main_basesoc_ibus_dat_w;
wire          main_basesoc_ibus_err;
wire    [3:0] main_basesoc_ibus_sel;
wire          main_basesoc_ibus_stb;
wire          main_basesoc_ibus_we;
reg           main_basesoc_interface0_ram_bus_ack = 1'd0;
wire   [29:0] main_basesoc_interface0_ram_bus_adr;
wire    [1:0] main_basesoc_interface0_ram_bus_bte;
wire    [2:0] main_basesoc_interface0_ram_bus_cti;
wire          main_basesoc_interface0_ram_bus_cyc;
wire   [31:0] main_basesoc_interface0_ram_bus_dat_r;
wire   [31:0] main_basesoc_interface0_ram_bus_dat_w;
reg           main_basesoc_interface0_ram_bus_err = 1'd0;
wire    [3:0] main_basesoc_interface0_ram_bus_sel;
wire          main_basesoc_interface0_ram_bus_stb;
wire          main_basesoc_interface0_ram_bus_we;
reg           main_basesoc_interface1_ram_bus_ack = 1'd0;
wire   [29:0] main_basesoc_interface1_ram_bus_adr;
wire    [1:0] main_basesoc_interface1_ram_bus_bte;
wire    [2:0] main_basesoc_interface1_ram_bus_cti;
wire          main_basesoc_interface1_ram_bus_cyc;
wire   [31:0] main_basesoc_interface1_ram_bus_dat_r;
wire   [31:0] main_basesoc_interface1_ram_bus_dat_w;
reg           main_basesoc_interface1_ram_bus_err = 1'd0;
wire    [3:0] main_basesoc_interface1_ram_bus_sel;
wire          main_basesoc_interface1_ram_bus_stb;
wire          main_basesoc_interface1_ram_bus_we;
reg    [31:0] main_basesoc_interrupt = 32'd0;
reg           main_basesoc_ram_bus_ack = 1'd0;
wire   [29:0] main_basesoc_ram_bus_adr;
wire    [1:0] main_basesoc_ram_bus_bte;
wire    [2:0] main_basesoc_ram_bus_cti;
wire          main_basesoc_ram_bus_cyc;
wire   [31:0] main_basesoc_ram_bus_dat_r;
wire   [31:0] main_basesoc_ram_bus_dat_w;
reg           main_basesoc_ram_bus_err = 1'd0;
wire    [3:0] main_basesoc_ram_bus_sel;
wire          main_basesoc_ram_bus_stb;
wire          main_basesoc_ram_bus_we;
wire          main_basesoc_reset;
reg     [1:0] main_basesoc_reset_storage = 2'd0;
reg           main_basesoc_reset_wr_stb = 1'd0;
reg    [31:0] main_basesoc_scratch_storage = 32'd305419896;
reg           main_basesoc_scratch_wr_stb = 1'd0;
reg           main_basesoc_serial_tx_rs232phytx_next_value1 = 1'd0;
reg           main_basesoc_serial_tx_rs232phytx_next_value_ce1 = 1'd0;
reg           main_basesoc_soc_rst = 1'd0;
wire   [10:0] main_basesoc_sram0_adr;
reg           main_basesoc_sram0_adr_burst = 1'd0;
wire   [31:0] main_basesoc_sram0_dat_r;
wire   [31:0] main_basesoc_sram0_dat_w;
reg     [3:0] main_basesoc_sram0_we = 4'd0;
wire   [13:0] main_basesoc_sram1_adr;
reg           main_basesoc_sram1_adr_burst = 1'd0;
wire   [31:0] main_basesoc_sram1_dat_r;
wire   [31:0] main_basesoc_sram1_dat_w;
reg     [3:0] main_basesoc_sram1_we = 4'd0;
reg           main_basesoc_timer_en_storage = 1'd0;
reg           main_basesoc_timer_en_wr_stb = 1'd0;
reg           main_basesoc_timer_enable_storage = 1'd0;
reg           main_basesoc_timer_enable_wr_stb = 1'd0;
wire          main_basesoc_timer_irq;
reg    [31:0] main_basesoc_timer_load_storage = 32'd0;
reg           main_basesoc_timer_load_wr_stb = 1'd0;
wire          main_basesoc_timer_pending_rd_stb;
wire          main_basesoc_timer_pending_status;
reg           main_basesoc_timer_pending_wr_data = 1'd0;
reg           main_basesoc_timer_pending_wr_stb = 1'd0;
reg    [31:0] main_basesoc_timer_reload_storage = 32'd0;
reg           main_basesoc_timer_reload_wr_stb = 1'd0;
wire          main_basesoc_timer_status_rd_stb;
wire          main_basesoc_timer_status_status;
reg           main_basesoc_timer_status_wr_stb = 1'd0;
reg           main_basesoc_timer_update_value_storage = 1'd0;
reg           main_basesoc_timer_update_value_wr_stb = 1'd0;
reg    [31:0] main_basesoc_timer_value = 32'd0;
wire          main_basesoc_timer_value_rd_stb;
reg    [31:0] main_basesoc_timer_value_status = 32'd0;
reg           main_basesoc_timer_value_wr_stb = 1'd0;
wire          main_basesoc_timer_zero0;
wire          main_basesoc_timer_zero1;
wire          main_basesoc_timer_zero2;
reg           main_basesoc_timer_zero_clear = 1'd0;
reg           main_basesoc_timer_zero_pending = 1'd0;
wire          main_basesoc_timer_zero_status;
wire          main_basesoc_timer_zero_trigger;
reg           main_basesoc_timer_zero_trigger_d = 1'd0;
reg     [1:0] main_basesoc_uart_core_enable_storage = 2'd0;
reg           main_basesoc_uart_core_enable_wr_stb = 1'd0;
wire          main_basesoc_uart_core_irq;
wire          main_basesoc_uart_core_pending_rd_stb;
reg     [1:0] main_basesoc_uart_core_pending_status = 2'd0;
reg     [1:0] main_basesoc_uart_core_pending_wr_data = 2'd0;
reg           main_basesoc_uart_core_pending_wr_stb = 1'd0;
wire          main_basesoc_uart_core_rx0;
wire          main_basesoc_uart_core_rx1;
wire          main_basesoc_uart_core_rx2;
reg           main_basesoc_uart_core_rx_clear = 1'd0;
reg     [3:0] main_basesoc_uart_core_rx_count = 4'd0;
reg     [3:0] main_basesoc_uart_core_rx_count_rs232phyrx_next_value0 = 4'd0;
reg           main_basesoc_uart_core_rx_count_rs232phyrx_next_value_ce0 = 1'd0;
reg     [7:0] main_basesoc_uart_core_rx_data = 8'd0;
reg     [7:0] main_basesoc_uart_core_rx_data_rs232phyrx_next_value1 = 8'd0;
reg           main_basesoc_uart_core_rx_data_rs232phyrx_next_value_ce1 = 1'd0;
reg           main_basesoc_uart_core_rx_enable = 1'd0;
reg     [3:0] main_basesoc_uart_core_rx_fifo_consume = 4'd0;
wire          main_basesoc_uart_core_rx_fifo_do_read;
wire          main_basesoc_uart_core_rx_fifo_fifo_in_first;
wire          main_basesoc_uart_core_rx_fifo_fifo_in_last;
wire    [7:0] main_basesoc_uart_core_rx_fifo_fifo_in_payload_data;
wire          main_basesoc_uart_core_rx_fifo_fifo_out_first;
wire          main_basesoc_uart_core_rx_fifo_fifo_out_last;
wire    [7:0] main_basesoc_uart_core_rx_fifo_fifo_out_payload_data;
reg     [4:0] main_basesoc_uart_core_rx_fifo_level0 = 5'd0;
wire    [4:0] main_basesoc_uart_core_rx_fifo_level1;
reg     [3:0] main_basesoc_uart_core_rx_fifo_produce = 4'd0;
wire    [3:0] main_basesoc_uart_core_rx_fifo_rdport_adr;
wire    [9:0] main_basesoc_uart_core_rx_fifo_rdport_dat_r;
wire          main_basesoc_uart_core_rx_fifo_rdport_re;
wire          main_basesoc_uart_core_rx_fifo_re;
reg           main_basesoc_uart_core_rx_fifo_readable = 1'd0;
reg           main_basesoc_uart_core_rx_fifo_replace = 1'd0;
wire          main_basesoc_uart_core_rx_fifo_sink_first;
wire          main_basesoc_uart_core_rx_fifo_sink_last;
wire    [7:0] main_basesoc_uart_core_rx_fifo_sink_payload_data;
wire          main_basesoc_uart_core_rx_fifo_sink_ready;
wire          main_basesoc_uart_core_rx_fifo_sink_valid;
wire          main_basesoc_uart_core_rx_fifo_source_first;
wire          main_basesoc_uart_core_rx_fifo_source_last;
wire    [7:0] main_basesoc_uart_core_rx_fifo_source_payload_data;
wire          main_basesoc_uart_core_rx_fifo_source_ready;
wire          main_basesoc_uart_core_rx_fifo_source_valid;
wire    [9:0] main_basesoc_uart_core_rx_fifo_syncfifo_din;
wire    [9:0] main_basesoc_uart_core_rx_fifo_syncfifo_dout;
wire          main_basesoc_uart_core_rx_fifo_syncfifo_re;
wire          main_basesoc_uart_core_rx_fifo_syncfifo_readable;
wire          main_basesoc_uart_core_rx_fifo_syncfifo_we;
wire          main_basesoc_uart_core_rx_fifo_syncfifo_writable;
reg     [3:0] main_basesoc_uart_core_rx_fifo_wrport_adr = 4'd0;
wire    [9:0] main_basesoc_uart_core_rx_fifo_wrport_dat_r;
wire    [9:0] main_basesoc_uart_core_rx_fifo_wrport_dat_w;
wire          main_basesoc_uart_core_rx_fifo_wrport_we;
reg           main_basesoc_uart_core_rx_framing_error = 1'd0;
reg           main_basesoc_uart_core_rx_overflow = 1'd0;
wire          main_basesoc_uart_core_rx_pending;
reg    [31:0] main_basesoc_uart_core_rx_phase = 32'd0;
wire          main_basesoc_uart_core_rx_rx;
reg           main_basesoc_uart_core_rx_rx_d = 1'd0;
reg           main_basesoc_uart_core_rx_source_first = 1'd0;
reg           main_basesoc_uart_core_rx_source_last = 1'd0;
reg     [7:0] main_basesoc_uart_core_rx_source_payload_data = 8'd0;
wire          main_basesoc_uart_core_rx_source_ready;
reg           main_basesoc_uart_core_rx_source_valid = 1'd0;
wire          main_basesoc_uart_core_rx_status;
reg           main_basesoc_uart_core_rx_tick = 1'd0;
wire          main_basesoc_uart_core_rx_trigger;
wire          main_basesoc_uart_core_rxempty_rd_stb;
wire          main_basesoc_uart_core_rxempty_status;
reg           main_basesoc_uart_core_rxempty_wr_stb = 1'd0;
wire          main_basesoc_uart_core_rxfull_rd_stb;
wire          main_basesoc_uart_core_rxfull_status;
reg           main_basesoc_uart_core_rxfull_wr_stb = 1'd0;
wire    [7:0] main_basesoc_uart_core_rxtx_r;
reg           main_basesoc_uart_core_rxtx_re = 1'd0;
wire    [7:0] main_basesoc_uart_core_rxtx_w;
reg           main_basesoc_uart_core_rxtx_we = 1'd0;
wire          main_basesoc_uart_core_status_rd_stb;
reg     [1:0] main_basesoc_uart_core_status_status = 2'd0;
reg           main_basesoc_uart_core_status_wr_stb = 1'd0;
wire          main_basesoc_uart_core_tx0;
wire          main_basesoc_uart_core_tx1;
wire          main_basesoc_uart_core_tx2;
reg           main_basesoc_uart_core_tx_clear = 1'd0;
reg     [3:0] main_basesoc_uart_core_tx_count = 4'd0;
reg     [3:0] main_basesoc_uart_core_tx_count_rs232phytx_next_value0 = 4'd0;
reg           main_basesoc_uart_core_tx_count_rs232phytx_next_value_ce0 = 1'd0;
reg     [7:0] main_basesoc_uart_core_tx_data = 8'd0;
reg     [7:0] main_basesoc_uart_core_tx_data_rs232phytx_next_value2 = 8'd0;
reg           main_basesoc_uart_core_tx_data_rs232phytx_next_value_ce2 = 1'd0;
reg           main_basesoc_uart_core_tx_enable = 1'd0;
reg     [3:0] main_basesoc_uart_core_tx_fifo_consume = 4'd0;
wire          main_basesoc_uart_core_tx_fifo_do_read;
wire          main_basesoc_uart_core_tx_fifo_fifo_in_first;
wire          main_basesoc_uart_core_tx_fifo_fifo_in_last;
wire    [7:0] main_basesoc_uart_core_tx_fifo_fifo_in_payload_data;
wire          main_basesoc_uart_core_tx_fifo_fifo_out_first;
wire          main_basesoc_uart_core_tx_fifo_fifo_out_last;
wire    [7:0] main_basesoc_uart_core_tx_fifo_fifo_out_payload_data;
reg     [4:0] main_basesoc_uart_core_tx_fifo_level0 = 5'd0;
wire    [4:0] main_basesoc_uart_core_tx_fifo_level1;
reg     [3:0] main_basesoc_uart_core_tx_fifo_produce = 4'd0;
wire    [3:0] main_basesoc_uart_core_tx_fifo_rdport_adr;
wire    [9:0] main_basesoc_uart_core_tx_fifo_rdport_dat_r;
wire          main_basesoc_uart_core_tx_fifo_rdport_re;
wire          main_basesoc_uart_core_tx_fifo_re;
reg           main_basesoc_uart_core_tx_fifo_readable = 1'd0;
reg           main_basesoc_uart_core_tx_fifo_replace = 1'd0;
reg           main_basesoc_uart_core_tx_fifo_sink_first = 1'd0;
reg           main_basesoc_uart_core_tx_fifo_sink_last = 1'd0;
wire    [7:0] main_basesoc_uart_core_tx_fifo_sink_payload_data;
wire          main_basesoc_uart_core_tx_fifo_sink_ready;
wire          main_basesoc_uart_core_tx_fifo_sink_valid;
wire          main_basesoc_uart_core_tx_fifo_source_first;
wire          main_basesoc_uart_core_tx_fifo_source_last;
wire    [7:0] main_basesoc_uart_core_tx_fifo_source_payload_data;
wire          main_basesoc_uart_core_tx_fifo_source_ready;
wire          main_basesoc_uart_core_tx_fifo_source_valid;
wire    [9:0] main_basesoc_uart_core_tx_fifo_syncfifo_din;
wire    [9:0] main_basesoc_uart_core_tx_fifo_syncfifo_dout;
wire          main_basesoc_uart_core_tx_fifo_syncfifo_re;
wire          main_basesoc_uart_core_tx_fifo_syncfifo_readable;
wire          main_basesoc_uart_core_tx_fifo_syncfifo_we;
wire          main_basesoc_uart_core_tx_fifo_syncfifo_writable;
reg     [3:0] main_basesoc_uart_core_tx_fifo_wrport_adr = 4'd0;
wire    [9:0] main_basesoc_uart_core_tx_fifo_wrport_dat_r;
wire    [9:0] main_basesoc_uart_core_tx_fifo_wrport_dat_w;
wire          main_basesoc_uart_core_tx_fifo_wrport_we;
wire          main_basesoc_uart_core_tx_pending;
reg    [31:0] main_basesoc_uart_core_tx_phase = 32'd0;
wire          main_basesoc_uart_core_tx_sink_first;
wire          main_basesoc_uart_core_tx_sink_last;
wire    [7:0] main_basesoc_uart_core_tx_sink_payload_data;
reg           main_basesoc_uart_core_tx_sink_ready = 1'd0;
wire          main_basesoc_uart_core_tx_sink_valid;
wire          main_basesoc_uart_core_tx_status;
reg           main_basesoc_uart_core_tx_tick = 1'd0;
wire          main_basesoc_uart_core_tx_trigger;
wire          main_basesoc_uart_core_txempty_rd_stb;
wire          main_basesoc_uart_core_txempty_status;
reg           main_basesoc_uart_core_txempty_wr_stb = 1'd0;
wire          main_basesoc_uart_core_txfull_rd_stb;
wire          main_basesoc_uart_core_txfull_status;
reg           main_basesoc_uart_core_txfull_wr_stb = 1'd0;
wire          main_basesoc_uart_core_uart_sink_first;
wire          main_basesoc_uart_core_uart_sink_last;
wire    [7:0] main_basesoc_uart_core_uart_sink_payload_data;
wire          main_basesoc_uart_core_uart_sink_ready;
wire          main_basesoc_uart_core_uart_sink_valid;
wire          main_basesoc_uart_core_uart_source_first;
wire          main_basesoc_uart_core_uart_source_last;
wire    [7:0] main_basesoc_uart_core_uart_source_payload_data;
wire          main_basesoc_uart_core_uart_source_ready;
wire          main_basesoc_uart_core_uart_source_valid;
reg    [31:0] main_basesoc_vexriscv = 32'd0;
wire          main_basesoc_wishbone_interface_bus_rx_ack;
wire   [29:0] main_basesoc_wishbone_interface_bus_rx_adr;
wire    [1:0] main_basesoc_wishbone_interface_bus_rx_bte;
wire    [2:0] main_basesoc_wishbone_interface_bus_rx_cti;
wire          main_basesoc_wishbone_interface_bus_rx_cyc;
wire   [31:0] main_basesoc_wishbone_interface_bus_rx_dat_r;
wire   [31:0] main_basesoc_wishbone_interface_bus_rx_dat_w;
wire          main_basesoc_wishbone_interface_bus_rx_err;
wire    [3:0] main_basesoc_wishbone_interface_bus_rx_sel;
wire          main_basesoc_wishbone_interface_bus_rx_stb;
wire          main_basesoc_wishbone_interface_bus_rx_we;
wire          main_basesoc_wishbone_interface_bus_tx_ack;
wire   [29:0] main_basesoc_wishbone_interface_bus_tx_adr;
wire    [1:0] main_basesoc_wishbone_interface_bus_tx_bte;
wire    [2:0] main_basesoc_wishbone_interface_bus_tx_cti;
wire          main_basesoc_wishbone_interface_bus_tx_cyc;
wire   [31:0] main_basesoc_wishbone_interface_bus_tx_dat_r;
wire   [31:0] main_basesoc_wishbone_interface_bus_tx_dat_w;
wire          main_basesoc_wishbone_interface_bus_tx_err;
wire    [3:0] main_basesoc_wishbone_interface_bus_tx_sel;
wire          main_basesoc_wishbone_interface_bus_tx_stb;
wire          main_basesoc_wishbone_interface_bus_tx_we;
reg     [1:0] main_basesoc_wishbone_interface_decoder0_slave_sel = 2'd0;
reg     [1:0] main_basesoc_wishbone_interface_decoder0_slave_sel_r = 2'd0;
reg     [1:0] main_basesoc_wishbone_interface_decoder1_slave_sel = 2'd0;
reg     [1:0] main_basesoc_wishbone_interface_decoder1_slave_sel_r = 2'd0;
wire          main_basesoc_wishbone_interface_ev_irq;
reg           main_basesoc_wishbone_interface_interface0_ack = 1'd0;
wire   [29:0] main_basesoc_wishbone_interface_interface0_adr;
wire    [1:0] main_basesoc_wishbone_interface_interface0_bte;
wire    [2:0] main_basesoc_wishbone_interface_interface0_cti;
wire          main_basesoc_wishbone_interface_interface0_cyc;
wire   [31:0] main_basesoc_wishbone_interface_interface0_dat_r;
wire   [31:0] main_basesoc_wishbone_interface_interface0_dat_w;
reg           main_basesoc_wishbone_interface_interface0_err = 1'd0;
wire    [3:0] main_basesoc_wishbone_interface_interface0_sel;
wire          main_basesoc_wishbone_interface_interface0_stb;
wire          main_basesoc_wishbone_interface_interface0_we;
reg           main_basesoc_wishbone_interface_interface1_ack = 1'd0;
wire   [29:0] main_basesoc_wishbone_interface_interface1_adr;
wire    [1:0] main_basesoc_wishbone_interface_interface1_bte;
wire    [2:0] main_basesoc_wishbone_interface_interface1_cti;
wire          main_basesoc_wishbone_interface_interface1_cyc;
wire   [31:0] main_basesoc_wishbone_interface_interface1_dat_r;
wire   [31:0] main_basesoc_wishbone_interface_interface1_dat_w;
reg           main_basesoc_wishbone_interface_interface1_err = 1'd0;
wire    [3:0] main_basesoc_wishbone_interface_interface1_sel;
wire          main_basesoc_wishbone_interface_interface1_stb;
wire          main_basesoc_wishbone_interface_interface1_we;
reg           main_basesoc_wishbone_interface_interface2_ack = 1'd0;
wire   [29:0] main_basesoc_wishbone_interface_interface2_adr;
wire    [1:0] main_basesoc_wishbone_interface_interface2_bte;
wire    [2:0] main_basesoc_wishbone_interface_interface2_cti;
wire          main_basesoc_wishbone_interface_interface2_cyc;
wire   [31:0] main_basesoc_wishbone_interface_interface2_dat_r;
wire   [31:0] main_basesoc_wishbone_interface_interface2_dat_w;
reg           main_basesoc_wishbone_interface_interface2_err = 1'd0;
wire    [3:0] main_basesoc_wishbone_interface_interface2_sel;
wire          main_basesoc_wishbone_interface_interface2_stb;
wire          main_basesoc_wishbone_interface_interface2_we;
reg           main_basesoc_wishbone_interface_interface3_ack = 1'd0;
wire   [29:0] main_basesoc_wishbone_interface_interface3_adr;
wire    [1:0] main_basesoc_wishbone_interface_interface3_bte;
wire    [2:0] main_basesoc_wishbone_interface_interface3_cti;
wire          main_basesoc_wishbone_interface_interface3_cyc;
wire   [31:0] main_basesoc_wishbone_interface_interface3_dat_r;
wire   [31:0] main_basesoc_wishbone_interface_interface3_dat_w;
reg           main_basesoc_wishbone_interface_interface3_err = 1'd0;
wire    [3:0] main_basesoc_wishbone_interface_interface3_sel;
wire          main_basesoc_wishbone_interface_interface3_stb;
wire          main_basesoc_wishbone_interface_interface3_we;
reg           main_basesoc_wishbone_interface_reader_cmd_fifo_consume = 1'd0;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_do_read;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_in_first;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_in_last;
wire   [10:0] main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_in_payload_length;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_in_payload_slot;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_out_first;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_out_last;
wire   [10:0] main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_out_payload_length;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_out_payload_slot;
reg     [1:0] main_basesoc_wishbone_interface_reader_cmd_fifo_level = 2'd0;
reg           main_basesoc_wishbone_interface_reader_cmd_fifo_produce = 1'd0;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_rdport_adr;
wire   [13:0] main_basesoc_wishbone_interface_reader_cmd_fifo_rdport_dat_r;
reg           main_basesoc_wishbone_interface_reader_cmd_fifo_replace = 1'd0;
reg           main_basesoc_wishbone_interface_reader_cmd_fifo_sink_first = 1'd0;
reg           main_basesoc_wishbone_interface_reader_cmd_fifo_sink_last = 1'd0;
wire   [10:0] main_basesoc_wishbone_interface_reader_cmd_fifo_sink_payload_length;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_sink_payload_slot;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_sink_ready;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_sink_valid;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_source_first;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_source_last;
wire   [10:0] main_basesoc_wishbone_interface_reader_cmd_fifo_source_payload_length;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_source_payload_slot;
reg           main_basesoc_wishbone_interface_reader_cmd_fifo_source_ready = 1'd0;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_source_valid;
wire   [13:0] main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_din;
wire   [13:0] main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_dout;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_re;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_readable;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_we;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_writable;
reg           main_basesoc_wishbone_interface_reader_cmd_fifo_wrport_adr = 1'd0;
wire   [13:0] main_basesoc_wishbone_interface_reader_cmd_fifo_wrport_dat_r;
wire   [13:0] main_basesoc_wishbone_interface_reader_cmd_fifo_wrport_dat_w;
wire          main_basesoc_wishbone_interface_reader_cmd_fifo_wrport_we;
reg           main_basesoc_wishbone_interface_reader_enable_storage = 1'd0;
reg           main_basesoc_wishbone_interface_reader_enable_wr_stb = 1'd0;
wire          main_basesoc_wishbone_interface_reader_event00;
wire          main_basesoc_wishbone_interface_reader_event01;
wire          main_basesoc_wishbone_interface_reader_event02;
reg           main_basesoc_wishbone_interface_reader_eventsourcepulse_clear = 1'd0;
reg           main_basesoc_wishbone_interface_reader_eventsourcepulse_pending = 1'd0;
wire          main_basesoc_wishbone_interface_reader_eventsourcepulse_status;
wire          main_basesoc_wishbone_interface_reader_eventsourcepulse_trigger;
reg           main_basesoc_wishbone_interface_reader_fsm_is_ongoing0 = 1'd0;
reg           main_basesoc_wishbone_interface_reader_fsm_is_ongoing1 = 1'd0;
wire          main_basesoc_wishbone_interface_reader_irq;
reg    [10:0] main_basesoc_wishbone_interface_reader_length_storage = 11'd0;
reg           main_basesoc_wishbone_interface_reader_length_wr_stb = 1'd0;
wire          main_basesoc_wishbone_interface_reader_level_rd_stb;
wire    [1:0] main_basesoc_wishbone_interface_reader_level_status;
reg           main_basesoc_wishbone_interface_reader_level_wr_stb = 1'd0;
wire    [8:0] main_basesoc_wishbone_interface_reader_memory0_adr;
wire   [31:0] main_basesoc_wishbone_interface_reader_memory0_dat_r;
wire          main_basesoc_wishbone_interface_reader_memory0_re;
wire    [8:0] main_basesoc_wishbone_interface_reader_memory1_adr;
wire   [31:0] main_basesoc_wishbone_interface_reader_memory1_dat_r;
wire          main_basesoc_wishbone_interface_reader_memory1_re;
wire          main_basesoc_wishbone_interface_reader_packet_direct_read;
reg           main_basesoc_wishbone_interface_reader_packet_done = 1'd0;
wire          main_basesoc_wishbone_interface_reader_packet_enable;
wire          main_basesoc_wishbone_interface_reader_packet_idle;
reg           main_basesoc_wishbone_interface_reader_packet_is_ongoing0 = 1'd0;
reg           main_basesoc_wishbone_interface_reader_packet_is_ongoing1 = 1'd0;
wire   [10:0] main_basesoc_wishbone_interface_reader_packet_length;
wire          main_basesoc_wishbone_interface_reader_packet_sink_last;
wire   [31:0] main_basesoc_wishbone_interface_reader_packet_sink_payload_data;
wire          main_basesoc_wishbone_interface_reader_packet_sink_ready;
wire          main_basesoc_wishbone_interface_reader_packet_sink_valid;
reg           main_basesoc_wishbone_interface_reader_packet_source_first = 1'd0;
wire          main_basesoc_wishbone_interface_reader_packet_source_last;
wire    [3:0] main_basesoc_wishbone_interface_reader_packet_source_payload_be;
wire   [31:0] main_basesoc_wishbone_interface_reader_packet_source_payload_data;
wire    [3:0] main_basesoc_wishbone_interface_reader_packet_source_payload_error;
wire          main_basesoc_wishbone_interface_reader_packet_source_ready;
wire          main_basesoc_wishbone_interface_reader_packet_source_valid;
wire          main_basesoc_wishbone_interface_reader_pending_rd_stb;
wire          main_basesoc_wishbone_interface_reader_pending_status;
reg           main_basesoc_wishbone_interface_reader_pending_wr_data = 1'd0;
reg           main_basesoc_wishbone_interface_reader_pending_wr_stb = 1'd0;
reg    [31:0] main_basesoc_wishbone_interface_reader_rd_data = 32'd0;
reg    [10:0] main_basesoc_wishbone_interface_reader_rd_offset = 11'd0;
reg    [10:0] main_basesoc_wishbone_interface_reader_rd_offset_liteethmacsramreader_next_value = 11'd0;
reg           main_basesoc_wishbone_interface_reader_rd_offset_liteethmacsramreader_next_value_ce = 1'd0;
reg           main_basesoc_wishbone_interface_reader_read = 1'd0;
wire          main_basesoc_wishbone_interface_reader_ready_rd_stb;
wire          main_basesoc_wishbone_interface_reader_ready_status;
reg           main_basesoc_wishbone_interface_reader_ready_wr_stb = 1'd0;
reg           main_basesoc_wishbone_interface_reader_slot_storage = 1'd0;
reg           main_basesoc_wishbone_interface_reader_slot_wr_stb = 1'd0;
wire          main_basesoc_wishbone_interface_reader_start_r;
reg           main_basesoc_wishbone_interface_reader_start_re = 1'd0;
reg           main_basesoc_wishbone_interface_reader_start_w = 1'd0;
reg           main_basesoc_wishbone_interface_reader_start_we = 1'd0;
wire          main_basesoc_wishbone_interface_reader_status_rd_stb;
wire          main_basesoc_wishbone_interface_reader_status_status;
reg           main_basesoc_wishbone_interface_reader_status_wr_stb = 1'd0;
wire          main_basesoc_wishbone_interface_reader_valid_command;
wire          main_basesoc_wishbone_interface_sink_first;
wire          main_basesoc_wishbone_interface_sink_last;
wire    [3:0] main_basesoc_wishbone_interface_sink_payload_be;
wire   [31:0] main_basesoc_wishbone_interface_sink_payload_data;
wire    [3:0] main_basesoc_wishbone_interface_sink_payload_error;
wire          main_basesoc_wishbone_interface_sink_ready;
wire          main_basesoc_wishbone_interface_sink_valid;
wire          main_basesoc_wishbone_interface_source_first;
wire          main_basesoc_wishbone_interface_source_last;
wire    [3:0] main_basesoc_wishbone_interface_source_payload_be;
wire   [31:0] main_basesoc_wishbone_interface_source_payload_data;
wire    [3:0] main_basesoc_wishbone_interface_source_payload_error;
wire          main_basesoc_wishbone_interface_source_ready;
wire          main_basesoc_wishbone_interface_source_valid;
wire    [8:0] main_basesoc_wishbone_interface_sram0_adr;
reg           main_basesoc_wishbone_interface_sram0_adr_burst = 1'd0;
wire   [31:0] main_basesoc_wishbone_interface_sram0_dat_r;
wire    [8:0] main_basesoc_wishbone_interface_sram1_adr;
reg           main_basesoc_wishbone_interface_sram1_adr_burst = 1'd0;
wire   [31:0] main_basesoc_wishbone_interface_sram1_dat_r;
wire    [8:0] main_basesoc_wishbone_interface_sram2_adr;
reg           main_basesoc_wishbone_interface_sram2_adr_burst = 1'd0;
wire   [31:0] main_basesoc_wishbone_interface_sram2_dat_r;
wire   [31:0] main_basesoc_wishbone_interface_sram2_dat_w;
reg     [3:0] main_basesoc_wishbone_interface_sram2_we = 4'd0;
wire    [8:0] main_basesoc_wishbone_interface_sram3_adr;
reg           main_basesoc_wishbone_interface_sram3_adr_burst = 1'd0;
wire   [31:0] main_basesoc_wishbone_interface_sram3_dat_r;
wire   [31:0] main_basesoc_wishbone_interface_sram3_dat_w;
reg     [3:0] main_basesoc_wishbone_interface_sram3_we = 4'd0;
wire          main_basesoc_wishbone_interface_writer_available0;
wire          main_basesoc_wishbone_interface_writer_available1;
wire          main_basesoc_wishbone_interface_writer_available2;
reg           main_basesoc_wishbone_interface_writer_available_clear = 1'd0;
wire          main_basesoc_wishbone_interface_writer_available_pending;
wire          main_basesoc_wishbone_interface_writer_available_status;
wire          main_basesoc_wishbone_interface_writer_available_trigger;
reg           main_basesoc_wishbone_interface_writer_enable_storage = 1'd0;
reg           main_basesoc_wishbone_interface_writer_enable_wr_stb = 1'd0;
wire          main_basesoc_wishbone_interface_writer_errors_rd_stb;
reg    [31:0] main_basesoc_wishbone_interface_writer_errors_status = 32'd0;
reg           main_basesoc_wishbone_interface_writer_errors_wr_stb = 1'd0;
wire          main_basesoc_wishbone_interface_writer_irq;
wire          main_basesoc_wishbone_interface_writer_length_rd_stb;
wire   [10:0] main_basesoc_wishbone_interface_writer_length_status;
reg           main_basesoc_wishbone_interface_writer_length_wr_stb = 1'd0;
wire    [8:0] main_basesoc_wishbone_interface_writer_memory0_adr;
wire   [31:0] main_basesoc_wishbone_interface_writer_memory0_dat_r;
wire   [31:0] main_basesoc_wishbone_interface_writer_memory0_dat_w;
reg           main_basesoc_wishbone_interface_writer_memory0_we = 1'd0;
wire    [8:0] main_basesoc_wishbone_interface_writer_memory1_adr;
wire   [31:0] main_basesoc_wishbone_interface_writer_memory1_dat_r;
wire   [31:0] main_basesoc_wishbone_interface_writer_memory1_dat_w;
reg           main_basesoc_wishbone_interface_writer_memory1_we = 1'd0;
reg           main_basesoc_wishbone_interface_writer_packet_done = 1'd0;
reg           main_basesoc_wishbone_interface_writer_packet_drop = 1'd0;
wire          main_basesoc_wishbone_interface_writer_packet_enable;
reg           main_basesoc_wishbone_interface_writer_packet_error0 = 1'd0;
reg           main_basesoc_wishbone_interface_writer_packet_error1 = 1'd0;
reg           main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value2 = 1'd0;
reg           main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value_ce2 = 1'd0;
wire          main_basesoc_wishbone_interface_writer_packet_last_error;
wire   [10:0] main_basesoc_wishbone_interface_writer_packet_length0;
reg    [10:0] main_basesoc_wishbone_interface_writer_packet_length1 = 11'd0;
reg    [10:0] main_basesoc_wishbone_interface_writer_packet_length1_liteethmacsramwriter_next_value0 = 11'd0;
reg           main_basesoc_wishbone_interface_writer_packet_length1_liteethmacsramwriter_next_value_ce0 = 1'd0;
wire    [3:0] main_basesoc_wishbone_interface_writer_packet_length_inc;
wire   [11:0] main_basesoc_wishbone_interface_writer_packet_next_length;
wire   [10:0] main_basesoc_wishbone_interface_writer_packet_offset;
wire          main_basesoc_wishbone_interface_writer_packet_oversized;
reg    [10:0] main_basesoc_wishbone_interface_writer_packet_pkt_len = 11'd0;
reg    [10:0] main_basesoc_wishbone_interface_writer_packet_pkt_len_liteethmacsramwriter_next_value1 = 11'd0;
reg           main_basesoc_wishbone_interface_writer_packet_pkt_len_liteethmacsramwriter_next_value_ce1 = 1'd0;
wire          main_basesoc_wishbone_interface_writer_packet_sink_first;
wire          main_basesoc_wishbone_interface_writer_packet_sink_last;
wire    [3:0] main_basesoc_wishbone_interface_writer_packet_sink_payload_be;
wire   [31:0] main_basesoc_wishbone_interface_writer_packet_sink_payload_data;
wire    [3:0] main_basesoc_wishbone_interface_writer_packet_sink_payload_error;
reg           main_basesoc_wishbone_interface_writer_packet_sink_ready = 1'd0;
wire          main_basesoc_wishbone_interface_writer_packet_sink_valid;
reg           main_basesoc_wishbone_interface_writer_packet_source_last = 1'd0;
reg    [31:0] main_basesoc_wishbone_interface_writer_packet_source_payload_data = 32'd0;
wire          main_basesoc_wishbone_interface_writer_packet_source_ready;
reg           main_basesoc_wishbone_interface_writer_packet_source_valid = 1'd0;
wire          main_basesoc_wishbone_interface_writer_pending_rd_stb;
wire          main_basesoc_wishbone_interface_writer_pending_status;
reg           main_basesoc_wishbone_interface_writer_pending_wr_data = 1'd0;
reg           main_basesoc_wishbone_interface_writer_pending_wr_stb = 1'd0;
reg           main_basesoc_wishbone_interface_writer_slot = 1'd0;
wire          main_basesoc_wishbone_interface_writer_slot_rd_stb;
wire          main_basesoc_wishbone_interface_writer_slot_status;
reg           main_basesoc_wishbone_interface_writer_slot_wr_stb = 1'd0;
reg           main_basesoc_wishbone_interface_writer_stat_fifo_consume = 1'd0;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_do_read;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_fifo_in_first;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_fifo_in_last;
wire   [10:0] main_basesoc_wishbone_interface_writer_stat_fifo_fifo_in_payload_length;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_fifo_in_payload_slot;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_fifo_out_first;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_fifo_out_last;
wire   [10:0] main_basesoc_wishbone_interface_writer_stat_fifo_fifo_out_payload_length;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_fifo_out_payload_slot;
reg     [1:0] main_basesoc_wishbone_interface_writer_stat_fifo_level = 2'd0;
reg           main_basesoc_wishbone_interface_writer_stat_fifo_produce = 1'd0;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_rdport_adr;
wire   [13:0] main_basesoc_wishbone_interface_writer_stat_fifo_rdport_dat_r;
reg           main_basesoc_wishbone_interface_writer_stat_fifo_replace = 1'd0;
reg           main_basesoc_wishbone_interface_writer_stat_fifo_sink_first = 1'd0;
reg           main_basesoc_wishbone_interface_writer_stat_fifo_sink_last = 1'd0;
wire   [10:0] main_basesoc_wishbone_interface_writer_stat_fifo_sink_payload_length;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_sink_payload_slot;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_sink_ready;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_sink_valid;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_source_first;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_source_last;
wire   [10:0] main_basesoc_wishbone_interface_writer_stat_fifo_source_payload_length;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_source_payload_slot;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_source_ready;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_source_valid;
wire   [13:0] main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_din;
wire   [13:0] main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_dout;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_re;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_readable;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_we;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_writable;
reg           main_basesoc_wishbone_interface_writer_stat_fifo_wrport_adr = 1'd0;
wire   [13:0] main_basesoc_wishbone_interface_writer_stat_fifo_wrport_dat_r;
wire   [13:0] main_basesoc_wishbone_interface_writer_stat_fifo_wrport_dat_w;
wire          main_basesoc_wishbone_interface_writer_stat_fifo_wrport_we;
wire          main_basesoc_wishbone_interface_writer_status_rd_stb;
wire          main_basesoc_wishbone_interface_writer_status_status;
reg           main_basesoc_wishbone_interface_writer_status_wr_stb = 1'd0;
wire   [31:0] main_basesoc_wishbone_interface_writer_wr_data;
reg     [7:0] main_chaser = 8'd0;
reg    [22:0] main_count = 23'd6250000;
(* dont_touch = "true" *)
wire          main_crg_clkin_signal;
wire          main_crg_clkout0;
wire          main_crg_clkout1;
wire          main_crg_clkout2;
wire          main_crg_clkout3;
wire          main_crg_clkout4;
wire          main_crg_clkout_buf0;
wire          main_crg_clkout_buf1;
wire          main_crg_clkout_buf2;
wire          main_crg_clkout_buf3;
wire          main_crg_clkout_buf4;
reg           main_crg_ic_reset = 1'd1;
wire          main_crg_locked;
reg           main_crg_power_down = 1'd0;
wire          main_crg_reset;
reg     [3:0] main_crg_reset_counter = 4'd15;
reg           main_crg_rst = 1'd0;
wire          main_done;
wire          main_ethphy__r_rd_stb;
wire          main_ethphy__r_status;
reg           main_ethphy__r_wr_stb = 1'd0;
reg     [2:0] main_ethphy__w_storage = 3'd0;
reg           main_ethphy__w_wr_stb = 1'd0;
wire          main_ethphy_clkin_signal;
wire          main_ethphy_clkout0;
wire          main_ethphy_clkout1;
wire          main_ethphy_clkout_buf0;
wire          main_ethphy_clkout_buf1;
wire          main_ethphy_data_oe;
wire          main_ethphy_data_r;
wire          main_ethphy_data_w;
wire          main_ethphy_eth_rx_clk_ibuf;
wire          main_ethphy_eth_tx_clk_obuf;
reg     [8:0] main_ethphy_hw_reset_counter = 9'd0;
wire          main_ethphy_hw_reset_counter_ce;
wire          main_ethphy_hw_reset_counter_done;
wire          main_ethphy_hw_reset_reset;
wire          main_ethphy_last;
wire          main_ethphy_mdc;
wire          main_ethphy_oe;
wire          main_ethphy_pll_locked;
reg           main_ethphy_pll_power_down = 1'd0;
reg           main_ethphy_pll_reset = 1'd0;
wire          main_ethphy_r;
wire          main_ethphy_reset;
reg           main_ethphy_reset_storage = 1'd0;
reg           main_ethphy_reset_wr_stb = 1'd0;
wire    [1:0] main_ethphy_rx_ctl;
reg           main_ethphy_rx_ctl_d = 1'd0;
wire          main_ethphy_rx_ctl_ibuf;
wire          main_ethphy_rx_ctl_idelay;
wire    [7:0] main_ethphy_rx_data;
wire    [3:0] main_ethphy_rx_data_ibuf;
wire    [3:0] main_ethphy_rx_data_idelay;
wire          main_ethphy_sink_first;
wire          main_ethphy_sink_last;
wire          main_ethphy_sink_payload_be;
wire    [7:0] main_ethphy_sink_payload_data;
wire          main_ethphy_sink_payload_error;
wire          main_ethphy_sink_ready;
wire          main_ethphy_sink_valid;
reg           main_ethphy_source_first = 1'd0;
wire          main_ethphy_source_last;
wire          main_ethphy_source_payload_be;
reg     [7:0] main_ethphy_source_payload_data = 8'd0;
reg           main_ethphy_source_payload_error = 1'd0;
wire          main_ethphy_source_ready;
reg           main_ethphy_source_valid = 1'd0;
wire          main_ethphy_tx_ctl_obuf;
wire    [3:0] main_ethphy_tx_data_obuf;
wire          main_ethphy_w;
reg     [7:0] main_leds = 8'd0;
reg           main_mode = 1'd0;
reg     [7:0] main_storage = 8'd0;
wire          main_wait;
reg           main_wr_stb = 1'd0;
wire          sys4x_clk;
wire          sys4x_dqs_clk;
wire          sys4x_dqs_rst;
wire          sys4x_rst;
(* dont_touch = "true" *)
wire          sys_clk;
wire          sys_rst;


assign main_basesoc_reset = (main_basesoc_soc_rst | main_basesoc_cpu_rst);
always @(*) begin
    main_crg_rst = 1'd0;
    if (main_basesoc_soc_rst) begin
        main_crg_rst = 1'd1;
    end
end
assign main_basesoc_bus_error = builder_error;
always @(*) begin
    main_basesoc_interrupt = 32'd0;
    main_basesoc_interrupt[2] = main_basesoc_wishbone_interface_ev_irq;
    main_basesoc_interrupt[1] = main_basesoc_timer_irq;
    main_basesoc_interrupt[0] = main_basesoc_uart_core_irq;
end
assign main_crg_reset = ((~cpu_reset_n) | main_crg_rst);
assign main_crg_clkin_signal = clk100;
assign sys_clk = main_crg_clkout_buf0;
assign sys4x_clk = main_crg_clkout_buf1;
assign sys4x_dqs_clk = main_crg_clkout_buf2;
assign idelay_clk = main_crg_clkout_buf3;
assign clk100_clk = main_crg_clkout_buf4;
assign builder_shared_adr = builder_rhs_self0;
assign builder_shared_dat_w = builder_rhs_self1;
assign builder_shared_sel = builder_rhs_self2;
assign builder_shared_cyc = builder_rhs_self3;
assign builder_shared_stb = builder_rhs_self4;
assign builder_shared_we = builder_rhs_self5;
assign builder_shared_cti = builder_rhs_self6;
assign builder_shared_bte = builder_rhs_self7;
assign main_basesoc_ibus_dat_r = builder_shared_dat_r;
assign main_basesoc_dbus_dat_r = builder_shared_dat_r;
assign main_basesoc_ibus_ack = (builder_shared_ack & (builder_grant == 1'd0));
assign main_basesoc_dbus_ack = (builder_shared_ack & (builder_grant == 1'd1));
assign main_basesoc_ibus_err = (builder_shared_err & (builder_grant == 1'd0));
assign main_basesoc_dbus_err = (builder_shared_err & (builder_grant == 1'd1));
assign builder_request = {main_basesoc_dbus_cyc, main_basesoc_ibus_cyc};
always @(*) begin
    builder_slave_sel = 6'd0;
    builder_slave_sel[0] = (builder_shared_adr[29:15] == 1'd0);
    builder_slave_sel[1] = (builder_shared_adr[29:11] == 16'h8000);
    builder_slave_sel[2] = (builder_shared_adr[29:14] == 15'h4000);
    builder_slave_sel[3] = (builder_shared_adr[29:10] == 20'h80000);
    builder_slave_sel[4] = (builder_shared_adr[29:10] == 20'h80001);
    builder_slave_sel[5] = (builder_shared_adr[29:14] == 16'hf000);
end
assign main_basesoc_ram_bus_adr = builder_shared_adr;
assign main_basesoc_ram_bus_dat_w = builder_shared_dat_w;
assign main_basesoc_ram_bus_sel = builder_shared_sel;
assign main_basesoc_ram_bus_stb = builder_shared_stb;
assign main_basesoc_ram_bus_we = builder_shared_we;
assign main_basesoc_ram_bus_cti = builder_shared_cti;
assign main_basesoc_ram_bus_bte = builder_shared_bte;
assign main_basesoc_interface0_ram_bus_adr = builder_shared_adr;
assign main_basesoc_interface0_ram_bus_dat_w = builder_shared_dat_w;
assign main_basesoc_interface0_ram_bus_sel = builder_shared_sel;
assign main_basesoc_interface0_ram_bus_stb = builder_shared_stb;
assign main_basesoc_interface0_ram_bus_we = builder_shared_we;
assign main_basesoc_interface0_ram_bus_cti = builder_shared_cti;
assign main_basesoc_interface0_ram_bus_bte = builder_shared_bte;
assign main_basesoc_interface1_ram_bus_adr = builder_shared_adr;
assign main_basesoc_interface1_ram_bus_dat_w = builder_shared_dat_w;
assign main_basesoc_interface1_ram_bus_sel = builder_shared_sel;
assign main_basesoc_interface1_ram_bus_stb = builder_shared_stb;
assign main_basesoc_interface1_ram_bus_we = builder_shared_we;
assign main_basesoc_interface1_ram_bus_cti = builder_shared_cti;
assign main_basesoc_interface1_ram_bus_bte = builder_shared_bte;
assign main_basesoc_wishbone_interface_bus_rx_adr = builder_shared_adr;
assign main_basesoc_wishbone_interface_bus_rx_dat_w = builder_shared_dat_w;
assign main_basesoc_wishbone_interface_bus_rx_sel = builder_shared_sel;
assign main_basesoc_wishbone_interface_bus_rx_stb = builder_shared_stb;
assign main_basesoc_wishbone_interface_bus_rx_we = builder_shared_we;
assign main_basesoc_wishbone_interface_bus_rx_cti = builder_shared_cti;
assign main_basesoc_wishbone_interface_bus_rx_bte = builder_shared_bte;
assign main_basesoc_wishbone_interface_bus_tx_adr = builder_shared_adr;
assign main_basesoc_wishbone_interface_bus_tx_dat_w = builder_shared_dat_w;
assign main_basesoc_wishbone_interface_bus_tx_sel = builder_shared_sel;
assign main_basesoc_wishbone_interface_bus_tx_stb = builder_shared_stb;
assign main_basesoc_wishbone_interface_bus_tx_we = builder_shared_we;
assign main_basesoc_wishbone_interface_bus_tx_cti = builder_shared_cti;
assign main_basesoc_wishbone_interface_bus_tx_bte = builder_shared_bte;
assign builder_interface0_adr = builder_shared_adr;
assign builder_interface0_dat_w = builder_shared_dat_w;
assign builder_interface0_sel = builder_shared_sel;
assign builder_interface0_stb = builder_shared_stb;
assign builder_interface0_we = builder_shared_we;
assign builder_interface0_cti = builder_shared_cti;
assign builder_interface0_bte = builder_shared_bte;
assign main_basesoc_ram_bus_cyc = (builder_shared_cyc & builder_slave_sel[0]);
assign main_basesoc_interface0_ram_bus_cyc = (builder_shared_cyc & builder_slave_sel[1]);
assign main_basesoc_interface1_ram_bus_cyc = (builder_shared_cyc & builder_slave_sel[2]);
assign main_basesoc_wishbone_interface_bus_rx_cyc = (builder_shared_cyc & builder_slave_sel[3]);
assign main_basesoc_wishbone_interface_bus_tx_cyc = (builder_shared_cyc & builder_slave_sel[4]);
assign builder_interface0_cyc = (builder_shared_cyc & builder_slave_sel[5]);
assign builder_shared_err = (((((main_basesoc_ram_bus_err | main_basesoc_interface0_ram_bus_err) | main_basesoc_interface1_ram_bus_err) | main_basesoc_wishbone_interface_bus_rx_err) | main_basesoc_wishbone_interface_bus_tx_err) | builder_interface0_err);
assign builder_wait = ((builder_shared_stb & builder_shared_cyc) & (~builder_shared_ack));
always @(*) begin
    builder_error = 1'd0;
    builder_shared_ack = 1'd0;
    builder_shared_dat_r = 32'd0;
    builder_shared_ack = (((((main_basesoc_ram_bus_ack | main_basesoc_interface0_ram_bus_ack) | main_basesoc_interface1_ram_bus_ack) | main_basesoc_wishbone_interface_bus_rx_ack) | main_basesoc_wishbone_interface_bus_tx_ack) | builder_interface0_ack);
    builder_shared_dat_r = (((((({32{builder_slave_sel_r[0]}} & main_basesoc_ram_bus_dat_r) | ({32{builder_slave_sel_r[1]}} & main_basesoc_interface0_ram_bus_dat_r)) | ({32{builder_slave_sel_r[2]}} & main_basesoc_interface1_ram_bus_dat_r)) | ({32{builder_slave_sel_r[3]}} & main_basesoc_wishbone_interface_bus_rx_dat_r)) | ({32{builder_slave_sel_r[4]}} & main_basesoc_wishbone_interface_bus_tx_dat_r)) | ({32{builder_slave_sel_r[5]}} & builder_interface0_dat_r));
    if (builder_done) begin
        builder_shared_dat_r = 32'hffffffff;
        builder_shared_ack = 1'd1;
        builder_error = 1'd1;
    end
end
assign builder_done = (builder_count == 1'd0);
assign main_basesoc_bus_errors_status = main_basesoc_bus_errors;
assign main_basesoc_adr = main_basesoc_ram_bus_adr[14:0];
assign main_basesoc_ram_bus_dat_r = main_basesoc_dat_r;
always @(*) begin
    main_basesoc_sram0_we = 4'd0;
    main_basesoc_sram0_we[0] = (((main_basesoc_interface0_ram_bus_cyc & main_basesoc_interface0_ram_bus_stb) & main_basesoc_interface0_ram_bus_we) & main_basesoc_interface0_ram_bus_sel[0]);
    main_basesoc_sram0_we[1] = (((main_basesoc_interface0_ram_bus_cyc & main_basesoc_interface0_ram_bus_stb) & main_basesoc_interface0_ram_bus_we) & main_basesoc_interface0_ram_bus_sel[1]);
    main_basesoc_sram0_we[2] = (((main_basesoc_interface0_ram_bus_cyc & main_basesoc_interface0_ram_bus_stb) & main_basesoc_interface0_ram_bus_we) & main_basesoc_interface0_ram_bus_sel[2]);
    main_basesoc_sram0_we[3] = (((main_basesoc_interface0_ram_bus_cyc & main_basesoc_interface0_ram_bus_stb) & main_basesoc_interface0_ram_bus_we) & main_basesoc_interface0_ram_bus_sel[3]);
end
assign main_basesoc_sram0_adr = main_basesoc_interface0_ram_bus_adr[10:0];
assign main_basesoc_interface0_ram_bus_dat_r = main_basesoc_sram0_dat_r;
assign main_basesoc_sram0_dat_w = main_basesoc_interface0_ram_bus_dat_w;
always @(*) begin
    main_basesoc_sram1_we = 4'd0;
    main_basesoc_sram1_we[0] = (((main_basesoc_interface1_ram_bus_cyc & main_basesoc_interface1_ram_bus_stb) & main_basesoc_interface1_ram_bus_we) & main_basesoc_interface1_ram_bus_sel[0]);
    main_basesoc_sram1_we[1] = (((main_basesoc_interface1_ram_bus_cyc & main_basesoc_interface1_ram_bus_stb) & main_basesoc_interface1_ram_bus_we) & main_basesoc_interface1_ram_bus_sel[1]);
    main_basesoc_sram1_we[2] = (((main_basesoc_interface1_ram_bus_cyc & main_basesoc_interface1_ram_bus_stb) & main_basesoc_interface1_ram_bus_we) & main_basesoc_interface1_ram_bus_sel[2]);
    main_basesoc_sram1_we[3] = (((main_basesoc_interface1_ram_bus_cyc & main_basesoc_interface1_ram_bus_stb) & main_basesoc_interface1_ram_bus_we) & main_basesoc_interface1_ram_bus_sel[3]);
end
assign main_basesoc_sram1_adr = main_basesoc_interface1_ram_bus_adr[13:0];
assign main_basesoc_interface1_ram_bus_dat_r = main_basesoc_sram1_dat_r;
assign main_basesoc_sram1_dat_w = main_basesoc_interface1_ram_bus_dat_w;
assign main_basesoc_uart_core_uart_sink_valid = main_basesoc_uart_core_rx_source_valid;
assign main_basesoc_uart_core_rx_source_ready = main_basesoc_uart_core_uart_sink_ready;
assign main_basesoc_uart_core_uart_sink_first = main_basesoc_uart_core_rx_source_first;
assign main_basesoc_uart_core_uart_sink_last = main_basesoc_uart_core_rx_source_last;
assign main_basesoc_uart_core_uart_sink_payload_data = main_basesoc_uart_core_rx_source_payload_data;
assign main_basesoc_uart_core_tx_sink_valid = main_basesoc_uart_core_uart_source_valid;
assign main_basesoc_uart_core_uart_source_ready = main_basesoc_uart_core_tx_sink_ready;
assign main_basesoc_uart_core_tx_sink_first = main_basesoc_uart_core_uart_source_first;
assign main_basesoc_uart_core_tx_sink_last = main_basesoc_uart_core_uart_source_last;
assign main_basesoc_uart_core_tx_sink_payload_data = main_basesoc_uart_core_uart_source_payload_data;
assign main_basesoc_uart_core_tx_fifo_sink_valid = main_basesoc_uart_core_rxtx_re;
assign main_basesoc_uart_core_tx_fifo_sink_payload_data = main_basesoc_uart_core_rxtx_r;
assign main_basesoc_uart_core_uart_source_valid = main_basesoc_uart_core_tx_fifo_source_valid;
assign main_basesoc_uart_core_tx_fifo_source_ready = main_basesoc_uart_core_uart_source_ready;
assign main_basesoc_uart_core_uart_source_first = main_basesoc_uart_core_tx_fifo_source_first;
assign main_basesoc_uart_core_uart_source_last = main_basesoc_uart_core_tx_fifo_source_last;
assign main_basesoc_uart_core_uart_source_payload_data = main_basesoc_uart_core_tx_fifo_source_payload_data;
assign main_basesoc_uart_core_txfull_status = (~main_basesoc_uart_core_tx_fifo_sink_ready);
assign main_basesoc_uart_core_txempty_status = (~main_basesoc_uart_core_tx_fifo_source_valid);
assign main_basesoc_uart_core_tx_trigger = main_basesoc_uart_core_tx_fifo_sink_ready;
assign main_basesoc_uart_core_rx_fifo_sink_valid = main_basesoc_uart_core_uart_sink_valid;
assign main_basesoc_uart_core_uart_sink_ready = main_basesoc_uart_core_rx_fifo_sink_ready;
assign main_basesoc_uart_core_rx_fifo_sink_first = main_basesoc_uart_core_uart_sink_first;
assign main_basesoc_uart_core_rx_fifo_sink_last = main_basesoc_uart_core_uart_sink_last;
assign main_basesoc_uart_core_rx_fifo_sink_payload_data = main_basesoc_uart_core_uart_sink_payload_data;
assign main_basesoc_uart_core_rxtx_w = main_basesoc_uart_core_rx_fifo_source_payload_data;
assign main_basesoc_uart_core_rx_fifo_source_ready = main_basesoc_uart_core_rx_clear;
assign main_basesoc_uart_core_rxempty_status = (~main_basesoc_uart_core_rx_fifo_source_valid);
assign main_basesoc_uart_core_rxfull_status = (~main_basesoc_uart_core_rx_fifo_sink_ready);
assign main_basesoc_uart_core_rx_trigger = main_basesoc_uart_core_rx_fifo_source_valid;
assign main_basesoc_uart_core_tx0 = main_basesoc_uart_core_tx_status;
assign main_basesoc_uart_core_tx1 = main_basesoc_uart_core_tx_pending;
always @(*) begin
    main_basesoc_uart_core_tx_clear = 1'd0;
    if ((main_basesoc_uart_core_pending_wr_stb & main_basesoc_uart_core_pending_wr_data[0])) begin
        main_basesoc_uart_core_tx_clear = 1'd1;
    end
end
assign main_basesoc_uart_core_rx0 = main_basesoc_uart_core_rx_status;
assign main_basesoc_uart_core_rx1 = main_basesoc_uart_core_rx_pending;
always @(*) begin
    main_basesoc_uart_core_rx_clear = 1'd0;
    if ((main_basesoc_uart_core_pending_wr_stb & main_basesoc_uart_core_pending_wr_data[1])) begin
        main_basesoc_uart_core_rx_clear = 1'd1;
    end
end
assign main_basesoc_uart_core_irq = ((main_basesoc_uart_core_pending_status[0] & main_basesoc_uart_core_enable_storage[0]) | (main_basesoc_uart_core_pending_status[1] & main_basesoc_uart_core_enable_storage[1]));
assign main_basesoc_uart_core_tx_status = main_basesoc_uart_core_tx_trigger;
assign main_basesoc_uart_core_tx_pending = main_basesoc_uart_core_tx_trigger;
assign main_basesoc_uart_core_rx_status = main_basesoc_uart_core_rx_trigger;
assign main_basesoc_uart_core_rx_pending = main_basesoc_uart_core_rx_trigger;
always @(*) begin
    builder_rs232phytx_next_state = 1'd0;
    main_basesoc_serial_tx_rs232phytx_next_value1 = 1'd0;
    main_basesoc_serial_tx_rs232phytx_next_value_ce1 = 1'd0;
    main_basesoc_uart_core_tx_count_rs232phytx_next_value0 = 4'd0;
    main_basesoc_uart_core_tx_count_rs232phytx_next_value_ce0 = 1'd0;
    main_basesoc_uart_core_tx_data_rs232phytx_next_value2 = 8'd0;
    main_basesoc_uart_core_tx_data_rs232phytx_next_value_ce2 = 1'd0;
    main_basesoc_uart_core_tx_enable = 1'd0;
    main_basesoc_uart_core_tx_sink_ready = 1'd0;
    builder_rs232phytx_next_state = builder_rs232phytx_state;
    case (builder_rs232phytx_state)
        1'd1: begin
            main_basesoc_uart_core_tx_enable = 1'd1;
            if (main_basesoc_uart_core_tx_tick) begin
                main_basesoc_serial_tx_rs232phytx_next_value1 = main_basesoc_uart_core_tx_data[0];
                main_basesoc_serial_tx_rs232phytx_next_value_ce1 = 1'd1;
                main_basesoc_uart_core_tx_count_rs232phytx_next_value0 = (main_basesoc_uart_core_tx_count + 1'd1);
                main_basesoc_uart_core_tx_count_rs232phytx_next_value_ce0 = 1'd1;
                main_basesoc_uart_core_tx_data_rs232phytx_next_value2 = {1'd1, main_basesoc_uart_core_tx_data[7:1]};
                main_basesoc_uart_core_tx_data_rs232phytx_next_value_ce2 = 1'd1;
                if ((main_basesoc_uart_core_tx_count == 4'd9)) begin
                    main_basesoc_uart_core_tx_sink_ready = 1'd1;
                    builder_rs232phytx_next_state = 1'd0;
                end
            end
        end
        default: begin
            main_basesoc_uart_core_tx_count_rs232phytx_next_value0 = 1'd0;
            main_basesoc_uart_core_tx_count_rs232phytx_next_value_ce0 = 1'd1;
            main_basesoc_serial_tx_rs232phytx_next_value1 = 1'd1;
            main_basesoc_serial_tx_rs232phytx_next_value_ce1 = 1'd1;
            if (main_basesoc_uart_core_tx_sink_valid) begin
                main_basesoc_serial_tx_rs232phytx_next_value1 = 1'd0;
                main_basesoc_serial_tx_rs232phytx_next_value_ce1 = 1'd1;
                main_basesoc_uart_core_tx_data_rs232phytx_next_value2 = main_basesoc_uart_core_tx_sink_payload_data;
                main_basesoc_uart_core_tx_data_rs232phytx_next_value_ce2 = 1'd1;
                builder_rs232phytx_next_state = 1'd1;
            end
        end
    endcase
end
always @(*) begin
    builder_rs232phyrx_next_state = 1'd0;
    main_basesoc_uart_core_rx_count_rs232phyrx_next_value0 = 4'd0;
    main_basesoc_uart_core_rx_count_rs232phyrx_next_value_ce0 = 1'd0;
    main_basesoc_uart_core_rx_data_rs232phyrx_next_value1 = 8'd0;
    main_basesoc_uart_core_rx_data_rs232phyrx_next_value_ce1 = 1'd0;
    main_basesoc_uart_core_rx_enable = 1'd0;
    main_basesoc_uart_core_rx_framing_error = 1'd0;
    main_basesoc_uart_core_rx_overflow = 1'd0;
    main_basesoc_uart_core_rx_source_payload_data = 8'd0;
    main_basesoc_uart_core_rx_source_valid = 1'd0;
    builder_rs232phyrx_next_state = builder_rs232phyrx_state;
    case (builder_rs232phyrx_state)
        1'd1: begin
            main_basesoc_uart_core_rx_enable = 1'd1;
            if (main_basesoc_uart_core_rx_tick) begin
                main_basesoc_uart_core_rx_count_rs232phyrx_next_value0 = (main_basesoc_uart_core_rx_count + 1'd1);
                main_basesoc_uart_core_rx_count_rs232phyrx_next_value_ce0 = 1'd1;
                main_basesoc_uart_core_rx_data_rs232phyrx_next_value1 = {main_basesoc_uart_core_rx_rx, main_basesoc_uart_core_rx_data[7:1]};
                main_basesoc_uart_core_rx_data_rs232phyrx_next_value_ce1 = 1'd1;
                if (((main_basesoc_uart_core_rx_count == 1'd0) & (main_basesoc_uart_core_rx_rx != 1'd0))) begin
                    builder_rs232phyrx_next_state = 1'd0;
                end
                if ((main_basesoc_uart_core_rx_count == 4'd9)) begin
                    main_basesoc_uart_core_rx_source_valid = (main_basesoc_uart_core_rx_rx == 1'd1);
                    main_basesoc_uart_core_rx_source_payload_data = main_basesoc_uart_core_rx_data;
                    main_basesoc_uart_core_rx_framing_error = (main_basesoc_uart_core_rx_rx != 1'd1);
                    main_basesoc_uart_core_rx_overflow = ((main_basesoc_uart_core_rx_rx == 1'd1) & (~main_basesoc_uart_core_rx_source_ready));
                    builder_rs232phyrx_next_state = 1'd0;
                end
            end
        end
        default: begin
            main_basesoc_uart_core_rx_count_rs232phyrx_next_value0 = 1'd0;
            main_basesoc_uart_core_rx_count_rs232phyrx_next_value_ce0 = 1'd1;
            if (((main_basesoc_uart_core_rx_rx == 1'd0) & (main_basesoc_uart_core_rx_rx_d == 1'd1))) begin
                builder_rs232phyrx_next_state = 1'd1;
            end
        end
    endcase
end
assign main_basesoc_uart_core_tx_fifo_syncfifo_din = {main_basesoc_uart_core_tx_fifo_fifo_in_last, main_basesoc_uart_core_tx_fifo_fifo_in_first, main_basesoc_uart_core_tx_fifo_fifo_in_payload_data};
assign {main_basesoc_uart_core_tx_fifo_fifo_out_last, main_basesoc_uart_core_tx_fifo_fifo_out_first, main_basesoc_uart_core_tx_fifo_fifo_out_payload_data} = main_basesoc_uart_core_tx_fifo_syncfifo_dout;
assign main_basesoc_uart_core_tx_fifo_sink_ready = main_basesoc_uart_core_tx_fifo_syncfifo_writable;
assign main_basesoc_uart_core_tx_fifo_syncfifo_we = main_basesoc_uart_core_tx_fifo_sink_valid;
assign main_basesoc_uart_core_tx_fifo_fifo_in_first = main_basesoc_uart_core_tx_fifo_sink_first;
assign main_basesoc_uart_core_tx_fifo_fifo_in_last = main_basesoc_uart_core_tx_fifo_sink_last;
assign main_basesoc_uart_core_tx_fifo_fifo_in_payload_data = main_basesoc_uart_core_tx_fifo_sink_payload_data;
assign main_basesoc_uart_core_tx_fifo_source_valid = main_basesoc_uart_core_tx_fifo_readable;
assign main_basesoc_uart_core_tx_fifo_source_first = main_basesoc_uart_core_tx_fifo_fifo_out_first;
assign main_basesoc_uart_core_tx_fifo_source_last = main_basesoc_uart_core_tx_fifo_fifo_out_last;
assign main_basesoc_uart_core_tx_fifo_source_payload_data = main_basesoc_uart_core_tx_fifo_fifo_out_payload_data;
assign main_basesoc_uart_core_tx_fifo_re = main_basesoc_uart_core_tx_fifo_source_ready;
assign main_basesoc_uart_core_tx_fifo_syncfifo_re = (main_basesoc_uart_core_tx_fifo_syncfifo_readable & ((~main_basesoc_uart_core_tx_fifo_readable) | main_basesoc_uart_core_tx_fifo_re));
assign main_basesoc_uart_core_tx_fifo_level1 = (main_basesoc_uart_core_tx_fifo_level0 + main_basesoc_uart_core_tx_fifo_readable);
always @(*) begin
    main_basesoc_uart_core_tx_fifo_wrport_adr = 4'd0;
    if (main_basesoc_uart_core_tx_fifo_replace) begin
        main_basesoc_uart_core_tx_fifo_wrport_adr = (main_basesoc_uart_core_tx_fifo_produce - 1'd1);
    end else begin
        main_basesoc_uart_core_tx_fifo_wrport_adr = main_basesoc_uart_core_tx_fifo_produce;
    end
end
assign main_basesoc_uart_core_tx_fifo_wrport_dat_w = main_basesoc_uart_core_tx_fifo_syncfifo_din;
assign main_basesoc_uart_core_tx_fifo_wrport_we = (main_basesoc_uart_core_tx_fifo_syncfifo_we & (main_basesoc_uart_core_tx_fifo_syncfifo_writable | main_basesoc_uart_core_tx_fifo_replace));
assign main_basesoc_uart_core_tx_fifo_do_read = (main_basesoc_uart_core_tx_fifo_syncfifo_readable & main_basesoc_uart_core_tx_fifo_syncfifo_re);
assign main_basesoc_uart_core_tx_fifo_rdport_adr = main_basesoc_uart_core_tx_fifo_consume;
assign main_basesoc_uart_core_tx_fifo_syncfifo_dout = main_basesoc_uart_core_tx_fifo_rdport_dat_r;
assign main_basesoc_uart_core_tx_fifo_rdport_re = main_basesoc_uart_core_tx_fifo_do_read;
assign main_basesoc_uart_core_tx_fifo_syncfifo_writable = (main_basesoc_uart_core_tx_fifo_level0 != 5'd16);
assign main_basesoc_uart_core_tx_fifo_syncfifo_readable = (main_basesoc_uart_core_tx_fifo_level0 != 1'd0);
assign main_basesoc_uart_core_rx_fifo_syncfifo_din = {main_basesoc_uart_core_rx_fifo_fifo_in_last, main_basesoc_uart_core_rx_fifo_fifo_in_first, main_basesoc_uart_core_rx_fifo_fifo_in_payload_data};
assign {main_basesoc_uart_core_rx_fifo_fifo_out_last, main_basesoc_uart_core_rx_fifo_fifo_out_first, main_basesoc_uart_core_rx_fifo_fifo_out_payload_data} = main_basesoc_uart_core_rx_fifo_syncfifo_dout;
assign main_basesoc_uart_core_rx_fifo_sink_ready = main_basesoc_uart_core_rx_fifo_syncfifo_writable;
assign main_basesoc_uart_core_rx_fifo_syncfifo_we = main_basesoc_uart_core_rx_fifo_sink_valid;
assign main_basesoc_uart_core_rx_fifo_fifo_in_first = main_basesoc_uart_core_rx_fifo_sink_first;
assign main_basesoc_uart_core_rx_fifo_fifo_in_last = main_basesoc_uart_core_rx_fifo_sink_last;
assign main_basesoc_uart_core_rx_fifo_fifo_in_payload_data = main_basesoc_uart_core_rx_fifo_sink_payload_data;
assign main_basesoc_uart_core_rx_fifo_source_valid = main_basesoc_uart_core_rx_fifo_readable;
assign main_basesoc_uart_core_rx_fifo_source_first = main_basesoc_uart_core_rx_fifo_fifo_out_first;
assign main_basesoc_uart_core_rx_fifo_source_last = main_basesoc_uart_core_rx_fifo_fifo_out_last;
assign main_basesoc_uart_core_rx_fifo_source_payload_data = main_basesoc_uart_core_rx_fifo_fifo_out_payload_data;
assign main_basesoc_uart_core_rx_fifo_re = main_basesoc_uart_core_rx_fifo_source_ready;
assign main_basesoc_uart_core_rx_fifo_syncfifo_re = (main_basesoc_uart_core_rx_fifo_syncfifo_readable & ((~main_basesoc_uart_core_rx_fifo_readable) | main_basesoc_uart_core_rx_fifo_re));
assign main_basesoc_uart_core_rx_fifo_level1 = (main_basesoc_uart_core_rx_fifo_level0 + main_basesoc_uart_core_rx_fifo_readable);
always @(*) begin
    main_basesoc_uart_core_rx_fifo_wrport_adr = 4'd0;
    if (main_basesoc_uart_core_rx_fifo_replace) begin
        main_basesoc_uart_core_rx_fifo_wrport_adr = (main_basesoc_uart_core_rx_fifo_produce - 1'd1);
    end else begin
        main_basesoc_uart_core_rx_fifo_wrport_adr = main_basesoc_uart_core_rx_fifo_produce;
    end
end
assign main_basesoc_uart_core_rx_fifo_wrport_dat_w = main_basesoc_uart_core_rx_fifo_syncfifo_din;
assign main_basesoc_uart_core_rx_fifo_wrport_we = (main_basesoc_uart_core_rx_fifo_syncfifo_we & (main_basesoc_uart_core_rx_fifo_syncfifo_writable | main_basesoc_uart_core_rx_fifo_replace));
assign main_basesoc_uart_core_rx_fifo_do_read = (main_basesoc_uart_core_rx_fifo_syncfifo_readable & main_basesoc_uart_core_rx_fifo_syncfifo_re);
assign main_basesoc_uart_core_rx_fifo_rdport_adr = main_basesoc_uart_core_rx_fifo_consume;
assign main_basesoc_uart_core_rx_fifo_syncfifo_dout = main_basesoc_uart_core_rx_fifo_rdport_dat_r;
assign main_basesoc_uart_core_rx_fifo_rdport_re = main_basesoc_uart_core_rx_fifo_do_read;
assign main_basesoc_uart_core_rx_fifo_syncfifo_writable = (main_basesoc_uart_core_rx_fifo_level0 != 5'd16);
assign main_basesoc_uart_core_rx_fifo_syncfifo_readable = (main_basesoc_uart_core_rx_fifo_level0 != 1'd0);
assign main_basesoc_timer_zero_trigger = (main_basesoc_timer_value == 1'd0);
assign main_basesoc_timer_zero0 = main_basesoc_timer_zero_status;
assign main_basesoc_timer_zero1 = main_basesoc_timer_zero_pending;
always @(*) begin
    main_basesoc_timer_zero_clear = 1'd0;
    if ((main_basesoc_timer_pending_wr_stb & main_basesoc_timer_pending_wr_data)) begin
        main_basesoc_timer_zero_clear = 1'd1;
    end
end
assign main_basesoc_timer_irq = (main_basesoc_timer_pending_status & main_basesoc_timer_enable_storage);
assign main_basesoc_timer_zero_status = main_basesoc_timer_zero_trigger;
assign main_ethphy_reset = (main_ethphy_reset_storage | main_ethphy_hw_reset_reset);
assign eth_rst_n = (~main_ethphy_reset);
assign main_ethphy_clkin_signal = eth_rx_clk;
assign eth_tx_clk = main_ethphy_clkout_buf0;
assign eth_tx_delayed_clk = main_ethphy_clkout_buf1;
assign main_ethphy_hw_reset_counter_done = (main_ethphy_hw_reset_counter == 9'h100);
assign main_ethphy_hw_reset_counter_ce = (~main_ethphy_hw_reset_counter_done);
assign main_ethphy_hw_reset_reset = (~main_ethphy_hw_reset_counter_done);
assign main_ethphy_sink_ready = 1'd1;
assign main_ethphy_source_payload_be = 1'd1;
assign main_ethphy_last = ((~main_ethphy_rx_ctl[0]) & main_ethphy_rx_ctl_d);
assign main_ethphy_source_last = main_ethphy_last;
assign eth_mdc = main_ethphy_mdc;
assign main_ethphy_data_oe = main_ethphy_oe;
assign main_ethphy_data_w = main_ethphy_w;
assign main_basesoc_core_sink_valid = main_basesoc_wishbone_interface_source_valid;
assign main_basesoc_wishbone_interface_source_ready = main_basesoc_core_sink_ready;
assign main_basesoc_core_sink_first = main_basesoc_wishbone_interface_source_first;
assign main_basesoc_core_sink_last = main_basesoc_wishbone_interface_source_last;
assign main_basesoc_core_sink_payload_data = main_basesoc_wishbone_interface_source_payload_data;
assign main_basesoc_core_sink_payload_be = main_basesoc_wishbone_interface_source_payload_be;
assign main_basesoc_core_sink_payload_error = main_basesoc_wishbone_interface_source_payload_error;
assign main_basesoc_wishbone_interface_sink_valid = main_basesoc_core_source_valid;
assign main_basesoc_core_source_ready = main_basesoc_wishbone_interface_sink_ready;
assign main_basesoc_wishbone_interface_sink_first = main_basesoc_core_source_first;
assign main_basesoc_wishbone_interface_sink_last = main_basesoc_core_source_last;
assign main_basesoc_wishbone_interface_sink_payload_data = main_basesoc_core_source_payload_data;
assign main_basesoc_wishbone_interface_sink_payload_be = main_basesoc_core_source_payload_be;
assign main_basesoc_wishbone_interface_sink_payload_error = main_basesoc_core_source_payload_error;
assign main_basesoc_core_cdc_rst = main_basesoc_core_tx_cdc_ext_rst_to;
assign main_basesoc_core_tx_converter_reset = main_basesoc_core_cdc_rst;
assign main_basesoc_core_tx_padding_reset = main_basesoc_core_cdc_rst;
assign main_basesoc_core_txdatapath_reset = main_basesoc_core_cdc_rst;
assign main_basesoc_core_tx_preamble_reset = main_basesoc_core_cdc_rst;
assign main_basesoc_core_tx_gap_reset = main_basesoc_core_cdc_rst;
assign main_basesoc_core_tx_cdc_write_rst = (sys_rst | main_basesoc_core_tx_cdc_write_ext_rst);
assign main_basesoc_core_tx_cdc_cdc_reset_write = main_basesoc_core_tx_cdc_write_ext_rst;
assign main_basesoc_core_tx_cdc_cdc_reset_read = main_basesoc_core_tx_cdc_ext_rst_to;
assign main_basesoc_core_tx_cdc_cdc_sink_valid = main_basesoc_core_tx_cdc_sink_sink_valid;
assign main_basesoc_core_tx_cdc_sink_sink_ready = main_basesoc_core_tx_cdc_cdc_sink_ready;
assign main_basesoc_core_tx_cdc_cdc_sink_first = main_basesoc_core_tx_cdc_sink_sink_first;
assign main_basesoc_core_tx_cdc_cdc_sink_last = main_basesoc_core_tx_cdc_sink_sink_last;
assign main_basesoc_core_tx_cdc_cdc_sink_payload_data = main_basesoc_core_tx_cdc_sink_sink_payload_data;
assign main_basesoc_core_tx_cdc_cdc_sink_payload_be = main_basesoc_core_tx_cdc_sink_sink_payload_be;
assign main_basesoc_core_tx_cdc_cdc_sink_payload_error = main_basesoc_core_tx_cdc_sink_sink_payload_error;
assign main_basesoc_core_tx_cdc_cdc_source_ready = main_basesoc_core_tx_cdc_source_source_ready;
assign main_basesoc_core_tx_cdc_source_source_first = main_basesoc_core_tx_cdc_cdc_source_first;
assign main_basesoc_core_tx_cdc_source_source_last = main_basesoc_core_tx_cdc_cdc_source_last;
assign main_basesoc_core_tx_cdc_source_source_payload_data = main_basesoc_core_tx_cdc_cdc_source_payload_data;
assign main_basesoc_core_tx_cdc_source_source_payload_be = main_basesoc_core_tx_cdc_cdc_source_payload_be;
assign main_basesoc_core_tx_cdc_source_source_payload_error = main_basesoc_core_tx_cdc_cdc_source_payload_error;
assign main_basesoc_core_tx_cdc_source_source_valid = ((main_basesoc_core_tx_cdc_cdc_source_valid & (~main_basesoc_core_tx_cdc_ext_rst_to)) & (~eth_tx_rst));
assign main_basesoc_core_tx_cdc_cdc_asyncfifo_din = {main_basesoc_core_tx_cdc_cdc_fifo_in_last, main_basesoc_core_tx_cdc_cdc_fifo_in_first, main_basesoc_core_tx_cdc_cdc_fifo_in_payload_error, main_basesoc_core_tx_cdc_cdc_fifo_in_payload_be, main_basesoc_core_tx_cdc_cdc_fifo_in_payload_data};
assign {main_basesoc_core_tx_cdc_cdc_fifo_out_last, main_basesoc_core_tx_cdc_cdc_fifo_out_first, main_basesoc_core_tx_cdc_cdc_fifo_out_payload_error, main_basesoc_core_tx_cdc_cdc_fifo_out_payload_be, main_basesoc_core_tx_cdc_cdc_fifo_out_payload_data} = main_basesoc_core_tx_cdc_cdc_asyncfifo_dout;
assign main_basesoc_core_tx_cdc_cdc_sink_ready = main_basesoc_core_tx_cdc_cdc_asyncfifo_writable;
assign main_basesoc_core_tx_cdc_cdc_asyncfifo_we = main_basesoc_core_tx_cdc_cdc_sink_valid;
assign main_basesoc_core_tx_cdc_cdc_fifo_in_first = main_basesoc_core_tx_cdc_cdc_sink_first;
assign main_basesoc_core_tx_cdc_cdc_fifo_in_last = main_basesoc_core_tx_cdc_cdc_sink_last;
assign main_basesoc_core_tx_cdc_cdc_fifo_in_payload_data = main_basesoc_core_tx_cdc_cdc_sink_payload_data;
assign main_basesoc_core_tx_cdc_cdc_fifo_in_payload_be = main_basesoc_core_tx_cdc_cdc_sink_payload_be;
assign main_basesoc_core_tx_cdc_cdc_fifo_in_payload_error = main_basesoc_core_tx_cdc_cdc_sink_payload_error;
assign main_basesoc_core_tx_cdc_cdc_source_valid = main_basesoc_core_tx_cdc_cdc_asyncfifo_readable;
assign main_basesoc_core_tx_cdc_cdc_source_first = main_basesoc_core_tx_cdc_cdc_fifo_out_first;
assign main_basesoc_core_tx_cdc_cdc_source_last = main_basesoc_core_tx_cdc_cdc_fifo_out_last;
assign main_basesoc_core_tx_cdc_cdc_source_payload_data = main_basesoc_core_tx_cdc_cdc_fifo_out_payload_data;
assign main_basesoc_core_tx_cdc_cdc_source_payload_be = main_basesoc_core_tx_cdc_cdc_fifo_out_payload_be;
assign main_basesoc_core_tx_cdc_cdc_source_payload_error = main_basesoc_core_tx_cdc_cdc_fifo_out_payload_error;
assign main_basesoc_core_tx_cdc_cdc_asyncfifo_re = main_basesoc_core_tx_cdc_cdc_source_ready;
assign main_basesoc_core_tx_cdc_cdc_graycounter0_ce = (main_basesoc_core_tx_cdc_cdc_asyncfifo_writable & main_basesoc_core_tx_cdc_cdc_asyncfifo_we);
assign main_basesoc_core_tx_cdc_cdc_graycounter1_ce = (main_basesoc_core_tx_cdc_cdc_asyncfifo_readable & main_basesoc_core_tx_cdc_cdc_asyncfifo_re);
assign main_basesoc_core_tx_cdc_cdc_asyncfifo_writable = (((main_basesoc_core_tx_cdc_cdc_graycounter0_q[5] == main_basesoc_core_tx_cdc_cdc_consume_wdomain[5]) | (main_basesoc_core_tx_cdc_cdc_graycounter0_q[4] == main_basesoc_core_tx_cdc_cdc_consume_wdomain[4])) | (main_basesoc_core_tx_cdc_cdc_graycounter0_q[3:0] != main_basesoc_core_tx_cdc_cdc_consume_wdomain[3:0]));
assign main_basesoc_core_tx_cdc_cdc_asyncfifo_readable = (main_basesoc_core_tx_cdc_cdc_graycounter1_q != main_basesoc_core_tx_cdc_cdc_produce_rdomain);
assign main_basesoc_core_tx_cdc_cdc_wrport_adr = main_basesoc_core_tx_cdc_cdc_graycounter0_q_binary[4:0];
assign main_basesoc_core_tx_cdc_cdc_wrport_dat_w = main_basesoc_core_tx_cdc_cdc_asyncfifo_din;
assign main_basesoc_core_tx_cdc_cdc_wrport_we = main_basesoc_core_tx_cdc_cdc_graycounter0_ce;
assign main_basesoc_core_tx_cdc_cdc_rdport_adr = main_basesoc_core_tx_cdc_cdc_graycounter1_q_next_binary[4:0];
assign main_basesoc_core_tx_cdc_cdc_asyncfifo_dout = main_basesoc_core_tx_cdc_cdc_rdport_dat_r;
always @(*) begin
    main_basesoc_core_tx_cdc_cdc_graycounter0_q_next_binary = 6'd0;
    if (main_basesoc_core_tx_cdc_cdc_graycounter0_ce) begin
        main_basesoc_core_tx_cdc_cdc_graycounter0_q_next_binary = (main_basesoc_core_tx_cdc_cdc_graycounter0_q_binary + 1'd1);
    end else begin
        main_basesoc_core_tx_cdc_cdc_graycounter0_q_next_binary = main_basesoc_core_tx_cdc_cdc_graycounter0_q_binary;
    end
end
assign main_basesoc_core_tx_cdc_cdc_graycounter0_q_next = (main_basesoc_core_tx_cdc_cdc_graycounter0_q_next_binary ^ main_basesoc_core_tx_cdc_cdc_graycounter0_q_next_binary[5:1]);
always @(*) begin
    main_basesoc_core_tx_cdc_cdc_graycounter1_q_next_binary = 6'd0;
    if (main_basesoc_core_tx_cdc_cdc_graycounter1_ce) begin
        main_basesoc_core_tx_cdc_cdc_graycounter1_q_next_binary = (main_basesoc_core_tx_cdc_cdc_graycounter1_q_binary + 1'd1);
    end else begin
        main_basesoc_core_tx_cdc_cdc_graycounter1_q_next_binary = main_basesoc_core_tx_cdc_cdc_graycounter1_q_binary;
    end
end
assign main_basesoc_core_tx_cdc_cdc_graycounter1_q_next = (main_basesoc_core_tx_cdc_cdc_graycounter1_q_next_binary ^ main_basesoc_core_tx_cdc_cdc_graycounter1_q_next_binary[5:1]);
assign main_basesoc_core_tx_converter_converter_sink_valid = main_basesoc_core_tx_converter_sink_sink_valid;
assign main_basesoc_core_tx_converter_converter_sink_first = main_basesoc_core_tx_converter_sink_sink_first;
assign main_basesoc_core_tx_converter_converter_sink_last = main_basesoc_core_tx_converter_sink_sink_last;
assign main_basesoc_core_tx_converter_sink_sink_ready = main_basesoc_core_tx_converter_converter_sink_ready;
always @(*) begin
    main_basesoc_core_tx_converter_converter_sink_payload_data = 40'd0;
    main_basesoc_core_tx_converter_converter_sink_payload_data[7:0] = main_basesoc_core_tx_converter_sink_sink_payload_data[7:0];
    main_basesoc_core_tx_converter_converter_sink_payload_data[8] = main_basesoc_core_tx_converter_sink_sink_payload_be[0];
    main_basesoc_core_tx_converter_converter_sink_payload_data[9] = main_basesoc_core_tx_converter_sink_sink_payload_error[0];
    main_basesoc_core_tx_converter_converter_sink_payload_data[17:10] = main_basesoc_core_tx_converter_sink_sink_payload_data[15:8];
    main_basesoc_core_tx_converter_converter_sink_payload_data[18] = main_basesoc_core_tx_converter_sink_sink_payload_be[1];
    main_basesoc_core_tx_converter_converter_sink_payload_data[19] = main_basesoc_core_tx_converter_sink_sink_payload_error[1];
    main_basesoc_core_tx_converter_converter_sink_payload_data[27:20] = main_basesoc_core_tx_converter_sink_sink_payload_data[23:16];
    main_basesoc_core_tx_converter_converter_sink_payload_data[28] = main_basesoc_core_tx_converter_sink_sink_payload_be[2];
    main_basesoc_core_tx_converter_converter_sink_payload_data[29] = main_basesoc_core_tx_converter_sink_sink_payload_error[2];
    main_basesoc_core_tx_converter_converter_sink_payload_data[37:30] = main_basesoc_core_tx_converter_sink_sink_payload_data[31:24];
    main_basesoc_core_tx_converter_converter_sink_payload_data[38] = main_basesoc_core_tx_converter_sink_sink_payload_be[3];
    main_basesoc_core_tx_converter_converter_sink_payload_data[39] = main_basesoc_core_tx_converter_sink_sink_payload_error[3];
end
always @(*) begin
    main_basesoc_core_tx_converter_packet_end = 1'd0;
    case (main_basesoc_core_tx_converter_index)
        1'd0: begin
            main_basesoc_core_tx_converter_packet_end = (main_basesoc_core_tx_converter_sink_sink_last & (main_basesoc_core_tx_converter_sink_sink_payload_be[3:1] == 1'd0));
        end
        1'd1: begin
            main_basesoc_core_tx_converter_packet_end = (main_basesoc_core_tx_converter_sink_sink_last & (main_basesoc_core_tx_converter_sink_sink_payload_be[3:2] == 1'd0));
        end
        2'd2: begin
            main_basesoc_core_tx_converter_packet_end = (main_basesoc_core_tx_converter_sink_sink_last & (main_basesoc_core_tx_converter_sink_sink_payload_be[3] == 1'd0));
        end
        2'd3: begin
            main_basesoc_core_tx_converter_packet_end = main_basesoc_core_tx_converter_sink_sink_last;
        end
    endcase
end
assign main_basesoc_core_tx_converter_source_source_valid = (main_basesoc_core_tx_converter_converter_source_valid & (~main_basesoc_core_tx_converter_drop));
assign main_basesoc_core_tx_converter_source_source_first = (main_basesoc_core_tx_converter_converter_source_first & (~main_basesoc_core_tx_converter_drop));
assign main_basesoc_core_tx_converter_source_source_last = main_basesoc_core_tx_converter_packet_end;
assign main_basesoc_core_tx_converter_converter_source_ready = (main_basesoc_core_tx_converter_source_source_ready | main_basesoc_core_tx_converter_drop);
assign {main_basesoc_core_tx_converter_source_source_payload_error, main_basesoc_core_tx_converter_source_source_payload_be, main_basesoc_core_tx_converter_source_source_payload_data} = main_basesoc_core_tx_converter_converter_source_payload_data;
assign main_basesoc_core_tx_converter_converter_first = (main_basesoc_core_tx_converter_converter_mux == 1'd0);
assign main_basesoc_core_tx_converter_converter_last = (main_basesoc_core_tx_converter_converter_mux == 2'd3);
assign main_basesoc_core_tx_converter_converter_source_valid = main_basesoc_core_tx_converter_converter_sink_valid;
assign main_basesoc_core_tx_converter_converter_source_first = (main_basesoc_core_tx_converter_converter_sink_first & main_basesoc_core_tx_converter_converter_first);
assign main_basesoc_core_tx_converter_converter_source_last = (main_basesoc_core_tx_converter_converter_sink_last & main_basesoc_core_tx_converter_converter_last);
assign main_basesoc_core_tx_converter_converter_sink_ready = (main_basesoc_core_tx_converter_converter_last & main_basesoc_core_tx_converter_converter_source_ready);
always @(*) begin
    main_basesoc_core_tx_converter_converter_source_payload_data = 10'd0;
    case (main_basesoc_core_tx_converter_converter_mux)
        1'd0: begin
            main_basesoc_core_tx_converter_converter_source_payload_data = main_basesoc_core_tx_converter_converter_sink_payload_data[9:0];
        end
        1'd1: begin
            main_basesoc_core_tx_converter_converter_source_payload_data = main_basesoc_core_tx_converter_converter_sink_payload_data[19:10];
        end
        2'd2: begin
            main_basesoc_core_tx_converter_converter_source_payload_data = main_basesoc_core_tx_converter_converter_sink_payload_data[29:20];
        end
        default: begin
            main_basesoc_core_tx_converter_converter_source_payload_data = main_basesoc_core_tx_converter_converter_sink_payload_data[39:30];
        end
    endcase
end
assign main_basesoc_core_tx_converter_converter_source_payload_valid_token_count = main_basesoc_core_tx_converter_converter_last;
assign main_basesoc_core_tx_padding_counter_done = (main_basesoc_core_tx_padding_counter >= 6'd59);
always @(*) begin
    builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_next_state = 1'd0;
    main_basesoc_core_tx_padding_counter_clockdomainsrenamer0_next_value = 16'd0;
    main_basesoc_core_tx_padding_counter_clockdomainsrenamer0_next_value_ce = 1'd0;
    main_basesoc_core_tx_padding_sink_ready = 1'd0;
    main_basesoc_core_tx_padding_source_first = 1'd0;
    main_basesoc_core_tx_padding_source_last = 1'd0;
    main_basesoc_core_tx_padding_source_payload_be = 1'd0;
    main_basesoc_core_tx_padding_source_payload_data = 8'd0;
    main_basesoc_core_tx_padding_source_payload_error = 1'd0;
    main_basesoc_core_tx_padding_source_valid = 1'd0;
    case (builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_state)
        1'd1: begin
        end
        default: begin
            main_basesoc_core_tx_padding_sink_ready = main_basesoc_core_tx_padding_source_ready;
        end
    endcase
    case (builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_state)
        1'd1: begin
        end
        default: begin
            main_basesoc_core_tx_padding_source_first = main_basesoc_core_tx_padding_sink_first;
        end
    endcase
    case (builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_state)
        1'd1: begin
            if (main_basesoc_core_tx_padding_counter_done) begin
                main_basesoc_core_tx_padding_source_last = 1'd1;
            end
        end
        default: begin
            main_basesoc_core_tx_padding_source_last = main_basesoc_core_tx_padding_sink_last;
            if (main_basesoc_core_tx_padding_sink_last) begin
                if ((~main_basesoc_core_tx_padding_counter_done)) begin
                    main_basesoc_core_tx_padding_source_last = 1'd0;
                end else begin
                end
            end
        end
    endcase
    case (builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_state)
        1'd1: begin
            main_basesoc_core_tx_padding_source_payload_be = 1'd1;
            if (main_basesoc_core_tx_padding_counter_done) begin
                main_basesoc_core_tx_padding_source_payload_be = 1'd1;
            end
        end
        default: begin
            main_basesoc_core_tx_padding_source_payload_be = main_basesoc_core_tx_padding_sink_payload_be;
            if (main_basesoc_core_tx_padding_sink_last) begin
                if ((~main_basesoc_core_tx_padding_counter_done)) begin
                    main_basesoc_core_tx_padding_source_payload_be = 1'd1;
                end else begin
                    if (((main_basesoc_core_tx_padding_counter == 6'd59) & (main_basesoc_core_tx_padding_sink_payload_be < 1'd1))) begin
                        main_basesoc_core_tx_padding_source_payload_be = 1'd1;
                    end
                end
            end
        end
    endcase
    case (builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_state)
        1'd1: begin
            main_basesoc_core_tx_padding_source_payload_data = 1'd0;
        end
        default: begin
            main_basesoc_core_tx_padding_source_payload_data = main_basesoc_core_tx_padding_sink_payload_data;
            if (main_basesoc_core_tx_padding_sink_last) begin
                if ((~main_basesoc_core_tx_padding_sink_payload_be)) begin
                    main_basesoc_core_tx_padding_source_payload_data = 1'd0;
                end
            end
        end
    endcase
    case (builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_state)
        1'd1: begin
        end
        default: begin
            main_basesoc_core_tx_padding_source_payload_error = main_basesoc_core_tx_padding_sink_payload_error;
        end
    endcase
    case (builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_state)
        1'd1: begin
            main_basesoc_core_tx_padding_source_valid = 1'd1;
        end
        default: begin
            main_basesoc_core_tx_padding_source_valid = main_basesoc_core_tx_padding_sink_valid;
        end
    endcase
    builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_next_state = builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_state;
    case (builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_state)
        1'd1: begin
            if ((main_basesoc_core_tx_padding_source_valid & main_basesoc_core_tx_padding_source_ready)) begin
                if (main_basesoc_core_tx_padding_counter_done) begin
                    builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_next_state = 1'd0;
                end
            end
        end
        default: begin
            if ((main_basesoc_core_tx_padding_source_valid & main_basesoc_core_tx_padding_source_ready)) begin
                if (main_basesoc_core_tx_padding_sink_last) begin
                    if ((~main_basesoc_core_tx_padding_counter_done)) begin
                        builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_next_state = 1'd1;
                    end else begin
                    end
                end
            end
        end
    endcase
    case (builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_state)
        1'd1: begin
            if ((main_basesoc_core_tx_padding_source_valid & main_basesoc_core_tx_padding_source_ready)) begin
                main_basesoc_core_tx_padding_counter_clockdomainsrenamer0_next_value = (main_basesoc_core_tx_padding_counter + 1'd1);
                if (main_basesoc_core_tx_padding_counter_done) begin
                    main_basesoc_core_tx_padding_counter_clockdomainsrenamer0_next_value = 1'd0;
                end
            end
        end
        default: begin
            if ((main_basesoc_core_tx_padding_source_valid & main_basesoc_core_tx_padding_source_ready)) begin
                main_basesoc_core_tx_padding_counter_clockdomainsrenamer0_next_value = (main_basesoc_core_tx_padding_counter + 1'd1);
                if (main_basesoc_core_tx_padding_sink_last) begin
                    if ((~main_basesoc_core_tx_padding_counter_done)) begin
                    end else begin
                        main_basesoc_core_tx_padding_counter_clockdomainsrenamer0_next_value = 1'd0;
                    end
                end
            end
        end
    endcase
    case (builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_state)
        1'd1: begin
            if ((main_basesoc_core_tx_padding_source_valid & main_basesoc_core_tx_padding_source_ready)) begin
                main_basesoc_core_tx_padding_counter_clockdomainsrenamer0_next_value_ce = 1'd1;
                if (main_basesoc_core_tx_padding_counter_done) begin
                    main_basesoc_core_tx_padding_counter_clockdomainsrenamer0_next_value_ce = 1'd1;
                end
            end
        end
        default: begin
            if ((main_basesoc_core_tx_padding_source_valid & main_basesoc_core_tx_padding_source_ready)) begin
                main_basesoc_core_tx_padding_counter_clockdomainsrenamer0_next_value_ce = 1'd1;
                if (main_basesoc_core_tx_padding_sink_last) begin
                    if ((~main_basesoc_core_tx_padding_counter_done)) begin
                    end else begin
                        main_basesoc_core_tx_padding_counter_clockdomainsrenamer0_next_value_ce = 1'd1;
                    end
                end
            end
        end
    endcase
end
assign main_basesoc_core_liteethmaccrc32inserter_data0 = main_basesoc_core_liteethmaccrc32inserter_sink_payload_data;
assign main_basesoc_core_liteethmaccrc32inserter_be1 = main_basesoc_core_liteethmaccrc32inserter_sink_payload_be;
assign main_basesoc_core_liteethmaccrc32inserter_cnt_done = (main_basesoc_core_liteethmaccrc32inserter_cnt == 1'd0);
assign main_basesoc_core_liteethmaccrc32inserter_sink_valid = main_basesoc_core_source_source_valid;
assign main_basesoc_core_source_source_ready = main_basesoc_core_liteethmaccrc32inserter_sink_ready;
assign main_basesoc_core_liteethmaccrc32inserter_sink_first = main_basesoc_core_source_source_first;
assign main_basesoc_core_liteethmaccrc32inserter_sink_last = main_basesoc_core_source_source_last;
assign main_basesoc_core_liteethmaccrc32inserter_sink_payload_data = main_basesoc_core_source_source_payload_data;
assign main_basesoc_core_liteethmaccrc32inserter_sink_payload_be = main_basesoc_core_source_source_payload_be;
assign main_basesoc_core_liteethmaccrc32inserter_sink_payload_error = main_basesoc_core_source_source_payload_error;
assign main_basesoc_core_liteethmaccrc32inserter_data1 = main_basesoc_core_liteethmaccrc32inserter_data0;
assign main_basesoc_core_liteethmaccrc32inserter_crc_prev = main_basesoc_core_liteethmaccrc32inserter_reg;
always @(*) begin
    main_basesoc_core_liteethmaccrc32inserter_error = 1'd0;
    main_basesoc_core_liteethmaccrc32inserter_value = 32'd0;
    if (main_basesoc_core_liteethmaccrc32inserter_be1) begin
        main_basesoc_core_liteethmaccrc32inserter_value = ({main_basesoc_core_liteethmaccrc32inserter_crc_next[0], main_basesoc_core_liteethmaccrc32inserter_crc_next[1], main_basesoc_core_liteethmaccrc32inserter_crc_next[2], main_basesoc_core_liteethmaccrc32inserter_crc_next[3], main_basesoc_core_liteethmaccrc32inserter_crc_next[4], main_basesoc_core_liteethmaccrc32inserter_crc_next[5], main_basesoc_core_liteethmaccrc32inserter_crc_next[6], main_basesoc_core_liteethmaccrc32inserter_crc_next[7], main_basesoc_core_liteethmaccrc32inserter_crc_next[8], main_basesoc_core_liteethmaccrc32inserter_crc_next[9], main_basesoc_core_liteethmaccrc32inserter_crc_next[10], main_basesoc_core_liteethmaccrc32inserter_crc_next[11], main_basesoc_core_liteethmaccrc32inserter_crc_next[12], main_basesoc_core_liteethmaccrc32inserter_crc_next[13], main_basesoc_core_liteethmaccrc32inserter_crc_next[14], main_basesoc_core_liteethmaccrc32inserter_crc_next[15], main_basesoc_core_liteethmaccrc32inserter_crc_next[16], main_basesoc_core_liteethmaccrc32inserter_crc_next[17], main_basesoc_core_liteethmaccrc32inserter_crc_next[18], main_basesoc_core_liteethmaccrc32inserter_crc_next[19], main_basesoc_core_liteethmaccrc32inserter_crc_next[20], main_basesoc_core_liteethmaccrc32inserter_crc_next[21], main_basesoc_core_liteethmaccrc32inserter_crc_next[22], main_basesoc_core_liteethmaccrc32inserter_crc_next[23], main_basesoc_core_liteethmaccrc32inserter_crc_next[24], main_basesoc_core_liteethmaccrc32inserter_crc_next[25], main_basesoc_core_liteethmaccrc32inserter_crc_next[26], main_basesoc_core_liteethmaccrc32inserter_crc_next[27], main_basesoc_core_liteethmaccrc32inserter_crc_next[28], main_basesoc_core_liteethmaccrc32inserter_crc_next[29], main_basesoc_core_liteethmaccrc32inserter_crc_next[30], main_basesoc_core_liteethmaccrc32inserter_crc_next[31]} ^ 32'hffffffff);
        main_basesoc_core_liteethmaccrc32inserter_error = (main_basesoc_core_liteethmaccrc32inserter_crc_next != 32'd3338984827);
    end
end
always @(*) begin
    main_basesoc_core_liteethmaccrc32inserter_crc_next = 32'd0;
    main_basesoc_core_liteethmaccrc32inserter_crc_next[0] = (((main_basesoc_core_liteethmaccrc32inserter_crc_prev[24] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[1]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[7]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[1] = (((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[25] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[0]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[6]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[1]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[7]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[2] = (((((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[26] ^ main_basesoc_core_liteethmaccrc32inserter_data1[5]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[0]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[6]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[1]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[7]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[3] = (((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[27] ^ main_basesoc_core_liteethmaccrc32inserter_data1[4]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[5]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[0]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[6]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[4] = (((((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[28] ^ main_basesoc_core_liteethmaccrc32inserter_data1[3]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[4]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[5]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[1]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[7]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[5] = (((((((((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[29] ^ main_basesoc_core_liteethmaccrc32inserter_data1[2]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[3]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[4]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[0]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[6]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[1]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[7]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[6] = (((((((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[30] ^ main_basesoc_core_liteethmaccrc32inserter_data1[1]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[2]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[3]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[5]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[0]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[6]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[7] = (((((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[31] ^ main_basesoc_core_liteethmaccrc32inserter_data1[0]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[2]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[4]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[5]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[7]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[8] = ((((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[0] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[3]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[4]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[6]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[7]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[9] = ((((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[1] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[2]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[3]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[5]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[6]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[10] = ((((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[2] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[2]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[4]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[5]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[7]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[11] = ((((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[3] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[3]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[4]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[6]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[7]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[12] = ((((((((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[4] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[2]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[3]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[5]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[6]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[1]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[7]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[13] = ((((((((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[5] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[1]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[2]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[4]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[5]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[0]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[6]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[14] = ((((((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[6] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[0]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[1]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[3]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[4]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[5]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[15] = ((((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[7] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[0]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[2]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[3]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[4]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[16] = ((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[8] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[2]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[3]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[7]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[17] = ((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[9] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[1]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[2]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[6]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[18] = ((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[10] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[0]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[1]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[5]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[19] = ((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[11] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[0]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[4]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[20] = ((main_basesoc_core_liteethmaccrc32inserter_crc_prev[12] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[3]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[21] = ((main_basesoc_core_liteethmaccrc32inserter_crc_prev[13] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[2]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[22] = ((main_basesoc_core_liteethmaccrc32inserter_crc_prev[14] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[7]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[23] = ((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[15] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[6]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[1]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[7]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[24] = ((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[16] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[5]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[0]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[6]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[25] = ((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[17] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[4]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[5]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[26] = ((((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[18] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[3]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[4]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[1]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[7]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[27] = ((((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[19] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[2]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[3]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[0]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[6]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[28] = ((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[20] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[1]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[2]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[5]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[29] = ((((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[21] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[0]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[1]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[4]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[30] = ((((main_basesoc_core_liteethmaccrc32inserter_crc_prev[22] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[0]) ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[3]);
    main_basesoc_core_liteethmaccrc32inserter_crc_next[31] = ((main_basesoc_core_liteethmaccrc32inserter_crc_prev[23] ^ main_basesoc_core_liteethmaccrc32inserter_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32inserter_data1[2]);
end
always @(*) begin
    builder_clockdomainsrenamer_txdatapath_bufferizeendpoints_next_state = 2'd0;
    main_basesoc_core_liteethmaccrc32inserter_be0_clockdomainsrenamer1_next_value1 = 1'd0;
    main_basesoc_core_liteethmaccrc32inserter_be0_clockdomainsrenamer1_next_value_ce1 = 1'd0;
    main_basesoc_core_liteethmaccrc32inserter_ce = 1'd0;
    main_basesoc_core_liteethmaccrc32inserter_crc_packet_clockdomainsrenamer1_next_value0 = 32'd0;
    main_basesoc_core_liteethmaccrc32inserter_crc_packet_clockdomainsrenamer1_next_value_ce0 = 1'd0;
    main_basesoc_core_liteethmaccrc32inserter_is_ongoing0 = 1'd0;
    main_basesoc_core_liteethmaccrc32inserter_is_ongoing1 = 1'd0;
    main_basesoc_core_liteethmaccrc32inserter_reset = 1'd0;
    main_basesoc_core_liteethmaccrc32inserter_sink_ready = 1'd0;
    main_basesoc_core_liteethmaccrc32inserter_source_first = 1'd0;
    main_basesoc_core_liteethmaccrc32inserter_source_last = 1'd0;
    main_basesoc_core_liteethmaccrc32inserter_source_payload_be = 1'd0;
    main_basesoc_core_liteethmaccrc32inserter_source_payload_data = 8'd0;
    main_basesoc_core_liteethmaccrc32inserter_source_payload_error = 1'd0;
    main_basesoc_core_liteethmaccrc32inserter_source_valid = 1'd0;
    builder_clockdomainsrenamer_txdatapath_bufferizeendpoints_next_state = builder_clockdomainsrenamer_txdatapath_bufferizeendpoints_state;
    case (builder_clockdomainsrenamer_txdatapath_bufferizeendpoints_state)
        1'd1: begin
            main_basesoc_core_liteethmaccrc32inserter_ce = (main_basesoc_core_liteethmaccrc32inserter_sink_valid & main_basesoc_core_liteethmaccrc32inserter_source_ready);
            main_basesoc_core_liteethmaccrc32inserter_source_valid = main_basesoc_core_liteethmaccrc32inserter_sink_valid;
            main_basesoc_core_liteethmaccrc32inserter_sink_ready = main_basesoc_core_liteethmaccrc32inserter_source_ready;
            main_basesoc_core_liteethmaccrc32inserter_source_first = main_basesoc_core_liteethmaccrc32inserter_sink_first;
            main_basesoc_core_liteethmaccrc32inserter_source_last = main_basesoc_core_liteethmaccrc32inserter_sink_last;
            main_basesoc_core_liteethmaccrc32inserter_source_payload_data = main_basesoc_core_liteethmaccrc32inserter_sink_payload_data;
            main_basesoc_core_liteethmaccrc32inserter_source_payload_be = main_basesoc_core_liteethmaccrc32inserter_sink_payload_be;
            main_basesoc_core_liteethmaccrc32inserter_source_payload_error = main_basesoc_core_liteethmaccrc32inserter_sink_payload_error;
            main_basesoc_core_liteethmaccrc32inserter_source_last = 1'd0;
            main_basesoc_core_liteethmaccrc32inserter_source_payload_be = 1'd1;
            if (main_basesoc_core_liteethmaccrc32inserter_sink_last) begin
                if (main_basesoc_core_liteethmaccrc32inserter_sink_payload_be) begin
                    main_basesoc_core_liteethmaccrc32inserter_source_payload_data = main_basesoc_core_liteethmaccrc32inserter_sink_payload_data;
                end
                if ((1'd0 & (main_basesoc_core_liteethmaccrc32inserter_sink_payload_be <= 4'd15))) begin
                    main_basesoc_core_liteethmaccrc32inserter_source_last = 1'd1;
                    main_basesoc_core_liteethmaccrc32inserter_source_payload_be = ((main_basesoc_core_liteethmaccrc32inserter_sink_payload_be <<< 3'd4) | 4'd15);
                end
            end
            if (((main_basesoc_core_liteethmaccrc32inserter_sink_valid & main_basesoc_core_liteethmaccrc32inserter_sink_last) & main_basesoc_core_liteethmaccrc32inserter_source_ready)) begin
                if ((1'd0 & (main_basesoc_core_liteethmaccrc32inserter_sink_payload_be <= 4'd15))) begin
                    builder_clockdomainsrenamer_txdatapath_bufferizeendpoints_next_state = 1'd0;
                end else begin
                    main_basesoc_core_liteethmaccrc32inserter_crc_packet_clockdomainsrenamer1_next_value0 = main_basesoc_core_liteethmaccrc32inserter_value;
                    main_basesoc_core_liteethmaccrc32inserter_crc_packet_clockdomainsrenamer1_next_value_ce0 = 1'd1;
                    if (1'd0) begin
                        main_basesoc_core_liteethmaccrc32inserter_be0_clockdomainsrenamer1_next_value1 = (main_basesoc_core_liteethmaccrc32inserter_sink_payload_be >>> 3'd4);
                        main_basesoc_core_liteethmaccrc32inserter_be0_clockdomainsrenamer1_next_value_ce1 = 1'd1;
                    end else begin
                        main_basesoc_core_liteethmaccrc32inserter_be0_clockdomainsrenamer1_next_value1 = main_basesoc_core_liteethmaccrc32inserter_sink_payload_be;
                        main_basesoc_core_liteethmaccrc32inserter_be0_clockdomainsrenamer1_next_value_ce1 = 1'd1;
                    end
                    builder_clockdomainsrenamer_txdatapath_bufferizeendpoints_next_state = 2'd2;
                end
            end
        end
        2'd2: begin
            main_basesoc_core_liteethmaccrc32inserter_source_valid = 1'd1;
            main_basesoc_core_liteethmaccrc32inserter_source_payload_be = 1'd1;
            case (main_basesoc_core_liteethmaccrc32inserter_cnt)
                1'd0: begin
                    main_basesoc_core_liteethmaccrc32inserter_source_payload_data = main_basesoc_core_liteethmaccrc32inserter_crc_packet[31:24];
                end
                1'd1: begin
                    main_basesoc_core_liteethmaccrc32inserter_source_payload_data = main_basesoc_core_liteethmaccrc32inserter_crc_packet[23:16];
                end
                2'd2: begin
                    main_basesoc_core_liteethmaccrc32inserter_source_payload_data = main_basesoc_core_liteethmaccrc32inserter_crc_packet[15:8];
                end
                default: begin
                    main_basesoc_core_liteethmaccrc32inserter_source_payload_data = main_basesoc_core_liteethmaccrc32inserter_crc_packet[7:0];
                end
            endcase
            if (main_basesoc_core_liteethmaccrc32inserter_cnt_done) begin
                main_basesoc_core_liteethmaccrc32inserter_source_last = 1'd1;
                if (main_basesoc_core_liteethmaccrc32inserter_source_ready) begin
                    builder_clockdomainsrenamer_txdatapath_bufferizeendpoints_next_state = 1'd0;
                end
            end
            main_basesoc_core_liteethmaccrc32inserter_is_ongoing1 = 1'd1;
        end
        default: begin
            main_basesoc_core_liteethmaccrc32inserter_reset = 1'd1;
            main_basesoc_core_liteethmaccrc32inserter_sink_ready = 1'd1;
            if (main_basesoc_core_liteethmaccrc32inserter_sink_valid) begin
                main_basesoc_core_liteethmaccrc32inserter_sink_ready = 1'd0;
                builder_clockdomainsrenamer_txdatapath_bufferizeendpoints_next_state = 1'd1;
            end
            main_basesoc_core_liteethmaccrc32inserter_is_ongoing0 = 1'd1;
        end
    endcase
end
assign main_basesoc_core_pipe_valid_sink_ready = ((~main_basesoc_core_pipe_valid_source_valid) | main_basesoc_core_pipe_valid_source_ready);
assign main_basesoc_core_pipe_valid_sink_valid = main_basesoc_core_sink_sink_valid;
assign main_basesoc_core_sink_sink_ready = main_basesoc_core_pipe_valid_sink_ready;
assign main_basesoc_core_pipe_valid_sink_first = main_basesoc_core_sink_sink_first;
assign main_basesoc_core_pipe_valid_sink_last = main_basesoc_core_sink_sink_last;
assign main_basesoc_core_pipe_valid_sink_payload_data = main_basesoc_core_sink_sink_payload_data;
assign main_basesoc_core_pipe_valid_sink_payload_be = main_basesoc_core_sink_sink_payload_be;
assign main_basesoc_core_pipe_valid_sink_payload_error = main_basesoc_core_sink_sink_payload_error;
assign main_basesoc_core_source_source_valid = main_basesoc_core_pipe_valid_source_valid;
assign main_basesoc_core_pipe_valid_source_ready = main_basesoc_core_source_source_ready;
assign main_basesoc_core_source_source_first = main_basesoc_core_pipe_valid_source_first;
assign main_basesoc_core_source_source_last = main_basesoc_core_pipe_valid_source_last;
assign main_basesoc_core_source_source_payload_data = main_basesoc_core_pipe_valid_source_payload_data;
assign main_basesoc_core_source_source_payload_be = main_basesoc_core_pipe_valid_source_payload_be;
assign main_basesoc_core_source_source_payload_error = main_basesoc_core_pipe_valid_source_payload_error;
always @(*) begin
    builder_clockdomainsrenamer_txdatapath_liteethmacpreambleinserter_next_state = 2'd0;
    main_basesoc_core_tx_preamble_count_clockdomainsrenamer2_next_value = 3'd0;
    main_basesoc_core_tx_preamble_count_clockdomainsrenamer2_next_value_ce = 1'd0;
    main_basesoc_core_tx_preamble_sink_ready = 1'd0;
    main_basesoc_core_tx_preamble_source_first = 1'd0;
    main_basesoc_core_tx_preamble_source_last = 1'd0;
    main_basesoc_core_tx_preamble_source_payload_be = 1'd0;
    main_basesoc_core_tx_preamble_source_payload_data = 8'd0;
    main_basesoc_core_tx_preamble_source_payload_error = 1'd0;
    main_basesoc_core_tx_preamble_source_valid = 1'd0;
    main_basesoc_core_tx_preamble_source_payload_data = main_basesoc_core_tx_preamble_sink_payload_data;
    main_basesoc_core_tx_preamble_source_payload_be = main_basesoc_core_tx_preamble_sink_payload_be;
    builder_clockdomainsrenamer_txdatapath_liteethmacpreambleinserter_next_state = builder_clockdomainsrenamer_txdatapath_liteethmacpreambleinserter_state;
    case (builder_clockdomainsrenamer_txdatapath_liteethmacpreambleinserter_state)
        1'd1: begin
            main_basesoc_core_tx_preamble_source_valid = 1'd1;
            main_basesoc_core_tx_preamble_source_payload_be = 1'd1;
            case (main_basesoc_core_tx_preamble_count)
                1'd0: begin
                    main_basesoc_core_tx_preamble_source_payload_data = main_basesoc_core_tx_preamble_preamble[7:0];
                end
                1'd1: begin
                    main_basesoc_core_tx_preamble_source_payload_data = main_basesoc_core_tx_preamble_preamble[15:8];
                end
                2'd2: begin
                    main_basesoc_core_tx_preamble_source_payload_data = main_basesoc_core_tx_preamble_preamble[23:16];
                end
                2'd3: begin
                    main_basesoc_core_tx_preamble_source_payload_data = main_basesoc_core_tx_preamble_preamble[31:24];
                end
                3'd4: begin
                    main_basesoc_core_tx_preamble_source_payload_data = main_basesoc_core_tx_preamble_preamble[39:32];
                end
                3'd5: begin
                    main_basesoc_core_tx_preamble_source_payload_data = main_basesoc_core_tx_preamble_preamble[47:40];
                end
                3'd6: begin
                    main_basesoc_core_tx_preamble_source_payload_data = main_basesoc_core_tx_preamble_preamble[55:48];
                end
                default: begin
                    main_basesoc_core_tx_preamble_source_payload_data = main_basesoc_core_tx_preamble_preamble[63:56];
                end
            endcase
            if (main_basesoc_core_tx_preamble_source_ready) begin
                if ((main_basesoc_core_tx_preamble_count == 3'd7)) begin
                    builder_clockdomainsrenamer_txdatapath_liteethmacpreambleinserter_next_state = 2'd2;
                end else begin
                    main_basesoc_core_tx_preamble_count_clockdomainsrenamer2_next_value = (main_basesoc_core_tx_preamble_count + 1'd1);
                    main_basesoc_core_tx_preamble_count_clockdomainsrenamer2_next_value_ce = 1'd1;
                end
            end
        end
        2'd2: begin
            main_basesoc_core_tx_preamble_source_valid = main_basesoc_core_tx_preamble_sink_valid;
            main_basesoc_core_tx_preamble_sink_ready = main_basesoc_core_tx_preamble_source_ready;
            main_basesoc_core_tx_preamble_source_first = main_basesoc_core_tx_preamble_sink_first;
            main_basesoc_core_tx_preamble_source_last = main_basesoc_core_tx_preamble_sink_last;
            main_basesoc_core_tx_preamble_source_payload_error = main_basesoc_core_tx_preamble_sink_payload_error;
            if (((main_basesoc_core_tx_preamble_sink_valid & main_basesoc_core_tx_preamble_sink_last) & main_basesoc_core_tx_preamble_source_ready)) begin
                builder_clockdomainsrenamer_txdatapath_liteethmacpreambleinserter_next_state = 1'd0;
            end
        end
        default: begin
            main_basesoc_core_tx_preamble_sink_ready = 1'd1;
            main_basesoc_core_tx_preamble_count_clockdomainsrenamer2_next_value = 1'd0;
            main_basesoc_core_tx_preamble_count_clockdomainsrenamer2_next_value_ce = 1'd1;
            if (main_basesoc_core_tx_preamble_sink_valid) begin
                main_basesoc_core_tx_preamble_sink_ready = 1'd0;
                builder_clockdomainsrenamer_txdatapath_liteethmacpreambleinserter_next_state = 1'd1;
            end
        end
    endcase
end
always @(*) begin
    builder_clockdomainsrenamer_txdatapath_liteethmacgap_next_state = 1'd0;
    main_basesoc_core_tx_gap_counter_clockdomainsrenamer3_next_value = 4'd0;
    main_basesoc_core_tx_gap_counter_clockdomainsrenamer3_next_value_ce = 1'd0;
    main_basesoc_core_tx_gap_sink_ready = 1'd0;
    main_basesoc_core_tx_gap_source_first = 1'd0;
    main_basesoc_core_tx_gap_source_last = 1'd0;
    main_basesoc_core_tx_gap_source_payload_be = 1'd0;
    main_basesoc_core_tx_gap_source_payload_data = 8'd0;
    main_basesoc_core_tx_gap_source_payload_error = 1'd0;
    main_basesoc_core_tx_gap_source_valid = 1'd0;
    case (builder_clockdomainsrenamer_txdatapath_liteethmacgap_state)
        1'd1: begin
        end
        default: begin
            main_basesoc_core_tx_gap_sink_ready = main_basesoc_core_tx_gap_source_ready;
        end
    endcase
    builder_clockdomainsrenamer_txdatapath_liteethmacgap_next_state = builder_clockdomainsrenamer_txdatapath_liteethmacgap_state;
    case (builder_clockdomainsrenamer_txdatapath_liteethmacgap_state)
        1'd1: begin
            if ((main_basesoc_core_tx_gap_counter == 1'd1)) begin
                builder_clockdomainsrenamer_txdatapath_liteethmacgap_next_state = 1'd0;
            end
        end
        default: begin
            if (((main_basesoc_core_tx_gap_sink_valid & main_basesoc_core_tx_gap_sink_last) & main_basesoc_core_tx_gap_sink_ready)) begin
                builder_clockdomainsrenamer_txdatapath_liteethmacgap_next_state = 1'd1;
            end
        end
    endcase
    case (builder_clockdomainsrenamer_txdatapath_liteethmacgap_state)
        1'd1: begin
            main_basesoc_core_tx_gap_counter_clockdomainsrenamer3_next_value = (main_basesoc_core_tx_gap_counter - 1'd1);
        end
        default: begin
            if (((main_basesoc_core_tx_gap_sink_valid & main_basesoc_core_tx_gap_sink_last) & main_basesoc_core_tx_gap_sink_ready)) begin
                main_basesoc_core_tx_gap_counter_clockdomainsrenamer3_next_value = 4'd12;
            end
        end
    endcase
    case (builder_clockdomainsrenamer_txdatapath_liteethmacgap_state)
        1'd1: begin
            main_basesoc_core_tx_gap_counter_clockdomainsrenamer3_next_value_ce = 1'd1;
        end
        default: begin
            if (((main_basesoc_core_tx_gap_sink_valid & main_basesoc_core_tx_gap_sink_last) & main_basesoc_core_tx_gap_sink_ready)) begin
                main_basesoc_core_tx_gap_counter_clockdomainsrenamer3_next_value_ce = 1'd1;
            end
        end
    endcase
    case (builder_clockdomainsrenamer_txdatapath_liteethmacgap_state)
        1'd1: begin
        end
        default: begin
            main_basesoc_core_tx_gap_source_first = main_basesoc_core_tx_gap_sink_first;
        end
    endcase
    case (builder_clockdomainsrenamer_txdatapath_liteethmacgap_state)
        1'd1: begin
        end
        default: begin
            main_basesoc_core_tx_gap_source_last = main_basesoc_core_tx_gap_sink_last;
        end
    endcase
    case (builder_clockdomainsrenamer_txdatapath_liteethmacgap_state)
        1'd1: begin
        end
        default: begin
            main_basesoc_core_tx_gap_source_payload_be = main_basesoc_core_tx_gap_sink_payload_be;
        end
    endcase
    case (builder_clockdomainsrenamer_txdatapath_liteethmacgap_state)
        1'd1: begin
        end
        default: begin
            main_basesoc_core_tx_gap_source_payload_data = main_basesoc_core_tx_gap_sink_payload_data;
        end
    endcase
    case (builder_clockdomainsrenamer_txdatapath_liteethmacgap_state)
        1'd1: begin
        end
        default: begin
            main_basesoc_core_tx_gap_source_payload_error = main_basesoc_core_tx_gap_sink_payload_error;
        end
    endcase
    case (builder_clockdomainsrenamer_txdatapath_liteethmacgap_state)
        1'd1: begin
        end
        default: begin
            main_basesoc_core_tx_gap_source_valid = main_basesoc_core_tx_gap_sink_valid;
        end
    endcase
end
assign main_basesoc_core_tx_cdc_sink_sink_valid = main_basesoc_core_sink_valid;
assign main_basesoc_core_sink_ready = main_basesoc_core_tx_cdc_sink_sink_ready;
assign main_basesoc_core_tx_cdc_sink_sink_first = main_basesoc_core_sink_first;
assign main_basesoc_core_tx_cdc_sink_sink_last = main_basesoc_core_sink_last;
assign main_basesoc_core_tx_cdc_sink_sink_payload_data = main_basesoc_core_sink_payload_data;
assign main_basesoc_core_tx_cdc_sink_sink_payload_be = main_basesoc_core_sink_payload_be;
assign main_basesoc_core_tx_cdc_sink_sink_payload_error = main_basesoc_core_sink_payload_error;
assign main_basesoc_core_tx_converter_sink_sink_valid = main_basesoc_core_tx_cdc_source_source_valid;
assign main_basesoc_core_tx_cdc_source_source_ready = main_basesoc_core_tx_converter_sink_sink_ready;
assign main_basesoc_core_tx_converter_sink_sink_first = main_basesoc_core_tx_cdc_source_source_first;
assign main_basesoc_core_tx_converter_sink_sink_last = main_basesoc_core_tx_cdc_source_source_last;
assign main_basesoc_core_tx_converter_sink_sink_payload_data = main_basesoc_core_tx_cdc_source_source_payload_data;
assign main_basesoc_core_tx_converter_sink_sink_payload_be = main_basesoc_core_tx_cdc_source_source_payload_be;
assign main_basesoc_core_tx_converter_sink_sink_payload_error = main_basesoc_core_tx_cdc_source_source_payload_error;
assign main_basesoc_core_tx_padding_sink_valid = main_basesoc_core_tx_converter_source_source_valid;
assign main_basesoc_core_tx_converter_source_source_ready = main_basesoc_core_tx_padding_sink_ready;
assign main_basesoc_core_tx_padding_sink_first = main_basesoc_core_tx_converter_source_source_first;
assign main_basesoc_core_tx_padding_sink_last = main_basesoc_core_tx_converter_source_source_last;
assign main_basesoc_core_tx_padding_sink_payload_data = main_basesoc_core_tx_converter_source_source_payload_data;
assign main_basesoc_core_tx_padding_sink_payload_be = main_basesoc_core_tx_converter_source_source_payload_be;
assign main_basesoc_core_tx_padding_sink_payload_error = main_basesoc_core_tx_converter_source_source_payload_error;
assign main_basesoc_core_sink_sink_valid = main_basesoc_core_tx_padding_source_valid;
assign main_basesoc_core_tx_padding_source_ready = main_basesoc_core_sink_sink_ready;
assign main_basesoc_core_sink_sink_first = main_basesoc_core_tx_padding_source_first;
assign main_basesoc_core_sink_sink_last = main_basesoc_core_tx_padding_source_last;
assign main_basesoc_core_sink_sink_payload_data = main_basesoc_core_tx_padding_source_payload_data;
assign main_basesoc_core_sink_sink_payload_be = main_basesoc_core_tx_padding_source_payload_be;
assign main_basesoc_core_sink_sink_payload_error = main_basesoc_core_tx_padding_source_payload_error;
assign main_basesoc_core_tx_preamble_sink_valid = main_basesoc_core_liteethmaccrc32inserter_source_valid;
assign main_basesoc_core_liteethmaccrc32inserter_source_ready = main_basesoc_core_tx_preamble_sink_ready;
assign main_basesoc_core_tx_preamble_sink_first = main_basesoc_core_liteethmaccrc32inserter_source_first;
assign main_basesoc_core_tx_preamble_sink_last = main_basesoc_core_liteethmaccrc32inserter_source_last;
assign main_basesoc_core_tx_preamble_sink_payload_data = main_basesoc_core_liteethmaccrc32inserter_source_payload_data;
assign main_basesoc_core_tx_preamble_sink_payload_be = main_basesoc_core_liteethmaccrc32inserter_source_payload_be;
assign main_basesoc_core_tx_preamble_sink_payload_error = main_basesoc_core_liteethmaccrc32inserter_source_payload_error;
assign main_basesoc_core_tx_gap_sink_valid = main_basesoc_core_tx_preamble_source_valid;
assign main_basesoc_core_tx_preamble_source_ready = main_basesoc_core_tx_gap_sink_ready;
assign main_basesoc_core_tx_gap_sink_first = main_basesoc_core_tx_preamble_source_first;
assign main_basesoc_core_tx_gap_sink_last = main_basesoc_core_tx_preamble_source_last;
assign main_basesoc_core_tx_gap_sink_payload_data = main_basesoc_core_tx_preamble_source_payload_data;
assign main_basesoc_core_tx_gap_sink_payload_be = main_basesoc_core_tx_preamble_source_payload_be;
assign main_basesoc_core_tx_gap_sink_payload_error = main_basesoc_core_tx_preamble_source_payload_error;
assign main_ethphy_sink_valid = main_basesoc_core_tx_gap_source_valid;
assign main_basesoc_core_tx_gap_source_ready = main_ethphy_sink_ready;
assign main_ethphy_sink_first = main_basesoc_core_tx_gap_source_first;
assign main_ethphy_sink_last = main_basesoc_core_tx_gap_source_last;
assign main_ethphy_sink_payload_data = main_basesoc_core_tx_gap_source_payload_data;
assign main_ethphy_sink_payload_be = main_basesoc_core_tx_gap_source_payload_be;
assign main_ethphy_sink_payload_error = main_basesoc_core_tx_gap_source_payload_error;
assign main_basesoc_core_pulsesynchronizer0_i = main_basesoc_core_rx_preamble_error;
assign main_basesoc_core_pulsesynchronizer1_i = main_basesoc_core_liteethmaccrc32checker_error;
assign main_basesoc_core_rx_preamble_source_payload_data = main_basesoc_core_rx_preamble_sink_payload_data;
assign main_basesoc_core_rx_preamble_source_payload_be = main_basesoc_core_rx_preamble_sink_payload_be;
always @(*) begin
    builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_next_state = 1'd0;
    main_basesoc_core_rx_preamble_error = 1'd0;
    main_basesoc_core_rx_preamble_sink_ready = 1'd0;
    main_basesoc_core_rx_preamble_source_first = 1'd0;
    main_basesoc_core_rx_preamble_source_last = 1'd0;
    main_basesoc_core_rx_preamble_source_payload_error = 1'd0;
    main_basesoc_core_rx_preamble_source_valid = 1'd0;
    case (builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_state)
        1'd1: begin
        end
        default: begin
            if ((main_basesoc_core_rx_preamble_sink_valid & main_basesoc_core_rx_preamble_sink_last)) begin
                main_basesoc_core_rx_preamble_error = 1'd1;
            end
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_state)
        1'd1: begin
            main_basesoc_core_rx_preamble_sink_ready = main_basesoc_core_rx_preamble_source_ready;
        end
        default: begin
            main_basesoc_core_rx_preamble_sink_ready = 1'd1;
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_state)
        1'd1: begin
            main_basesoc_core_rx_preamble_source_first = main_basesoc_core_rx_preamble_sink_first;
        end
        default: begin
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_state)
        1'd1: begin
            main_basesoc_core_rx_preamble_source_last = main_basesoc_core_rx_preamble_sink_last;
        end
        default: begin
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_state)
        1'd1: begin
            main_basesoc_core_rx_preamble_source_payload_error = main_basesoc_core_rx_preamble_sink_payload_error;
        end
        default: begin
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_state)
        1'd1: begin
            main_basesoc_core_rx_preamble_source_valid = main_basesoc_core_rx_preamble_sink_valid;
        end
        default: begin
        end
    endcase
    builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_next_state = builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_state;
    case (builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_state)
        1'd1: begin
            if (((main_basesoc_core_rx_preamble_source_valid & main_basesoc_core_rx_preamble_source_last) & main_basesoc_core_rx_preamble_source_ready)) begin
                builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_next_state = 1'd0;
            end
        end
        default: begin
            if (((main_basesoc_core_rx_preamble_sink_valid & (~main_basesoc_core_rx_preamble_sink_last)) & (main_basesoc_core_rx_preamble_sink_payload_data == main_basesoc_core_rx_preamble_preamble[63:56]))) begin
                builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_next_state = 1'd1;
            end
        end
    endcase
end
assign main_basesoc_core_pulsesynchronizer0_o = (main_basesoc_core_pulsesynchronizer0_toggle_o ^ main_basesoc_core_pulsesynchronizer0_toggle_o_r);
assign main_basesoc_core_liteethmaccrc32checker_fifo_full = (main_basesoc_core_liteethmaccrc32checker_syncfifo_level == 3'd4);
assign main_basesoc_core_liteethmaccrc32checker_fifo_out = (main_basesoc_core_liteethmaccrc32checker_source_source_valid & main_basesoc_core_liteethmaccrc32checker_source_source_ready);
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_first = main_basesoc_core_liteethmaccrc32checker_sink_sink_first;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_last = main_basesoc_core_liteethmaccrc32checker_sink_sink_last;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_payload_data = main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_data;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_payload_be = main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_be;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_payload_error = main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_error;
always @(*) begin
    main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_valid = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_valid = main_basesoc_core_liteethmaccrc32checker_sink_sink_valid;
    main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_valid = main_basesoc_core_liteethmaccrc32checker_fifo_in;
end
always @(*) begin
    main_basesoc_core_liteethmaccrc32checker_sink_sink_ready = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_sink_sink_ready = main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_ready;
    main_basesoc_core_liteethmaccrc32checker_sink_sink_ready = main_basesoc_core_liteethmaccrc32checker_fifo_in;
end
assign main_basesoc_core_liteethmaccrc32checker_fifo_in = (((main_basesoc_core_liteethmaccrc32checker_sink_sink_valid & ((~main_basesoc_core_liteethmaccrc32checker_fifo_full) | main_basesoc_core_liteethmaccrc32checker_fifo_out)) & (~main_basesoc_core_liteethmaccrc32checker_is_ongoing0)) & (~main_basesoc_core_liteethmaccrc32checker_is_ongoing1));
assign main_basesoc_core_liteethmaccrc32checker_crc_data0 = main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_data;
assign main_basesoc_core_liteethmaccrc32checker_crc_be = main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_be;
assign main_basesoc_core_liteethmaccrc32checker_last_word_error = ((main_basesoc_core_liteethmaccrc32checker_crc_error | main_basesoc_core_liteethmaccrc32checker_packet_error) | ((main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_error & main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_be) != 1'd0));
assign main_basesoc_core_liteethmaccrc32checker_source_source_first = main_basesoc_core_liteethmaccrc32checker_syncfifo_source_first;
assign main_basesoc_core_liteethmaccrc32checker_source_source_payload_data = main_basesoc_core_liteethmaccrc32checker_syncfifo_source_payload_data;
assign main_basesoc_core_liteethmaccrc32checker_sink_sink_valid = main_basesoc_core_bufferizeendpoints_source_source_valid;
assign main_basesoc_core_bufferizeendpoints_source_source_ready = main_basesoc_core_liteethmaccrc32checker_sink_sink_ready;
assign main_basesoc_core_liteethmaccrc32checker_sink_sink_first = main_basesoc_core_bufferizeendpoints_source_source_first;
assign main_basesoc_core_liteethmaccrc32checker_sink_sink_last = main_basesoc_core_bufferizeendpoints_source_source_last;
assign main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_data = main_basesoc_core_bufferizeendpoints_source_source_payload_data;
assign main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_be = main_basesoc_core_bufferizeendpoints_source_source_payload_be;
assign main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_error = main_basesoc_core_bufferizeendpoints_source_source_payload_error;
assign main_basesoc_core_liteethmaccrc32checker_crc_crc_prev = main_basesoc_core_liteethmaccrc32checker_crc_reg;
always @(*) begin
    main_basesoc_core_liteethmaccrc32checker_crc_data1 = 8'd0;
    main_basesoc_core_liteethmaccrc32checker_crc_error = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_crc_data1 = main_basesoc_core_liteethmaccrc32checker_crc_data0;
    if (main_basesoc_core_liteethmaccrc32checker_crc_be) begin
        main_basesoc_core_liteethmaccrc32checker_crc_data1 = (main_basesoc_core_liteethmaccrc32checker_crc_data0 & 8'hff);
        main_basesoc_core_liteethmaccrc32checker_crc_error = (main_basesoc_core_liteethmaccrc32checker_crc_crc_next != 32'd3338984827);
    end
end
always @(*) begin
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next = 32'd0;
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[0] = (((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[24] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[1]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[7]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[1] = (((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[25] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[0]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[6]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[1]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[7]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[2] = (((((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[26] ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[5]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[0]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[6]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[1]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[7]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[3] = (((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[27] ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[4]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[5]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[0]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[6]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[4] = (((((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[28] ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[3]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[4]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[5]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[1]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[7]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[5] = (((((((((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[29] ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[2]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[3]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[4]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[0]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[6]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[1]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[7]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[6] = (((((((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[30] ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[1]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[2]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[3]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[5]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[0]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[6]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[7] = (((((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[31] ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[0]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[2]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[4]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[5]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[7]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[8] = ((((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[0] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[3]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[4]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[6]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[7]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[9] = ((((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[1] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[2]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[3]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[5]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[6]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[10] = ((((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[2] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[2]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[4]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[5]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[7]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[11] = ((((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[3] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[3]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[4]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[6]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[7]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[12] = ((((((((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[4] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[2]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[3]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[5]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[6]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[1]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[7]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[13] = ((((((((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[5] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[1]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[2]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[4]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[5]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[0]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[6]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[14] = ((((((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[6] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[0]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[1]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[3]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[4]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[5]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[15] = ((((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[7] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[0]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[2]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[3]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[4]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[16] = ((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[8] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[2]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[3]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[7]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[17] = ((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[9] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[1]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[2]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[6]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[18] = ((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[10] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[0]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[1]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[5]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[19] = ((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[11] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[0]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[4]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[20] = ((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[12] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[3]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[21] = ((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[13] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[2]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[22] = ((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[14] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[7]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[23] = ((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[15] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[6]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[1]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[7]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[24] = ((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[16] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[5]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[0]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[6]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[25] = ((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[17] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[4]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[5]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[26] = ((((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[18] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[3]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[4]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[24]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[1]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[7]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[27] = ((((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[19] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[2]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[3]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[25]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[0]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[6]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[28] = ((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[20] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[1]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[2]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[26]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[5]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[29] = ((((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[21] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[0]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[30]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[1]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[27]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[4]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[30] = ((((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[22] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[31]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[0]) ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[28]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[3]);
    main_basesoc_core_liteethmaccrc32checker_crc_crc_next[31] = ((main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[23] ^ main_basesoc_core_liteethmaccrc32checker_crc_crc_prev[29]) ^ main_basesoc_core_liteethmaccrc32checker_crc_data1[2]);
end
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_din = {main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_in_last, main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_in_first, main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_in_payload_error, main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_in_payload_be, main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_in_payload_data};
assign {main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_out_last, main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_out_first, main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_out_payload_error, main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_out_payload_be, main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_out_payload_data} = main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_dout;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_ready = main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_writable;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_we = main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_valid;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_in_first = main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_first;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_in_last = main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_last;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_in_payload_data = main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_payload_data;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_in_payload_be = main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_payload_be;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_in_payload_error = main_basesoc_core_liteethmaccrc32checker_syncfifo_sink_payload_error;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_source_valid = main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_readable;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_source_first = main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_out_first;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_source_last = main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_out_last;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_source_payload_data = main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_out_payload_data;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_source_payload_be = main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_out_payload_be;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_source_payload_error = main_basesoc_core_liteethmaccrc32checker_syncfifo_fifo_out_payload_error;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_re = main_basesoc_core_liteethmaccrc32checker_syncfifo_source_ready;
always @(*) begin
    main_basesoc_core_liteethmaccrc32checker_syncfifo_wrport_adr = 3'd0;
    if (main_basesoc_core_liteethmaccrc32checker_syncfifo_replace) begin
        main_basesoc_core_liteethmaccrc32checker_syncfifo_wrport_adr = (main_basesoc_core_liteethmaccrc32checker_syncfifo_produce - 1'd1);
    end else begin
        main_basesoc_core_liteethmaccrc32checker_syncfifo_wrport_adr = main_basesoc_core_liteethmaccrc32checker_syncfifo_produce;
    end
end
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_wrport_dat_w = main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_din;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_wrport_we = (main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_we & (main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_writable | main_basesoc_core_liteethmaccrc32checker_syncfifo_replace));
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_do_read = (main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_readable & main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_re);
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_rdport_adr = main_basesoc_core_liteethmaccrc32checker_syncfifo_consume;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_dout = main_basesoc_core_liteethmaccrc32checker_syncfifo_rdport_dat_r;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_writable = (main_basesoc_core_liteethmaccrc32checker_syncfifo_level != 3'd5);
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_readable = (main_basesoc_core_liteethmaccrc32checker_syncfifo_level != 1'd0);
always @(*) begin
    builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_next_state = 2'd0;
    main_basesoc_core_liteethmaccrc32checker_be_next_value0 = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_be_next_value_ce0 = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_crc_ce = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_crc_reset = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_error = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_fifo_reset = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_is_ongoing0 = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_is_ongoing1 = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_is_ongoing2 = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_last_error_next_value1 = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_last_error_next_value_ce1 = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_source_source_last = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_source_source_payload_be = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_source_source_payload_error = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_source_source_valid = 1'd0;
    main_basesoc_core_liteethmaccrc32checker_syncfifo_source_ready = 1'd0;
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
        end
        2'd2: begin
        end
        2'd3: begin
            if (1'd1) begin
            end else begin
                if ((main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_be <= 4'd15)) begin
                end else begin
                    main_basesoc_core_liteethmaccrc32checker_be_next_value0 = (main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_be >>> 3'd4);
                end
            end
        end
        default: begin
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
        end
        2'd2: begin
        end
        2'd3: begin
            if (1'd1) begin
            end else begin
                if ((main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_be <= 4'd15)) begin
                end else begin
                    main_basesoc_core_liteethmaccrc32checker_be_next_value_ce0 = 1'd1;
                end
            end
        end
        default: begin
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
        end
        2'd2: begin
            if ((main_basesoc_core_liteethmaccrc32checker_sink_sink_valid & main_basesoc_core_liteethmaccrc32checker_sink_sink_ready)) begin
                main_basesoc_core_liteethmaccrc32checker_crc_ce = 1'd1;
            end
        end
        2'd3: begin
            if ((main_basesoc_core_liteethmaccrc32checker_sink_sink_valid & main_basesoc_core_liteethmaccrc32checker_sink_sink_ready)) begin
                main_basesoc_core_liteethmaccrc32checker_crc_ce = 1'd1;
            end
        end
        default: begin
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
        end
        2'd2: begin
        end
        2'd3: begin
        end
        default: begin
            main_basesoc_core_liteethmaccrc32checker_crc_reset = 1'd1;
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
        end
        2'd2: begin
        end
        2'd3: begin
            main_basesoc_core_liteethmaccrc32checker_error = ((main_basesoc_core_liteethmaccrc32checker_sink_sink_valid & main_basesoc_core_liteethmaccrc32checker_sink_sink_last) & main_basesoc_core_liteethmaccrc32checker_crc_error);
        end
        default: begin
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
        end
        2'd2: begin
        end
        2'd3: begin
        end
        default: begin
            main_basesoc_core_liteethmaccrc32checker_fifo_reset = 1'd1;
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
        end
        2'd2: begin
        end
        2'd3: begin
        end
        default: begin
            main_basesoc_core_liteethmaccrc32checker_is_ongoing0 = 1'd1;
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
            main_basesoc_core_liteethmaccrc32checker_is_ongoing1 = 1'd1;
        end
        2'd2: begin
        end
        2'd3: begin
        end
        default: begin
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
        end
        2'd2: begin
        end
        2'd3: begin
        end
        default: begin
            main_basesoc_core_liteethmaccrc32checker_is_ongoing2 = 1'd1;
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
        end
        2'd2: begin
        end
        2'd3: begin
            if (1'd1) begin
            end else begin
                if ((main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_be <= 4'd15)) begin
                end else begin
                    main_basesoc_core_liteethmaccrc32checker_last_error_next_value1 = main_basesoc_core_liteethmaccrc32checker_last_word_error;
                end
            end
        end
        default: begin
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
        end
        2'd2: begin
        end
        2'd3: begin
            if (1'd1) begin
            end else begin
                if ((main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_be <= 4'd15)) begin
                end else begin
                    main_basesoc_core_liteethmaccrc32checker_last_error_next_value_ce1 = 1'd1;
                end
            end
        end
        default: begin
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
            main_basesoc_core_liteethmaccrc32checker_source_source_last = main_basesoc_core_liteethmaccrc32checker_syncfifo_source_last;
        end
        2'd2: begin
        end
        2'd3: begin
            if (1'd1) begin
                main_basesoc_core_liteethmaccrc32checker_source_source_last = main_basesoc_core_liteethmaccrc32checker_sink_sink_last;
            end else begin
                if ((main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_be <= 4'd15)) begin
                    main_basesoc_core_liteethmaccrc32checker_source_source_last = main_basesoc_core_liteethmaccrc32checker_sink_sink_last;
                end else begin
                end
            end
        end
        default: begin
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
            main_basesoc_core_liteethmaccrc32checker_source_source_payload_be = main_basesoc_core_liteethmaccrc32checker_be;
        end
        2'd2: begin
        end
        2'd3: begin
            main_basesoc_core_liteethmaccrc32checker_source_source_payload_be = 1'd1;
            if (1'd1) begin
                if (main_basesoc_core_liteethmaccrc32checker_sink_sink_last) begin
                    main_basesoc_core_liteethmaccrc32checker_source_source_payload_be = main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_be;
                end
            end else begin
                if ((main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_be <= 4'd15)) begin
                    main_basesoc_core_liteethmaccrc32checker_source_source_payload_be = ((main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_be <<< 3'd4) | 4'd15);
                end else begin
                end
            end
        end
        default: begin
        end
    endcase
    main_basesoc_core_liteethmaccrc32checker_source_source_payload_error = main_basesoc_core_liteethmaccrc32checker_syncfifo_source_payload_error;
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
            main_basesoc_core_liteethmaccrc32checker_source_source_payload_error = (main_basesoc_core_liteethmaccrc32checker_syncfifo_source_payload_error | {1{main_basesoc_core_liteethmaccrc32checker_last_error}});
        end
        2'd2: begin
        end
        2'd3: begin
            main_basesoc_core_liteethmaccrc32checker_source_source_payload_error = (main_basesoc_core_liteethmaccrc32checker_sink_sink_last ? {1{main_basesoc_core_liteethmaccrc32checker_last_word_error}} : main_basesoc_core_liteethmaccrc32checker_syncfifo_source_payload_error);
        end
        default: begin
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
            main_basesoc_core_liteethmaccrc32checker_source_source_valid = main_basesoc_core_liteethmaccrc32checker_syncfifo_source_valid;
        end
        2'd2: begin
        end
        2'd3: begin
            main_basesoc_core_liteethmaccrc32checker_source_source_valid = (main_basesoc_core_liteethmaccrc32checker_sink_sink_valid & main_basesoc_core_liteethmaccrc32checker_fifo_full);
        end
        default: begin
        end
    endcase
    builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_next_state = builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state;
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
            if ((main_basesoc_core_liteethmaccrc32checker_source_source_valid & main_basesoc_core_liteethmaccrc32checker_source_source_ready)) begin
                builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_next_state = 1'd0;
            end
        end
        2'd2: begin
            if ((main_basesoc_core_liteethmaccrc32checker_sink_sink_valid & main_basesoc_core_liteethmaccrc32checker_sink_sink_ready)) begin
                builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_next_state = 2'd3;
            end
        end
        2'd3: begin
            if ((main_basesoc_core_liteethmaccrc32checker_sink_sink_valid & main_basesoc_core_liteethmaccrc32checker_sink_sink_ready)) begin
                if ((main_basesoc_core_liteethmaccrc32checker_sink_sink_last & (main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_be > 4'd15))) begin
                    builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_next_state = 1'd1;
                end else begin
                    if (main_basesoc_core_liteethmaccrc32checker_sink_sink_last) begin
                        builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_next_state = 1'd0;
                    end
                end
            end
        end
        default: begin
            builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_next_state = 2'd2;
        end
    endcase
    case (builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state)
        1'd1: begin
            main_basesoc_core_liteethmaccrc32checker_syncfifo_source_ready = main_basesoc_core_liteethmaccrc32checker_source_source_ready;
        end
        2'd2: begin
        end
        2'd3: begin
            main_basesoc_core_liteethmaccrc32checker_syncfifo_source_ready = main_basesoc_core_liteethmaccrc32checker_fifo_out;
        end
        default: begin
        end
    endcase
end
assign main_basesoc_core_bufferizeendpoints_pipe_valid_sink_ready = ((~main_basesoc_core_bufferizeendpoints_pipe_valid_source_valid) | main_basesoc_core_bufferizeendpoints_pipe_valid_source_ready);
assign main_basesoc_core_bufferizeendpoints_pipe_valid_sink_valid = main_basesoc_core_bufferizeendpoints_sink_sink_valid;
assign main_basesoc_core_bufferizeendpoints_sink_sink_ready = main_basesoc_core_bufferizeendpoints_pipe_valid_sink_ready;
assign main_basesoc_core_bufferizeendpoints_pipe_valid_sink_first = main_basesoc_core_bufferizeendpoints_sink_sink_first;
assign main_basesoc_core_bufferizeendpoints_pipe_valid_sink_last = main_basesoc_core_bufferizeendpoints_sink_sink_last;
assign main_basesoc_core_bufferizeendpoints_pipe_valid_sink_payload_data = main_basesoc_core_bufferizeendpoints_sink_sink_payload_data;
assign main_basesoc_core_bufferizeendpoints_pipe_valid_sink_payload_be = main_basesoc_core_bufferizeendpoints_sink_sink_payload_be;
assign main_basesoc_core_bufferizeendpoints_pipe_valid_sink_payload_error = main_basesoc_core_bufferizeendpoints_sink_sink_payload_error;
assign main_basesoc_core_bufferizeendpoints_source_source_valid = main_basesoc_core_bufferizeendpoints_pipe_valid_source_valid;
assign main_basesoc_core_bufferizeendpoints_pipe_valid_source_ready = main_basesoc_core_bufferizeendpoints_source_source_ready;
assign main_basesoc_core_bufferizeendpoints_source_source_first = main_basesoc_core_bufferizeendpoints_pipe_valid_source_first;
assign main_basesoc_core_bufferizeendpoints_source_source_last = main_basesoc_core_bufferizeendpoints_pipe_valid_source_last;
assign main_basesoc_core_bufferizeendpoints_source_source_payload_data = main_basesoc_core_bufferizeendpoints_pipe_valid_source_payload_data;
assign main_basesoc_core_bufferizeendpoints_source_source_payload_be = main_basesoc_core_bufferizeendpoints_pipe_valid_source_payload_be;
assign main_basesoc_core_bufferizeendpoints_source_source_payload_error = main_basesoc_core_bufferizeendpoints_pipe_valid_source_payload_error;
assign main_basesoc_core_pulsesynchronizer1_o = (main_basesoc_core_pulsesynchronizer1_toggle_o ^ main_basesoc_core_pulsesynchronizer1_toggle_o_r);
assign main_basesoc_core_rx_padding_length_inc = (1'd0 + main_basesoc_core_rx_padding_sink_payload_be);
assign main_basesoc_core_rx_padding_source_valid = main_basesoc_core_rx_padding_sink_valid;
assign main_basesoc_core_rx_padding_sink_ready = main_basesoc_core_rx_padding_source_ready;
assign main_basesoc_core_rx_padding_source_first = main_basesoc_core_rx_padding_sink_first;
assign main_basesoc_core_rx_padding_source_last = main_basesoc_core_rx_padding_sink_last;
assign main_basesoc_core_rx_padding_source_payload_data = main_basesoc_core_rx_padding_sink_payload_data;
assign main_basesoc_core_rx_padding_source_payload_be = main_basesoc_core_rx_padding_sink_payload_be;
always @(*) begin
    main_basesoc_core_rx_padding_source_payload_error = 1'd0;
    if (((main_basesoc_core_rx_padding_sink_valid & main_basesoc_core_rx_padding_sink_last) & ((((main_basesoc_core_rx_padding_length + main_basesoc_core_rx_padding_length_inc) + 12'd0)) < 6'd60))) begin
        main_basesoc_core_rx_padding_source_payload_error = {1{1'd1}};
    end else begin
        main_basesoc_core_rx_padding_source_payload_error = main_basesoc_core_rx_padding_sink_payload_error;
    end
end
assign main_basesoc_core_rx_converter_converter_sink_valid = main_basesoc_core_rx_converter_sink_sink_valid;
assign main_basesoc_core_rx_converter_converter_sink_first = main_basesoc_core_rx_converter_sink_sink_first;
assign main_basesoc_core_rx_converter_converter_sink_last = main_basesoc_core_rx_converter_sink_sink_last;
assign main_basesoc_core_rx_converter_sink_sink_ready = main_basesoc_core_rx_converter_converter_sink_ready;
assign main_basesoc_core_rx_converter_converter_sink_payload_data = {main_basesoc_core_rx_converter_sink_sink_payload_error, main_basesoc_core_rx_converter_sink_sink_payload_be, main_basesoc_core_rx_converter_sink_sink_payload_data};
assign main_basesoc_core_rx_converter_source_source_valid = main_basesoc_core_rx_converter_converter_source_valid;
assign main_basesoc_core_rx_converter_source_source_first = main_basesoc_core_rx_converter_converter_source_first;
assign main_basesoc_core_rx_converter_source_source_last = main_basesoc_core_rx_converter_converter_source_last;
assign main_basesoc_core_rx_converter_converter_source_ready = main_basesoc_core_rx_converter_source_source_ready;
always @(*) begin
    main_basesoc_core_rx_converter_source_source_payload_data = 32'd0;
    main_basesoc_core_rx_converter_source_source_payload_data[7:0] = main_basesoc_core_rx_converter_converter_source_payload_data[7:0];
    main_basesoc_core_rx_converter_source_source_payload_data[15:8] = main_basesoc_core_rx_converter_converter_source_payload_data[17:10];
    main_basesoc_core_rx_converter_source_source_payload_data[23:16] = main_basesoc_core_rx_converter_converter_source_payload_data[27:20];
    main_basesoc_core_rx_converter_source_source_payload_data[31:24] = main_basesoc_core_rx_converter_converter_source_payload_data[37:30];
end
always @(*) begin
    main_basesoc_core_rx_converter_source_source_payload_be = 4'd0;
    main_basesoc_core_rx_converter_source_source_payload_be[0] = ((main_basesoc_core_rx_converter_converter_source_payload_valid_token_count > 1'd0) ? main_basesoc_core_rx_converter_converter_source_payload_data[8] : 1'd0);
    main_basesoc_core_rx_converter_source_source_payload_be[1] = ((main_basesoc_core_rx_converter_converter_source_payload_valid_token_count > 1'd1) ? main_basesoc_core_rx_converter_converter_source_payload_data[18] : 1'd0);
    main_basesoc_core_rx_converter_source_source_payload_be[2] = ((main_basesoc_core_rx_converter_converter_source_payload_valid_token_count > 2'd2) ? main_basesoc_core_rx_converter_converter_source_payload_data[28] : 1'd0);
    main_basesoc_core_rx_converter_source_source_payload_be[3] = ((main_basesoc_core_rx_converter_converter_source_payload_valid_token_count > 2'd3) ? main_basesoc_core_rx_converter_converter_source_payload_data[38] : 1'd0);
end
always @(*) begin
    main_basesoc_core_rx_converter_source_source_payload_error = 4'd0;
    main_basesoc_core_rx_converter_source_source_payload_error[0] = main_basesoc_core_rx_converter_converter_source_payload_data[9];
    main_basesoc_core_rx_converter_source_source_payload_error[1] = main_basesoc_core_rx_converter_converter_source_payload_data[19];
    main_basesoc_core_rx_converter_source_source_payload_error[2] = main_basesoc_core_rx_converter_converter_source_payload_data[29];
    main_basesoc_core_rx_converter_source_source_payload_error[3] = main_basesoc_core_rx_converter_converter_source_payload_data[39];
end
assign main_basesoc_core_rx_converter_converter_sink_ready = ((~main_basesoc_core_rx_converter_converter_strobe_all) | main_basesoc_core_rx_converter_converter_source_ready);
assign main_basesoc_core_rx_converter_converter_source_valid = main_basesoc_core_rx_converter_converter_strobe_all;
assign main_basesoc_core_rx_converter_converter_load_part = (main_basesoc_core_rx_converter_converter_sink_valid & main_basesoc_core_rx_converter_converter_sink_ready);
assign main_basesoc_core_rx_cdc_write_rst = (eth_rx_rst | main_basesoc_core_rx_cdc_write_ext_rst);
assign main_basesoc_core_rx_cdc_cdc_reset_write = main_basesoc_core_rx_cdc_write_ext_rst;
assign main_basesoc_core_rx_cdc_cdc_reset_read = main_basesoc_core_rx_cdc_ext_rst_to;
assign main_basesoc_core_rx_cdc_cdc_sink_valid = main_basesoc_core_rx_cdc_sink_sink_valid;
assign main_basesoc_core_rx_cdc_sink_sink_ready = main_basesoc_core_rx_cdc_cdc_sink_ready;
assign main_basesoc_core_rx_cdc_cdc_sink_first = main_basesoc_core_rx_cdc_sink_sink_first;
assign main_basesoc_core_rx_cdc_cdc_sink_last = main_basesoc_core_rx_cdc_sink_sink_last;
assign main_basesoc_core_rx_cdc_cdc_sink_payload_data = main_basesoc_core_rx_cdc_sink_sink_payload_data;
assign main_basesoc_core_rx_cdc_cdc_sink_payload_be = main_basesoc_core_rx_cdc_sink_sink_payload_be;
assign main_basesoc_core_rx_cdc_cdc_sink_payload_error = main_basesoc_core_rx_cdc_sink_sink_payload_error;
assign main_basesoc_core_rx_cdc_cdc_source_ready = main_basesoc_core_rx_cdc_source_source_ready;
assign main_basesoc_core_rx_cdc_source_source_first = main_basesoc_core_rx_cdc_cdc_source_first;
assign main_basesoc_core_rx_cdc_source_source_last = main_basesoc_core_rx_cdc_cdc_source_last;
assign main_basesoc_core_rx_cdc_source_source_payload_data = main_basesoc_core_rx_cdc_cdc_source_payload_data;
assign main_basesoc_core_rx_cdc_source_source_payload_be = main_basesoc_core_rx_cdc_cdc_source_payload_be;
assign main_basesoc_core_rx_cdc_source_source_payload_error = main_basesoc_core_rx_cdc_cdc_source_payload_error;
assign main_basesoc_core_rx_cdc_source_source_valid = ((main_basesoc_core_rx_cdc_cdc_source_valid & (~main_basesoc_core_rx_cdc_ext_rst_to)) & (~sys_rst));
assign main_basesoc_core_rx_cdc_cdc_asyncfifo_din = {main_basesoc_core_rx_cdc_cdc_fifo_in_last, main_basesoc_core_rx_cdc_cdc_fifo_in_first, main_basesoc_core_rx_cdc_cdc_fifo_in_payload_error, main_basesoc_core_rx_cdc_cdc_fifo_in_payload_be, main_basesoc_core_rx_cdc_cdc_fifo_in_payload_data};
assign {main_basesoc_core_rx_cdc_cdc_fifo_out_last, main_basesoc_core_rx_cdc_cdc_fifo_out_first, main_basesoc_core_rx_cdc_cdc_fifo_out_payload_error, main_basesoc_core_rx_cdc_cdc_fifo_out_payload_be, main_basesoc_core_rx_cdc_cdc_fifo_out_payload_data} = main_basesoc_core_rx_cdc_cdc_asyncfifo_dout;
assign main_basesoc_core_rx_cdc_cdc_sink_ready = main_basesoc_core_rx_cdc_cdc_asyncfifo_writable;
assign main_basesoc_core_rx_cdc_cdc_asyncfifo_we = main_basesoc_core_rx_cdc_cdc_sink_valid;
assign main_basesoc_core_rx_cdc_cdc_fifo_in_first = main_basesoc_core_rx_cdc_cdc_sink_first;
assign main_basesoc_core_rx_cdc_cdc_fifo_in_last = main_basesoc_core_rx_cdc_cdc_sink_last;
assign main_basesoc_core_rx_cdc_cdc_fifo_in_payload_data = main_basesoc_core_rx_cdc_cdc_sink_payload_data;
assign main_basesoc_core_rx_cdc_cdc_fifo_in_payload_be = main_basesoc_core_rx_cdc_cdc_sink_payload_be;
assign main_basesoc_core_rx_cdc_cdc_fifo_in_payload_error = main_basesoc_core_rx_cdc_cdc_sink_payload_error;
assign main_basesoc_core_rx_cdc_cdc_source_valid = main_basesoc_core_rx_cdc_cdc_asyncfifo_readable;
assign main_basesoc_core_rx_cdc_cdc_source_first = main_basesoc_core_rx_cdc_cdc_fifo_out_first;
assign main_basesoc_core_rx_cdc_cdc_source_last = main_basesoc_core_rx_cdc_cdc_fifo_out_last;
assign main_basesoc_core_rx_cdc_cdc_source_payload_data = main_basesoc_core_rx_cdc_cdc_fifo_out_payload_data;
assign main_basesoc_core_rx_cdc_cdc_source_payload_be = main_basesoc_core_rx_cdc_cdc_fifo_out_payload_be;
assign main_basesoc_core_rx_cdc_cdc_source_payload_error = main_basesoc_core_rx_cdc_cdc_fifo_out_payload_error;
assign main_basesoc_core_rx_cdc_cdc_asyncfifo_re = main_basesoc_core_rx_cdc_cdc_source_ready;
assign main_basesoc_core_rx_cdc_cdc_graycounter0_ce = (main_basesoc_core_rx_cdc_cdc_asyncfifo_writable & main_basesoc_core_rx_cdc_cdc_asyncfifo_we);
assign main_basesoc_core_rx_cdc_cdc_graycounter1_ce = (main_basesoc_core_rx_cdc_cdc_asyncfifo_readable & main_basesoc_core_rx_cdc_cdc_asyncfifo_re);
assign main_basesoc_core_rx_cdc_cdc_asyncfifo_writable = (((main_basesoc_core_rx_cdc_cdc_graycounter0_q[5] == main_basesoc_core_rx_cdc_cdc_consume_wdomain[5]) | (main_basesoc_core_rx_cdc_cdc_graycounter0_q[4] == main_basesoc_core_rx_cdc_cdc_consume_wdomain[4])) | (main_basesoc_core_rx_cdc_cdc_graycounter0_q[3:0] != main_basesoc_core_rx_cdc_cdc_consume_wdomain[3:0]));
assign main_basesoc_core_rx_cdc_cdc_asyncfifo_readable = (main_basesoc_core_rx_cdc_cdc_graycounter1_q != main_basesoc_core_rx_cdc_cdc_produce_rdomain);
assign main_basesoc_core_rx_cdc_cdc_wrport_adr = main_basesoc_core_rx_cdc_cdc_graycounter0_q_binary[4:0];
assign main_basesoc_core_rx_cdc_cdc_wrport_dat_w = main_basesoc_core_rx_cdc_cdc_asyncfifo_din;
assign main_basesoc_core_rx_cdc_cdc_wrport_we = main_basesoc_core_rx_cdc_cdc_graycounter0_ce;
assign main_basesoc_core_rx_cdc_cdc_rdport_adr = main_basesoc_core_rx_cdc_cdc_graycounter1_q_next_binary[4:0];
assign main_basesoc_core_rx_cdc_cdc_asyncfifo_dout = main_basesoc_core_rx_cdc_cdc_rdport_dat_r;
always @(*) begin
    main_basesoc_core_rx_cdc_cdc_graycounter0_q_next_binary = 6'd0;
    if (main_basesoc_core_rx_cdc_cdc_graycounter0_ce) begin
        main_basesoc_core_rx_cdc_cdc_graycounter0_q_next_binary = (main_basesoc_core_rx_cdc_cdc_graycounter0_q_binary + 1'd1);
    end else begin
        main_basesoc_core_rx_cdc_cdc_graycounter0_q_next_binary = main_basesoc_core_rx_cdc_cdc_graycounter0_q_binary;
    end
end
assign main_basesoc_core_rx_cdc_cdc_graycounter0_q_next = (main_basesoc_core_rx_cdc_cdc_graycounter0_q_next_binary ^ main_basesoc_core_rx_cdc_cdc_graycounter0_q_next_binary[5:1]);
always @(*) begin
    main_basesoc_core_rx_cdc_cdc_graycounter1_q_next_binary = 6'd0;
    if (main_basesoc_core_rx_cdc_cdc_graycounter1_ce) begin
        main_basesoc_core_rx_cdc_cdc_graycounter1_q_next_binary = (main_basesoc_core_rx_cdc_cdc_graycounter1_q_binary + 1'd1);
    end else begin
        main_basesoc_core_rx_cdc_cdc_graycounter1_q_next_binary = main_basesoc_core_rx_cdc_cdc_graycounter1_q_binary;
    end
end
assign main_basesoc_core_rx_cdc_cdc_graycounter1_q_next = (main_basesoc_core_rx_cdc_cdc_graycounter1_q_next_binary ^ main_basesoc_core_rx_cdc_cdc_graycounter1_q_next_binary[5:1]);
assign main_basesoc_core_rx_preamble_sink_valid = main_ethphy_source_valid;
assign main_ethphy_source_ready = main_basesoc_core_rx_preamble_sink_ready;
assign main_basesoc_core_rx_preamble_sink_first = main_ethphy_source_first;
assign main_basesoc_core_rx_preamble_sink_last = main_ethphy_source_last;
assign main_basesoc_core_rx_preamble_sink_payload_data = main_ethphy_source_payload_data;
assign main_basesoc_core_rx_preamble_sink_payload_be = main_ethphy_source_payload_be;
assign main_basesoc_core_rx_preamble_sink_payload_error = main_ethphy_source_payload_error;
assign main_basesoc_core_bufferizeendpoints_sink_sink_valid = main_basesoc_core_rx_preamble_source_valid;
assign main_basesoc_core_rx_preamble_source_ready = main_basesoc_core_bufferizeendpoints_sink_sink_ready;
assign main_basesoc_core_bufferizeendpoints_sink_sink_first = main_basesoc_core_rx_preamble_source_first;
assign main_basesoc_core_bufferizeendpoints_sink_sink_last = main_basesoc_core_rx_preamble_source_last;
assign main_basesoc_core_bufferizeendpoints_sink_sink_payload_data = main_basesoc_core_rx_preamble_source_payload_data;
assign main_basesoc_core_bufferizeendpoints_sink_sink_payload_be = main_basesoc_core_rx_preamble_source_payload_be;
assign main_basesoc_core_bufferizeendpoints_sink_sink_payload_error = main_basesoc_core_rx_preamble_source_payload_error;
assign main_basesoc_core_rx_padding_sink_valid = main_basesoc_core_liteethmaccrc32checker_source_source_valid;
assign main_basesoc_core_liteethmaccrc32checker_source_source_ready = main_basesoc_core_rx_padding_sink_ready;
assign main_basesoc_core_rx_padding_sink_first = main_basesoc_core_liteethmaccrc32checker_source_source_first;
assign main_basesoc_core_rx_padding_sink_last = main_basesoc_core_liteethmaccrc32checker_source_source_last;
assign main_basesoc_core_rx_padding_sink_payload_data = main_basesoc_core_liteethmaccrc32checker_source_source_payload_data;
assign main_basesoc_core_rx_padding_sink_payload_be = main_basesoc_core_liteethmaccrc32checker_source_source_payload_be;
assign main_basesoc_core_rx_padding_sink_payload_error = main_basesoc_core_liteethmaccrc32checker_source_source_payload_error;
assign main_basesoc_core_rx_converter_sink_sink_valid = main_basesoc_core_rx_padding_source_valid;
assign main_basesoc_core_rx_padding_source_ready = main_basesoc_core_rx_converter_sink_sink_ready;
assign main_basesoc_core_rx_converter_sink_sink_first = main_basesoc_core_rx_padding_source_first;
assign main_basesoc_core_rx_converter_sink_sink_last = main_basesoc_core_rx_padding_source_last;
assign main_basesoc_core_rx_converter_sink_sink_payload_data = main_basesoc_core_rx_padding_source_payload_data;
assign main_basesoc_core_rx_converter_sink_sink_payload_be = main_basesoc_core_rx_padding_source_payload_be;
assign main_basesoc_core_rx_converter_sink_sink_payload_error = main_basesoc_core_rx_padding_source_payload_error;
assign main_basesoc_core_rx_cdc_sink_sink_valid = main_basesoc_core_rx_converter_source_source_valid;
assign main_basesoc_core_rx_converter_source_source_ready = main_basesoc_core_rx_cdc_sink_sink_ready;
assign main_basesoc_core_rx_cdc_sink_sink_first = main_basesoc_core_rx_converter_source_source_first;
assign main_basesoc_core_rx_cdc_sink_sink_last = main_basesoc_core_rx_converter_source_source_last;
assign main_basesoc_core_rx_cdc_sink_sink_payload_data = main_basesoc_core_rx_converter_source_source_payload_data;
assign main_basesoc_core_rx_cdc_sink_sink_payload_be = main_basesoc_core_rx_converter_source_source_payload_be;
assign main_basesoc_core_rx_cdc_sink_sink_payload_error = main_basesoc_core_rx_converter_source_source_payload_error;
assign main_basesoc_core_source_valid = main_basesoc_core_rx_cdc_source_source_valid;
assign main_basesoc_core_rx_cdc_source_source_ready = main_basesoc_core_source_ready;
assign main_basesoc_core_source_first = main_basesoc_core_rx_cdc_source_source_first;
assign main_basesoc_core_source_last = main_basesoc_core_rx_cdc_source_source_last;
assign main_basesoc_core_source_payload_data = main_basesoc_core_rx_cdc_source_source_payload_data;
assign main_basesoc_core_source_payload_be = main_basesoc_core_rx_cdc_source_source_payload_be;
assign main_basesoc_core_source_payload_error = main_basesoc_core_rx_cdc_source_source_payload_error;
assign main_basesoc_wishbone_interface_writer_packet_sink_valid = main_basesoc_wishbone_interface_sink_valid;
assign main_basesoc_wishbone_interface_sink_ready = main_basesoc_wishbone_interface_writer_packet_sink_ready;
assign main_basesoc_wishbone_interface_writer_packet_sink_first = main_basesoc_wishbone_interface_sink_first;
assign main_basesoc_wishbone_interface_writer_packet_sink_last = main_basesoc_wishbone_interface_sink_last;
assign main_basesoc_wishbone_interface_writer_packet_sink_payload_data = main_basesoc_wishbone_interface_sink_payload_data;
assign main_basesoc_wishbone_interface_writer_packet_sink_payload_be = main_basesoc_wishbone_interface_sink_payload_be;
assign main_basesoc_wishbone_interface_writer_packet_sink_payload_error = main_basesoc_wishbone_interface_sink_payload_error;
assign main_basesoc_wishbone_interface_source_valid = main_basesoc_wishbone_interface_reader_packet_source_valid;
assign main_basesoc_wishbone_interface_reader_packet_source_ready = main_basesoc_wishbone_interface_source_ready;
assign main_basesoc_wishbone_interface_source_first = main_basesoc_wishbone_interface_reader_packet_source_first;
assign main_basesoc_wishbone_interface_source_last = main_basesoc_wishbone_interface_reader_packet_source_last;
assign main_basesoc_wishbone_interface_source_payload_data = main_basesoc_wishbone_interface_reader_packet_source_payload_data;
assign main_basesoc_wishbone_interface_source_payload_be = main_basesoc_wishbone_interface_reader_packet_source_payload_be;
assign main_basesoc_wishbone_interface_source_payload_error = main_basesoc_wishbone_interface_reader_packet_source_payload_error;
assign main_basesoc_wishbone_interface_writer_packet_source_ready = 1'd1;
assign main_basesoc_wishbone_interface_writer_packet_enable = main_basesoc_wishbone_interface_writer_stat_fifo_sink_ready;
assign main_basesoc_wishbone_interface_writer_stat_fifo_sink_valid = main_basesoc_wishbone_interface_writer_packet_done;
assign main_basesoc_wishbone_interface_writer_stat_fifo_sink_payload_slot = main_basesoc_wishbone_interface_writer_slot;
assign main_basesoc_wishbone_interface_writer_stat_fifo_sink_payload_length = main_basesoc_wishbone_interface_writer_packet_length0;
assign main_basesoc_wishbone_interface_writer_stat_fifo_source_ready = main_basesoc_wishbone_interface_writer_available_clear;
assign main_basesoc_wishbone_interface_writer_available_trigger = main_basesoc_wishbone_interface_writer_stat_fifo_source_valid;
assign main_basesoc_wishbone_interface_writer_slot_status = main_basesoc_wishbone_interface_writer_stat_fifo_source_payload_slot;
assign main_basesoc_wishbone_interface_writer_length_status = main_basesoc_wishbone_interface_writer_stat_fifo_source_payload_length;
assign main_basesoc_wishbone_interface_writer_wr_data = main_basesoc_wishbone_interface_writer_packet_source_payload_data;
assign main_basesoc_wishbone_interface_writer_memory0_adr = main_basesoc_wishbone_interface_writer_packet_offset[10:2];
assign main_basesoc_wishbone_interface_writer_memory0_dat_w = main_basesoc_wishbone_interface_writer_wr_data;
assign main_basesoc_wishbone_interface_writer_memory1_adr = main_basesoc_wishbone_interface_writer_packet_offset[10:2];
assign main_basesoc_wishbone_interface_writer_memory1_dat_w = main_basesoc_wishbone_interface_writer_wr_data;
always @(*) begin
    main_basesoc_wishbone_interface_writer_memory0_we = 1'd0;
    main_basesoc_wishbone_interface_writer_memory1_we = 1'd0;
    if ((main_basesoc_wishbone_interface_writer_packet_source_valid & main_basesoc_wishbone_interface_writer_packet_source_ready)) begin
        case (main_basesoc_wishbone_interface_writer_slot)
            1'd0: begin
                main_basesoc_wishbone_interface_writer_memory0_we = 1'd1;
            end
            1'd1: begin
                main_basesoc_wishbone_interface_writer_memory1_we = 1'd1;
            end
        endcase
    end
end
assign main_basesoc_wishbone_interface_writer_available0 = main_basesoc_wishbone_interface_writer_available_status;
assign main_basesoc_wishbone_interface_writer_available1 = main_basesoc_wishbone_interface_writer_available_pending;
always @(*) begin
    main_basesoc_wishbone_interface_writer_available_clear = 1'd0;
    if ((main_basesoc_wishbone_interface_writer_pending_wr_stb & main_basesoc_wishbone_interface_writer_pending_wr_data)) begin
        main_basesoc_wishbone_interface_writer_available_clear = 1'd1;
    end
end
assign main_basesoc_wishbone_interface_writer_irq = (main_basesoc_wishbone_interface_writer_pending_status & main_basesoc_wishbone_interface_writer_enable_storage);
assign main_basesoc_wishbone_interface_writer_available_status = main_basesoc_wishbone_interface_writer_available_trigger;
assign main_basesoc_wishbone_interface_writer_available_pending = main_basesoc_wishbone_interface_writer_available_trigger;
assign main_basesoc_wishbone_interface_writer_packet_length_inc = ((((1'd0 + main_basesoc_wishbone_interface_writer_packet_sink_payload_be[0]) + main_basesoc_wishbone_interface_writer_packet_sink_payload_be[1]) + main_basesoc_wishbone_interface_writer_packet_sink_payload_be[2]) + main_basesoc_wishbone_interface_writer_packet_sink_payload_be[3]);
assign main_basesoc_wishbone_interface_writer_packet_next_length = (main_basesoc_wishbone_interface_writer_packet_length1 + main_basesoc_wishbone_interface_writer_packet_length_inc);
assign main_basesoc_wishbone_interface_writer_packet_oversized = (main_basesoc_wishbone_interface_writer_packet_next_length > 11'd1530);
assign main_basesoc_wishbone_interface_writer_packet_last_error = ((main_basesoc_wishbone_interface_writer_packet_sink_payload_error & main_basesoc_wishbone_interface_writer_packet_sink_payload_be) != 1'd0);
assign main_basesoc_wishbone_interface_writer_packet_offset = main_basesoc_wishbone_interface_writer_packet_length1;
assign main_basesoc_wishbone_interface_writer_packet_length0 = (main_basesoc_wishbone_interface_writer_packet_done ? main_basesoc_wishbone_interface_writer_packet_pkt_len : main_basesoc_wishbone_interface_writer_packet_next_length);
always @(*) begin
    builder_clockdomainsrenamer_next_state = 3'd0;
    main_basesoc_wishbone_interface_writer_packet_done = 1'd0;
    main_basesoc_wishbone_interface_writer_packet_drop = 1'd0;
    main_basesoc_wishbone_interface_writer_packet_error0 = 1'd0;
    main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value2 = 1'd0;
    main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value_ce2 = 1'd0;
    main_basesoc_wishbone_interface_writer_packet_length1_liteethmacsramwriter_next_value0 = 11'd0;
    main_basesoc_wishbone_interface_writer_packet_length1_liteethmacsramwriter_next_value_ce0 = 1'd0;
    main_basesoc_wishbone_interface_writer_packet_pkt_len_liteethmacsramwriter_next_value1 = 11'd0;
    main_basesoc_wishbone_interface_writer_packet_pkt_len_liteethmacsramwriter_next_value_ce1 = 1'd0;
    main_basesoc_wishbone_interface_writer_packet_sink_ready = 1'd0;
    main_basesoc_wishbone_interface_writer_packet_source_last = 1'd0;
    main_basesoc_wishbone_interface_writer_packet_source_payload_data = 32'd0;
    main_basesoc_wishbone_interface_writer_packet_source_valid = 1'd0;
    case (builder_clockdomainsrenamer_state)
        1'd1: begin
        end
        2'd2: begin
        end
        2'd3: begin
        end
        3'd4: begin
            main_basesoc_wishbone_interface_writer_packet_done = 1'd1;
        end
        default: begin
        end
    endcase
    case (builder_clockdomainsrenamer_state)
        1'd1: begin
        end
        2'd2: begin
        end
        2'd3: begin
            main_basesoc_wishbone_interface_writer_packet_drop = 1'd1;
        end
        3'd4: begin
        end
        default: begin
        end
    endcase
    case (builder_clockdomainsrenamer_state)
        1'd1: begin
        end
        2'd2: begin
        end
        2'd3: begin
            main_basesoc_wishbone_interface_writer_packet_error0 = main_basesoc_wishbone_interface_writer_packet_error1;
        end
        3'd4: begin
        end
        default: begin
        end
    endcase
    case (builder_clockdomainsrenamer_state)
        1'd1: begin
            main_basesoc_wishbone_interface_writer_packet_sink_ready = (main_basesoc_wishbone_interface_writer_packet_oversized ? 1'd1 : main_basesoc_wishbone_interface_writer_packet_source_ready);
        end
        2'd2: begin
            main_basesoc_wishbone_interface_writer_packet_sink_ready = 1'd1;
        end
        2'd3: begin
        end
        3'd4: begin
        end
        default: begin
            if (main_basesoc_wishbone_interface_writer_packet_enable) begin
                main_basesoc_wishbone_interface_writer_packet_sink_ready = (main_basesoc_wishbone_interface_writer_packet_oversized ? 1'd1 : main_basesoc_wishbone_interface_writer_packet_source_ready);
            end else begin
                main_basesoc_wishbone_interface_writer_packet_sink_ready = 1'd1;
            end
        end
    endcase
    builder_clockdomainsrenamer_next_state = builder_clockdomainsrenamer_state;
    case (builder_clockdomainsrenamer_state)
        1'd1: begin
            if ((main_basesoc_wishbone_interface_writer_packet_sink_valid & main_basesoc_wishbone_interface_writer_packet_sink_ready)) begin
                if (main_basesoc_wishbone_interface_writer_packet_oversized) begin
                    if (main_basesoc_wishbone_interface_writer_packet_sink_last) begin
                        builder_clockdomainsrenamer_next_state = 2'd3;
                    end else begin
                        builder_clockdomainsrenamer_next_state = 2'd2;
                    end
                end else begin
                    if (main_basesoc_wishbone_interface_writer_packet_sink_last) begin
                        if ((main_basesoc_wishbone_interface_writer_packet_error1 | main_basesoc_wishbone_interface_writer_packet_last_error)) begin
                            builder_clockdomainsrenamer_next_state = 2'd3;
                        end else begin
                            builder_clockdomainsrenamer_next_state = 3'd4;
                        end
                    end else begin
                    end
                end
            end
        end
        2'd2: begin
            if ((main_basesoc_wishbone_interface_writer_packet_sink_valid & main_basesoc_wishbone_interface_writer_packet_sink_last)) begin
                builder_clockdomainsrenamer_next_state = 2'd3;
            end
        end
        2'd3: begin
            builder_clockdomainsrenamer_next_state = 1'd0;
        end
        3'd4: begin
            builder_clockdomainsrenamer_next_state = 1'd0;
        end
        default: begin
            if (main_basesoc_wishbone_interface_writer_packet_enable) begin
                if ((main_basesoc_wishbone_interface_writer_packet_sink_valid & main_basesoc_wishbone_interface_writer_packet_sink_ready)) begin
                    if (main_basesoc_wishbone_interface_writer_packet_oversized) begin
                        if (main_basesoc_wishbone_interface_writer_packet_sink_last) begin
                            builder_clockdomainsrenamer_next_state = 2'd3;
                        end else begin
                            builder_clockdomainsrenamer_next_state = 2'd2;
                        end
                    end else begin
                        if (main_basesoc_wishbone_interface_writer_packet_sink_last) begin
                            if ((main_basesoc_wishbone_interface_writer_packet_error1 | main_basesoc_wishbone_interface_writer_packet_last_error)) begin
                                builder_clockdomainsrenamer_next_state = 2'd3;
                            end else begin
                                builder_clockdomainsrenamer_next_state = 3'd4;
                            end
                        end else begin
                            builder_clockdomainsrenamer_next_state = 1'd1;
                        end
                    end
                end
            end else begin
                if (main_basesoc_wishbone_interface_writer_packet_sink_valid) begin
                    if (main_basesoc_wishbone_interface_writer_packet_sink_last) begin
                        builder_clockdomainsrenamer_next_state = 2'd3;
                    end else begin
                        builder_clockdomainsrenamer_next_state = 2'd2;
                    end
                end
            end
        end
    endcase
    case (builder_clockdomainsrenamer_state)
        1'd1: begin
            if ((main_basesoc_wishbone_interface_writer_packet_sink_valid & main_basesoc_wishbone_interface_writer_packet_sink_ready)) begin
                if (main_basesoc_wishbone_interface_writer_packet_oversized) begin
                    main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value2 = 1'd1;
                end else begin
                    if (main_basesoc_wishbone_interface_writer_packet_sink_last) begin
                        if ((main_basesoc_wishbone_interface_writer_packet_error1 | main_basesoc_wishbone_interface_writer_packet_last_error)) begin
                            main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value2 = 1'd1;
                        end else begin
                        end
                    end else begin
                        if (main_basesoc_wishbone_interface_writer_packet_last_error) begin
                            main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value2 = 1'd1;
                        end
                    end
                end
            end
        end
        2'd2: begin
        end
        2'd3: begin
            main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value2 = 1'd0;
        end
        3'd4: begin
            main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value2 = 1'd0;
        end
        default: begin
            if (main_basesoc_wishbone_interface_writer_packet_enable) begin
                if ((main_basesoc_wishbone_interface_writer_packet_sink_valid & main_basesoc_wishbone_interface_writer_packet_sink_ready)) begin
                    if (main_basesoc_wishbone_interface_writer_packet_oversized) begin
                        main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value2 = 1'd1;
                    end else begin
                        if (main_basesoc_wishbone_interface_writer_packet_sink_last) begin
                            if ((main_basesoc_wishbone_interface_writer_packet_error1 | main_basesoc_wishbone_interface_writer_packet_last_error)) begin
                                main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value2 = 1'd1;
                            end else begin
                            end
                        end else begin
                            if (main_basesoc_wishbone_interface_writer_packet_last_error) begin
                                main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value2 = 1'd1;
                            end
                        end
                    end
                end
            end else begin
            end
        end
    endcase
    case (builder_clockdomainsrenamer_state)
        1'd1: begin
            if ((main_basesoc_wishbone_interface_writer_packet_sink_valid & main_basesoc_wishbone_interface_writer_packet_sink_ready)) begin
                if (main_basesoc_wishbone_interface_writer_packet_oversized) begin
                    main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value_ce2 = 1'd1;
                end else begin
                    if (main_basesoc_wishbone_interface_writer_packet_sink_last) begin
                        if ((main_basesoc_wishbone_interface_writer_packet_error1 | main_basesoc_wishbone_interface_writer_packet_last_error)) begin
                            main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value_ce2 = 1'd1;
                        end else begin
                        end
                    end else begin
                        if (main_basesoc_wishbone_interface_writer_packet_last_error) begin
                            main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value_ce2 = 1'd1;
                        end
                    end
                end
            end
        end
        2'd2: begin
        end
        2'd3: begin
            main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value_ce2 = 1'd1;
        end
        3'd4: begin
            main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value_ce2 = 1'd1;
        end
        default: begin
            if (main_basesoc_wishbone_interface_writer_packet_enable) begin
                if ((main_basesoc_wishbone_interface_writer_packet_sink_valid & main_basesoc_wishbone_interface_writer_packet_sink_ready)) begin
                    if (main_basesoc_wishbone_interface_writer_packet_oversized) begin
                        main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value_ce2 = 1'd1;
                    end else begin
                        if (main_basesoc_wishbone_interface_writer_packet_sink_last) begin
                            if ((main_basesoc_wishbone_interface_writer_packet_error1 | main_basesoc_wishbone_interface_writer_packet_last_error)) begin
                                main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value_ce2 = 1'd1;
                            end else begin
                            end
                        end else begin
                            if (main_basesoc_wishbone_interface_writer_packet_last_error) begin
                                main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value_ce2 = 1'd1;
                            end
                        end
                    end
                end
            end else begin
            end
        end
    endcase
    case (builder_clockdomainsrenamer_state)
        1'd1: begin
            if ((main_basesoc_wishbone_interface_writer_packet_sink_valid & main_basesoc_wishbone_interface_writer_packet_sink_ready)) begin
                main_basesoc_wishbone_interface_writer_packet_length1_liteethmacsramwriter_next_value0 = main_basesoc_wishbone_interface_writer_packet_next_length;
            end
        end
        2'd2: begin
        end
        2'd3: begin
            main_basesoc_wishbone_interface_writer_packet_length1_liteethmacsramwriter_next_value0 = 1'd0;
        end
        3'd4: begin
            main_basesoc_wishbone_interface_writer_packet_length1_liteethmacsramwriter_next_value0 = 1'd0;
        end
        default: begin
            if (main_basesoc_wishbone_interface_writer_packet_enable) begin
                if ((main_basesoc_wishbone_interface_writer_packet_sink_valid & main_basesoc_wishbone_interface_writer_packet_sink_ready)) begin
                    main_basesoc_wishbone_interface_writer_packet_length1_liteethmacsramwriter_next_value0 = main_basesoc_wishbone_interface_writer_packet_next_length;
                end
            end else begin
            end
        end
    endcase
    case (builder_clockdomainsrenamer_state)
        1'd1: begin
            if ((main_basesoc_wishbone_interface_writer_packet_sink_valid & main_basesoc_wishbone_interface_writer_packet_sink_ready)) begin
                main_basesoc_wishbone_interface_writer_packet_length1_liteethmacsramwriter_next_value_ce0 = 1'd1;
            end
        end
        2'd2: begin
        end
        2'd3: begin
            main_basesoc_wishbone_interface_writer_packet_length1_liteethmacsramwriter_next_value_ce0 = 1'd1;
        end
        3'd4: begin
            main_basesoc_wishbone_interface_writer_packet_length1_liteethmacsramwriter_next_value_ce0 = 1'd1;
        end
        default: begin
            if (main_basesoc_wishbone_interface_writer_packet_enable) begin
                if ((main_basesoc_wishbone_interface_writer_packet_sink_valid & main_basesoc_wishbone_interface_writer_packet_sink_ready)) begin
                    main_basesoc_wishbone_interface_writer_packet_length1_liteethmacsramwriter_next_value_ce0 = 1'd1;
                end
            end else begin
            end
        end
    endcase
    case (builder_clockdomainsrenamer_state)
        1'd1: begin
            if ((main_basesoc_wishbone_interface_writer_packet_sink_valid & main_basesoc_wishbone_interface_writer_packet_sink_ready)) begin
                main_basesoc_wishbone_interface_writer_packet_pkt_len_liteethmacsramwriter_next_value1 = main_basesoc_wishbone_interface_writer_packet_next_length;
            end
        end
        2'd2: begin
        end
        2'd3: begin
            main_basesoc_wishbone_interface_writer_packet_pkt_len_liteethmacsramwriter_next_value1 = 1'd0;
        end
        3'd4: begin
            main_basesoc_wishbone_interface_writer_packet_pkt_len_liteethmacsramwriter_next_value1 = 1'd0;
        end
        default: begin
            if (main_basesoc_wishbone_interface_writer_packet_enable) begin
                if ((main_basesoc_wishbone_interface_writer_packet_sink_valid & main_basesoc_wishbone_interface_writer_packet_sink_ready)) begin
                    main_basesoc_wishbone_interface_writer_packet_pkt_len_liteethmacsramwriter_next_value1 = main_basesoc_wishbone_interface_writer_packet_next_length;
                end
            end else begin
            end
        end
    endcase
    case (builder_clockdomainsrenamer_state)
        1'd1: begin
            if ((main_basesoc_wishbone_interface_writer_packet_sink_valid & main_basesoc_wishbone_interface_writer_packet_sink_ready)) begin
                main_basesoc_wishbone_interface_writer_packet_pkt_len_liteethmacsramwriter_next_value_ce1 = 1'd1;
            end
        end
        2'd2: begin
        end
        2'd3: begin
            main_basesoc_wishbone_interface_writer_packet_pkt_len_liteethmacsramwriter_next_value_ce1 = 1'd1;
        end
        3'd4: begin
            main_basesoc_wishbone_interface_writer_packet_pkt_len_liteethmacsramwriter_next_value_ce1 = 1'd1;
        end
        default: begin
            if (main_basesoc_wishbone_interface_writer_packet_enable) begin
                if ((main_basesoc_wishbone_interface_writer_packet_sink_valid & main_basesoc_wishbone_interface_writer_packet_sink_ready)) begin
                    main_basesoc_wishbone_interface_writer_packet_pkt_len_liteethmacsramwriter_next_value_ce1 = 1'd1;
                end
            end else begin
            end
        end
    endcase
    case (builder_clockdomainsrenamer_state)
        1'd1: begin
            main_basesoc_wishbone_interface_writer_packet_source_last = main_basesoc_wishbone_interface_writer_packet_sink_last;
        end
        2'd2: begin
        end
        2'd3: begin
        end
        3'd4: begin
        end
        default: begin
            if (main_basesoc_wishbone_interface_writer_packet_enable) begin
                main_basesoc_wishbone_interface_writer_packet_source_last = main_basesoc_wishbone_interface_writer_packet_sink_last;
            end else begin
            end
        end
    endcase
    case (builder_clockdomainsrenamer_state)
        1'd1: begin
            main_basesoc_wishbone_interface_writer_packet_source_payload_data = main_basesoc_wishbone_interface_writer_packet_sink_payload_data;
        end
        2'd2: begin
        end
        2'd3: begin
        end
        3'd4: begin
        end
        default: begin
            if (main_basesoc_wishbone_interface_writer_packet_enable) begin
                main_basesoc_wishbone_interface_writer_packet_source_payload_data = main_basesoc_wishbone_interface_writer_packet_sink_payload_data;
            end else begin
            end
        end
    endcase
    case (builder_clockdomainsrenamer_state)
        1'd1: begin
            main_basesoc_wishbone_interface_writer_packet_source_valid = (main_basesoc_wishbone_interface_writer_packet_sink_valid & (~main_basesoc_wishbone_interface_writer_packet_oversized));
        end
        2'd2: begin
        end
        2'd3: begin
        end
        3'd4: begin
        end
        default: begin
            if (main_basesoc_wishbone_interface_writer_packet_enable) begin
                main_basesoc_wishbone_interface_writer_packet_source_valid = (main_basesoc_wishbone_interface_writer_packet_sink_valid & (~main_basesoc_wishbone_interface_writer_packet_oversized));
            end else begin
            end
        end
    endcase
end
assign main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_din = {main_basesoc_wishbone_interface_writer_stat_fifo_fifo_in_last, main_basesoc_wishbone_interface_writer_stat_fifo_fifo_in_first, main_basesoc_wishbone_interface_writer_stat_fifo_fifo_in_payload_length, main_basesoc_wishbone_interface_writer_stat_fifo_fifo_in_payload_slot};
assign {main_basesoc_wishbone_interface_writer_stat_fifo_fifo_out_last, main_basesoc_wishbone_interface_writer_stat_fifo_fifo_out_first, main_basesoc_wishbone_interface_writer_stat_fifo_fifo_out_payload_length, main_basesoc_wishbone_interface_writer_stat_fifo_fifo_out_payload_slot} = main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_dout;
assign main_basesoc_wishbone_interface_writer_stat_fifo_sink_ready = main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_writable;
assign main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_we = main_basesoc_wishbone_interface_writer_stat_fifo_sink_valid;
assign main_basesoc_wishbone_interface_writer_stat_fifo_fifo_in_first = main_basesoc_wishbone_interface_writer_stat_fifo_sink_first;
assign main_basesoc_wishbone_interface_writer_stat_fifo_fifo_in_last = main_basesoc_wishbone_interface_writer_stat_fifo_sink_last;
assign main_basesoc_wishbone_interface_writer_stat_fifo_fifo_in_payload_slot = main_basesoc_wishbone_interface_writer_stat_fifo_sink_payload_slot;
assign main_basesoc_wishbone_interface_writer_stat_fifo_fifo_in_payload_length = main_basesoc_wishbone_interface_writer_stat_fifo_sink_payload_length;
assign main_basesoc_wishbone_interface_writer_stat_fifo_source_valid = main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_readable;
assign main_basesoc_wishbone_interface_writer_stat_fifo_source_first = main_basesoc_wishbone_interface_writer_stat_fifo_fifo_out_first;
assign main_basesoc_wishbone_interface_writer_stat_fifo_source_last = main_basesoc_wishbone_interface_writer_stat_fifo_fifo_out_last;
assign main_basesoc_wishbone_interface_writer_stat_fifo_source_payload_slot = main_basesoc_wishbone_interface_writer_stat_fifo_fifo_out_payload_slot;
assign main_basesoc_wishbone_interface_writer_stat_fifo_source_payload_length = main_basesoc_wishbone_interface_writer_stat_fifo_fifo_out_payload_length;
assign main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_re = main_basesoc_wishbone_interface_writer_stat_fifo_source_ready;
always @(*) begin
    main_basesoc_wishbone_interface_writer_stat_fifo_wrport_adr = 1'd0;
    if (main_basesoc_wishbone_interface_writer_stat_fifo_replace) begin
        main_basesoc_wishbone_interface_writer_stat_fifo_wrport_adr = (main_basesoc_wishbone_interface_writer_stat_fifo_produce - 1'd1);
    end else begin
        main_basesoc_wishbone_interface_writer_stat_fifo_wrport_adr = main_basesoc_wishbone_interface_writer_stat_fifo_produce;
    end
end
assign main_basesoc_wishbone_interface_writer_stat_fifo_wrport_dat_w = main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_din;
assign main_basesoc_wishbone_interface_writer_stat_fifo_wrport_we = (main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_we & (main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_writable | main_basesoc_wishbone_interface_writer_stat_fifo_replace));
assign main_basesoc_wishbone_interface_writer_stat_fifo_do_read = (main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_readable & main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_re);
assign main_basesoc_wishbone_interface_writer_stat_fifo_rdport_adr = main_basesoc_wishbone_interface_writer_stat_fifo_consume;
assign main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_dout = main_basesoc_wishbone_interface_writer_stat_fifo_rdport_dat_r;
assign main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_writable = (main_basesoc_wishbone_interface_writer_stat_fifo_level != 2'd2);
assign main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_readable = (main_basesoc_wishbone_interface_writer_stat_fifo_level != 1'd0);
assign main_basesoc_wishbone_interface_reader_cmd_fifo_sink_valid = main_basesoc_wishbone_interface_reader_start_re;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_sink_payload_slot = main_basesoc_wishbone_interface_reader_slot_storage;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_sink_payload_length = main_basesoc_wishbone_interface_reader_length_storage;
assign main_basesoc_wishbone_interface_reader_ready_status = main_basesoc_wishbone_interface_reader_cmd_fifo_sink_ready;
assign main_basesoc_wishbone_interface_reader_level_status = main_basesoc_wishbone_interface_reader_cmd_fifo_level;
assign main_basesoc_wishbone_interface_reader_packet_length = main_basesoc_wishbone_interface_reader_cmd_fifo_source_payload_length;
assign main_basesoc_wishbone_interface_reader_valid_command = (((main_basesoc_wishbone_interface_reader_cmd_fifo_source_payload_slot < 2'd2) & (main_basesoc_wishbone_interface_reader_cmd_fifo_source_payload_length != 1'd0)) & (main_basesoc_wishbone_interface_reader_cmd_fifo_source_payload_length <= 11'd1532));
assign main_basesoc_wishbone_interface_reader_packet_enable = ((main_basesoc_wishbone_interface_reader_fsm_is_ongoing0 & main_basesoc_wishbone_interface_reader_cmd_fifo_source_valid) & main_basesoc_wishbone_interface_reader_valid_command);
assign main_basesoc_wishbone_interface_reader_packet_sink_valid = 1'd1;
assign main_basesoc_wishbone_interface_reader_packet_sink_last = (main_basesoc_wishbone_interface_reader_rd_offset >= main_basesoc_wishbone_interface_reader_cmd_fifo_source_payload_length);
assign main_basesoc_wishbone_interface_reader_eventsourcepulse_trigger = main_basesoc_wishbone_interface_reader_fsm_is_ongoing1;
assign main_basesoc_wishbone_interface_reader_memory0_re = main_basesoc_wishbone_interface_reader_read;
assign main_basesoc_wishbone_interface_reader_memory0_adr = main_basesoc_wishbone_interface_reader_rd_offset[10:2];
assign main_basesoc_wishbone_interface_reader_memory1_re = main_basesoc_wishbone_interface_reader_read;
assign main_basesoc_wishbone_interface_reader_memory1_adr = main_basesoc_wishbone_interface_reader_rd_offset[10:2];
always @(*) begin
    main_basesoc_wishbone_interface_reader_rd_data = 32'd0;
    case (main_basesoc_wishbone_interface_reader_cmd_fifo_source_payload_slot)
        1'd0: begin
            main_basesoc_wishbone_interface_reader_rd_data = main_basesoc_wishbone_interface_reader_memory0_dat_r;
        end
        1'd1: begin
            main_basesoc_wishbone_interface_reader_rd_data = main_basesoc_wishbone_interface_reader_memory1_dat_r;
        end
    endcase
end
assign main_basesoc_wishbone_interface_reader_packet_sink_payload_data = main_basesoc_wishbone_interface_reader_rd_data;
assign main_basesoc_wishbone_interface_reader_event00 = main_basesoc_wishbone_interface_reader_eventsourcepulse_status;
assign main_basesoc_wishbone_interface_reader_event01 = main_basesoc_wishbone_interface_reader_eventsourcepulse_pending;
always @(*) begin
    main_basesoc_wishbone_interface_reader_eventsourcepulse_clear = 1'd0;
    if ((main_basesoc_wishbone_interface_reader_pending_wr_stb & main_basesoc_wishbone_interface_reader_pending_wr_data)) begin
        main_basesoc_wishbone_interface_reader_eventsourcepulse_clear = 1'd1;
    end
end
assign main_basesoc_wishbone_interface_reader_irq = (main_basesoc_wishbone_interface_reader_pending_status & main_basesoc_wishbone_interface_reader_enable_storage);
assign main_basesoc_wishbone_interface_reader_eventsourcepulse_status = 1'd0;
assign main_basesoc_wishbone_interface_reader_packet_source_valid = (main_basesoc_wishbone_interface_reader_packet_sink_valid & main_basesoc_wishbone_interface_reader_packet_direct_read);
assign main_basesoc_wishbone_interface_reader_packet_source_payload_data = main_basesoc_wishbone_interface_reader_packet_sink_payload_data;
assign main_basesoc_wishbone_interface_reader_packet_source_last = main_basesoc_wishbone_interface_reader_packet_sink_last;
assign main_basesoc_wishbone_interface_reader_packet_source_payload_error = 1'd0;
assign main_basesoc_wishbone_interface_reader_packet_sink_ready = (main_basesoc_wishbone_interface_reader_packet_source_ready & main_basesoc_wishbone_interface_reader_packet_direct_read);
assign main_basesoc_wishbone_interface_reader_packet_source_payload_be = (main_basesoc_wishbone_interface_reader_packet_source_last ? {((((main_basesoc_wishbone_interface_reader_packet_length & 2'd3) == 1'd0) ? 3'd4 : (main_basesoc_wishbone_interface_reader_packet_length & 2'd3)) > 2'd3), ((((main_basesoc_wishbone_interface_reader_packet_length & 2'd3) == 1'd0) ? 3'd4 : (main_basesoc_wishbone_interface_reader_packet_length & 2'd3)) > 2'd2), ((((main_basesoc_wishbone_interface_reader_packet_length & 2'd3) == 1'd0) ? 3'd4 : (main_basesoc_wishbone_interface_reader_packet_length & 2'd3)) > 1'd1), ((((main_basesoc_wishbone_interface_reader_packet_length & 2'd3) == 1'd0) ? 3'd4 : (main_basesoc_wishbone_interface_reader_packet_length & 2'd3)) > 1'd0)} : 4'd15);
assign main_basesoc_wishbone_interface_reader_packet_idle = main_basesoc_wishbone_interface_reader_packet_is_ongoing0;
assign main_basesoc_wishbone_interface_reader_packet_direct_read = main_basesoc_wishbone_interface_reader_packet_is_ongoing1;
always @(*) begin
    builder_clockdomainsrenamer_liteethmacpacketreader_next_state = 2'd0;
    main_basesoc_wishbone_interface_reader_packet_done = 1'd0;
    main_basesoc_wishbone_interface_reader_packet_is_ongoing0 = 1'd0;
    main_basesoc_wishbone_interface_reader_packet_is_ongoing1 = 1'd0;
    builder_clockdomainsrenamer_liteethmacpacketreader_next_state = builder_clockdomainsrenamer_liteethmacpacketreader_state;
    case (builder_clockdomainsrenamer_liteethmacpacketreader_state)
        1'd1: begin
            main_basesoc_wishbone_interface_reader_packet_is_ongoing1 = 1'd1;
            if (((main_basesoc_wishbone_interface_reader_packet_sink_valid & main_basesoc_wishbone_interface_reader_packet_sink_ready) & main_basesoc_wishbone_interface_reader_packet_sink_last)) begin
                builder_clockdomainsrenamer_liteethmacpacketreader_next_state = 2'd2;
            end
        end
        2'd2: begin
            main_basesoc_wishbone_interface_reader_packet_done = 1'd1;
            builder_clockdomainsrenamer_liteethmacpacketreader_next_state = 1'd0;
        end
        default: begin
            main_basesoc_wishbone_interface_reader_packet_is_ongoing0 = 1'd1;
            if (main_basesoc_wishbone_interface_reader_packet_enable) begin
                if (((main_basesoc_wishbone_interface_reader_packet_length == 1'd0) | (main_basesoc_wishbone_interface_reader_packet_length > 11'd1532))) begin
                    builder_clockdomainsrenamer_liteethmacpacketreader_next_state = 2'd2;
                end else begin
                    builder_clockdomainsrenamer_liteethmacpacketreader_next_state = 1'd1;
                end
            end
        end
    endcase
end
assign main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_din = {main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_in_last, main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_in_first, main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_in_payload_length, main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_in_payload_slot};
assign {main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_out_last, main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_out_first, main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_out_payload_length, main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_out_payload_slot} = main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_dout;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_sink_ready = main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_writable;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_we = main_basesoc_wishbone_interface_reader_cmd_fifo_sink_valid;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_in_first = main_basesoc_wishbone_interface_reader_cmd_fifo_sink_first;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_in_last = main_basesoc_wishbone_interface_reader_cmd_fifo_sink_last;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_in_payload_slot = main_basesoc_wishbone_interface_reader_cmd_fifo_sink_payload_slot;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_in_payload_length = main_basesoc_wishbone_interface_reader_cmd_fifo_sink_payload_length;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_source_valid = main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_readable;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_source_first = main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_out_first;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_source_last = main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_out_last;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_source_payload_slot = main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_out_payload_slot;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_source_payload_length = main_basesoc_wishbone_interface_reader_cmd_fifo_fifo_out_payload_length;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_re = main_basesoc_wishbone_interface_reader_cmd_fifo_source_ready;
always @(*) begin
    main_basesoc_wishbone_interface_reader_cmd_fifo_wrport_adr = 1'd0;
    if (main_basesoc_wishbone_interface_reader_cmd_fifo_replace) begin
        main_basesoc_wishbone_interface_reader_cmd_fifo_wrport_adr = (main_basesoc_wishbone_interface_reader_cmd_fifo_produce - 1'd1);
    end else begin
        main_basesoc_wishbone_interface_reader_cmd_fifo_wrport_adr = main_basesoc_wishbone_interface_reader_cmd_fifo_produce;
    end
end
assign main_basesoc_wishbone_interface_reader_cmd_fifo_wrport_dat_w = main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_din;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_wrport_we = (main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_we & (main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_writable | main_basesoc_wishbone_interface_reader_cmd_fifo_replace));
assign main_basesoc_wishbone_interface_reader_cmd_fifo_do_read = (main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_readable & main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_re);
assign main_basesoc_wishbone_interface_reader_cmd_fifo_rdport_adr = main_basesoc_wishbone_interface_reader_cmd_fifo_consume;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_dout = main_basesoc_wishbone_interface_reader_cmd_fifo_rdport_dat_r;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_writable = (main_basesoc_wishbone_interface_reader_cmd_fifo_level != 2'd2);
assign main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_readable = (main_basesoc_wishbone_interface_reader_cmd_fifo_level != 1'd0);
always @(*) begin
    builder_clockdomainsrenamer_fsm_next_state = 2'd0;
    main_basesoc_wishbone_interface_reader_cmd_fifo_source_ready = 1'd0;
    main_basesoc_wishbone_interface_reader_fsm_is_ongoing0 = 1'd0;
    main_basesoc_wishbone_interface_reader_fsm_is_ongoing1 = 1'd0;
    main_basesoc_wishbone_interface_reader_rd_offset_liteethmacsramreader_next_value = 11'd0;
    main_basesoc_wishbone_interface_reader_rd_offset_liteethmacsramreader_next_value_ce = 1'd0;
    main_basesoc_wishbone_interface_reader_read = 1'd0;
    builder_clockdomainsrenamer_fsm_next_state = builder_clockdomainsrenamer_fsm_state;
    case (builder_clockdomainsrenamer_fsm_state)
        1'd1: begin
            if (main_basesoc_wishbone_interface_reader_packet_done) begin
                builder_clockdomainsrenamer_fsm_next_state = 2'd2;
            end else begin
                if ((main_basesoc_wishbone_interface_reader_packet_sink_ready & (~main_basesoc_wishbone_interface_reader_packet_sink_last))) begin
                    main_basesoc_wishbone_interface_reader_read = 1'd1;
                    main_basesoc_wishbone_interface_reader_rd_offset_liteethmacsramreader_next_value = (main_basesoc_wishbone_interface_reader_rd_offset + 3'd4);
                    main_basesoc_wishbone_interface_reader_rd_offset_liteethmacsramreader_next_value_ce = 1'd1;
                end
            end
        end
        2'd2: begin
            if (1'd1) begin
                main_basesoc_wishbone_interface_reader_rd_offset_liteethmacsramreader_next_value = 1'd0;
                main_basesoc_wishbone_interface_reader_rd_offset_liteethmacsramreader_next_value_ce = 1'd1;
                main_basesoc_wishbone_interface_reader_cmd_fifo_source_ready = 1'd1;
                builder_clockdomainsrenamer_fsm_next_state = 1'd0;
            end
            main_basesoc_wishbone_interface_reader_fsm_is_ongoing1 = 1'd1;
        end
        default: begin
            main_basesoc_wishbone_interface_reader_fsm_is_ongoing0 = 1'd1;
            if (main_basesoc_wishbone_interface_reader_cmd_fifo_source_valid) begin
                if (main_basesoc_wishbone_interface_reader_valid_command) begin
                    main_basesoc_wishbone_interface_reader_read = 1'd1;
                    main_basesoc_wishbone_interface_reader_rd_offset_liteethmacsramreader_next_value = 3'd4;
                    main_basesoc_wishbone_interface_reader_rd_offset_liteethmacsramreader_next_value_ce = 1'd1;
                    builder_clockdomainsrenamer_fsm_next_state = 1'd1;
                end else begin
                    builder_clockdomainsrenamer_fsm_next_state = 2'd2;
                end
            end
        end
    endcase
end
assign main_basesoc_wishbone_interface_ev_irq = (main_basesoc_wishbone_interface_writer_irq | main_basesoc_wishbone_interface_reader_irq);
assign main_basesoc_wishbone_interface_sram0_adr = main_basesoc_wishbone_interface_interface0_adr[8:0];
assign main_basesoc_wishbone_interface_interface0_dat_r = main_basesoc_wishbone_interface_sram0_dat_r;
assign main_basesoc_wishbone_interface_sram1_adr = main_basesoc_wishbone_interface_interface1_adr[8:0];
assign main_basesoc_wishbone_interface_interface1_dat_r = main_basesoc_wishbone_interface_sram1_dat_r;
always @(*) begin
    main_basesoc_wishbone_interface_decoder0_slave_sel = 2'd0;
    main_basesoc_wishbone_interface_decoder0_slave_sel[0] = (main_basesoc_wishbone_interface_bus_rx_adr[9] == 1'd0);
    main_basesoc_wishbone_interface_decoder0_slave_sel[1] = (main_basesoc_wishbone_interface_bus_rx_adr[9] == 1'd1);
end
assign main_basesoc_wishbone_interface_interface0_adr = main_basesoc_wishbone_interface_bus_rx_adr;
assign main_basesoc_wishbone_interface_interface0_dat_w = main_basesoc_wishbone_interface_bus_rx_dat_w;
assign main_basesoc_wishbone_interface_interface0_sel = main_basesoc_wishbone_interface_bus_rx_sel;
assign main_basesoc_wishbone_interface_interface0_stb = main_basesoc_wishbone_interface_bus_rx_stb;
assign main_basesoc_wishbone_interface_interface0_we = main_basesoc_wishbone_interface_bus_rx_we;
assign main_basesoc_wishbone_interface_interface0_cti = main_basesoc_wishbone_interface_bus_rx_cti;
assign main_basesoc_wishbone_interface_interface0_bte = main_basesoc_wishbone_interface_bus_rx_bte;
assign main_basesoc_wishbone_interface_interface1_adr = main_basesoc_wishbone_interface_bus_rx_adr;
assign main_basesoc_wishbone_interface_interface1_dat_w = main_basesoc_wishbone_interface_bus_rx_dat_w;
assign main_basesoc_wishbone_interface_interface1_sel = main_basesoc_wishbone_interface_bus_rx_sel;
assign main_basesoc_wishbone_interface_interface1_stb = main_basesoc_wishbone_interface_bus_rx_stb;
assign main_basesoc_wishbone_interface_interface1_we = main_basesoc_wishbone_interface_bus_rx_we;
assign main_basesoc_wishbone_interface_interface1_cti = main_basesoc_wishbone_interface_bus_rx_cti;
assign main_basesoc_wishbone_interface_interface1_bte = main_basesoc_wishbone_interface_bus_rx_bte;
assign main_basesoc_wishbone_interface_interface0_cyc = (main_basesoc_wishbone_interface_bus_rx_cyc & main_basesoc_wishbone_interface_decoder0_slave_sel[0]);
assign main_basesoc_wishbone_interface_interface1_cyc = (main_basesoc_wishbone_interface_bus_rx_cyc & main_basesoc_wishbone_interface_decoder0_slave_sel[1]);
assign main_basesoc_wishbone_interface_bus_rx_ack = (main_basesoc_wishbone_interface_interface0_ack | main_basesoc_wishbone_interface_interface1_ack);
assign main_basesoc_wishbone_interface_bus_rx_err = (main_basesoc_wishbone_interface_interface0_err | main_basesoc_wishbone_interface_interface1_err);
assign main_basesoc_wishbone_interface_bus_rx_dat_r = (({32{main_basesoc_wishbone_interface_decoder0_slave_sel_r[0]}} & main_basesoc_wishbone_interface_interface0_dat_r) | ({32{main_basesoc_wishbone_interface_decoder0_slave_sel_r[1]}} & main_basesoc_wishbone_interface_interface1_dat_r));
always @(*) begin
    main_basesoc_wishbone_interface_sram2_we = 4'd0;
    main_basesoc_wishbone_interface_sram2_we[0] = (((main_basesoc_wishbone_interface_interface2_cyc & main_basesoc_wishbone_interface_interface2_stb) & main_basesoc_wishbone_interface_interface2_we) & main_basesoc_wishbone_interface_interface2_sel[0]);
    main_basesoc_wishbone_interface_sram2_we[1] = (((main_basesoc_wishbone_interface_interface2_cyc & main_basesoc_wishbone_interface_interface2_stb) & main_basesoc_wishbone_interface_interface2_we) & main_basesoc_wishbone_interface_interface2_sel[1]);
    main_basesoc_wishbone_interface_sram2_we[2] = (((main_basesoc_wishbone_interface_interface2_cyc & main_basesoc_wishbone_interface_interface2_stb) & main_basesoc_wishbone_interface_interface2_we) & main_basesoc_wishbone_interface_interface2_sel[2]);
    main_basesoc_wishbone_interface_sram2_we[3] = (((main_basesoc_wishbone_interface_interface2_cyc & main_basesoc_wishbone_interface_interface2_stb) & main_basesoc_wishbone_interface_interface2_we) & main_basesoc_wishbone_interface_interface2_sel[3]);
end
assign main_basesoc_wishbone_interface_sram2_adr = main_basesoc_wishbone_interface_interface2_adr[8:0];
assign main_basesoc_wishbone_interface_interface2_dat_r = main_basesoc_wishbone_interface_sram2_dat_r;
assign main_basesoc_wishbone_interface_sram2_dat_w = main_basesoc_wishbone_interface_interface2_dat_w;
always @(*) begin
    main_basesoc_wishbone_interface_sram3_we = 4'd0;
    main_basesoc_wishbone_interface_sram3_we[0] = (((main_basesoc_wishbone_interface_interface3_cyc & main_basesoc_wishbone_interface_interface3_stb) & main_basesoc_wishbone_interface_interface3_we) & main_basesoc_wishbone_interface_interface3_sel[0]);
    main_basesoc_wishbone_interface_sram3_we[1] = (((main_basesoc_wishbone_interface_interface3_cyc & main_basesoc_wishbone_interface_interface3_stb) & main_basesoc_wishbone_interface_interface3_we) & main_basesoc_wishbone_interface_interface3_sel[1]);
    main_basesoc_wishbone_interface_sram3_we[2] = (((main_basesoc_wishbone_interface_interface3_cyc & main_basesoc_wishbone_interface_interface3_stb) & main_basesoc_wishbone_interface_interface3_we) & main_basesoc_wishbone_interface_interface3_sel[2]);
    main_basesoc_wishbone_interface_sram3_we[3] = (((main_basesoc_wishbone_interface_interface3_cyc & main_basesoc_wishbone_interface_interface3_stb) & main_basesoc_wishbone_interface_interface3_we) & main_basesoc_wishbone_interface_interface3_sel[3]);
end
assign main_basesoc_wishbone_interface_sram3_adr = main_basesoc_wishbone_interface_interface3_adr[8:0];
assign main_basesoc_wishbone_interface_interface3_dat_r = main_basesoc_wishbone_interface_sram3_dat_r;
assign main_basesoc_wishbone_interface_sram3_dat_w = main_basesoc_wishbone_interface_interface3_dat_w;
always @(*) begin
    main_basesoc_wishbone_interface_decoder1_slave_sel = 2'd0;
    main_basesoc_wishbone_interface_decoder1_slave_sel[0] = (main_basesoc_wishbone_interface_bus_tx_adr[9] == 1'd0);
    main_basesoc_wishbone_interface_decoder1_slave_sel[1] = (main_basesoc_wishbone_interface_bus_tx_adr[9] == 1'd1);
end
assign main_basesoc_wishbone_interface_interface2_adr = main_basesoc_wishbone_interface_bus_tx_adr;
assign main_basesoc_wishbone_interface_interface2_dat_w = main_basesoc_wishbone_interface_bus_tx_dat_w;
assign main_basesoc_wishbone_interface_interface2_sel = main_basesoc_wishbone_interface_bus_tx_sel;
assign main_basesoc_wishbone_interface_interface2_stb = main_basesoc_wishbone_interface_bus_tx_stb;
assign main_basesoc_wishbone_interface_interface2_we = main_basesoc_wishbone_interface_bus_tx_we;
assign main_basesoc_wishbone_interface_interface2_cti = main_basesoc_wishbone_interface_bus_tx_cti;
assign main_basesoc_wishbone_interface_interface2_bte = main_basesoc_wishbone_interface_bus_tx_bte;
assign main_basesoc_wishbone_interface_interface3_adr = main_basesoc_wishbone_interface_bus_tx_adr;
assign main_basesoc_wishbone_interface_interface3_dat_w = main_basesoc_wishbone_interface_bus_tx_dat_w;
assign main_basesoc_wishbone_interface_interface3_sel = main_basesoc_wishbone_interface_bus_tx_sel;
assign main_basesoc_wishbone_interface_interface3_stb = main_basesoc_wishbone_interface_bus_tx_stb;
assign main_basesoc_wishbone_interface_interface3_we = main_basesoc_wishbone_interface_bus_tx_we;
assign main_basesoc_wishbone_interface_interface3_cti = main_basesoc_wishbone_interface_bus_tx_cti;
assign main_basesoc_wishbone_interface_interface3_bte = main_basesoc_wishbone_interface_bus_tx_bte;
assign main_basesoc_wishbone_interface_interface2_cyc = (main_basesoc_wishbone_interface_bus_tx_cyc & main_basesoc_wishbone_interface_decoder1_slave_sel[0]);
assign main_basesoc_wishbone_interface_interface3_cyc = (main_basesoc_wishbone_interface_bus_tx_cyc & main_basesoc_wishbone_interface_decoder1_slave_sel[1]);
assign main_basesoc_wishbone_interface_bus_tx_ack = (main_basesoc_wishbone_interface_interface2_ack | main_basesoc_wishbone_interface_interface3_ack);
assign main_basesoc_wishbone_interface_bus_tx_err = (main_basesoc_wishbone_interface_interface2_err | main_basesoc_wishbone_interface_interface3_err);
assign main_basesoc_wishbone_interface_bus_tx_dat_r = (({32{main_basesoc_wishbone_interface_decoder1_slave_sel_r[0]}} & main_basesoc_wishbone_interface_interface2_dat_r) | ({32{main_basesoc_wishbone_interface_decoder1_slave_sel_r[1]}} & main_basesoc_wishbone_interface_interface3_dat_r));
assign main_wait = (~main_done);
always @(*) begin
    main_leds = 8'd0;
    if ((main_mode == 1'd1)) begin
        main_leds = main_storage;
    end else begin
        main_leds = main_chaser;
    end
end
assign {user_led7, user_led6, user_led5, user_led4, user_led3, user_led2, user_led1, user_led0} = (main_leds ^ 1'd0);
assign main_done = (main_count == 1'd0);
always @(*) begin
    builder_csr_data_width = 1'd0;
    builder_csr_data_width = 1'd0;
    if ((builder_interface0_sel != 1'd0)) begin
        builder_csr_data_width = 1'd0;
    end
end
always @(*) begin
    builder_interface0_ack = 1'd0;
    builder_interface0_dat_r = 32'd0;
    builder_interface1_adr = 14'd0;
    builder_interface1_dat_w = 32'd0;
    builder_interface1_re = 1'd0;
    builder_interface1_we = 1'd0;
    builder_wishbone2csr_next_state = 1'd0;
    builder_wishbone2csr_next_state = builder_wishbone2csr_state;
    case (builder_wishbone2csr_state)
        1'd1: begin
            builder_interface0_ack = 1'd1;
            builder_interface0_dat_r = 1'd0;
            case (builder_csr_data_width)
                1'd0: begin
                    builder_interface0_dat_r = builder_interface1_dat_r;
                end
            endcase
            builder_wishbone2csr_next_state = 1'd0;
        end
        default: begin
            builder_interface1_dat_w = builder_basiclowerer_self;
            if ((builder_interface0_cyc & builder_interface0_stb)) begin
                builder_interface1_adr = builder_interface0_adr;
                builder_interface1_re = ((~builder_interface0_we) & (builder_interface0_sel != 1'd0));
                builder_interface1_we = (builder_interface0_we & (builder_interface0_sel != 1'd0));
                builder_wishbone2csr_next_state = 1'd1;
            end
        end
    endcase
end
assign builder_csr_bankarray_csrbank0_sel = (builder_csr_bankarray_interface0_bank_bus_adr[13:9] == 1'd0);
assign builder_csr_bankarray_csrbank0_reset_r = builder_csr_bankarray_interface0_bank_bus_dat_w[1:0];
always @(*) begin
    builder_csr_bankarray_csrbank0_reset_re = 1'd0;
    builder_csr_bankarray_csrbank0_reset_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 1'd0))) begin
        builder_csr_bankarray_csrbank0_reset_re = builder_csr_bankarray_interface0_bank_bus_we;
        builder_csr_bankarray_csrbank0_reset_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank0_scratch_r = builder_csr_bankarray_interface0_bank_bus_dat_w;
always @(*) begin
    builder_csr_bankarray_csrbank0_scratch_re = 1'd0;
    builder_csr_bankarray_csrbank0_scratch_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 1'd1))) begin
        builder_csr_bankarray_csrbank0_scratch_re = builder_csr_bankarray_interface0_bank_bus_we;
        builder_csr_bankarray_csrbank0_scratch_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank0_bus_errors_r = builder_csr_bankarray_interface0_bank_bus_dat_w;
always @(*) begin
    builder_csr_bankarray_csrbank0_bus_errors_re = 1'd0;
    builder_csr_bankarray_csrbank0_bus_errors_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 2'd2))) begin
        builder_csr_bankarray_csrbank0_bus_errors_re = builder_csr_bankarray_interface0_bank_bus_we;
        builder_csr_bankarray_csrbank0_bus_errors_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
always @(*) begin
    main_basesoc_soc_rst = 1'd0;
    if (main_basesoc_reset_wr_stb) begin
        main_basesoc_soc_rst = main_basesoc_reset_storage[0];
    end
end
assign main_basesoc_cpu_rst = main_basesoc_reset_storage[1];
assign builder_csr_bankarray_csrbank0_reset_w = main_basesoc_reset_storage;
assign builder_csr_bankarray_csrbank0_scratch_w = main_basesoc_scratch_storage;
assign builder_csr_bankarray_csrbank0_bus_errors_w = main_basesoc_bus_errors_status;
assign main_basesoc_bus_errors_rd_stb = builder_csr_bankarray_csrbank0_bus_errors_we;
assign builder_csr_bankarray_csrbank1_sel = (builder_csr_bankarray_interface1_bank_bus_adr[13:9] == 1'd1);
assign builder_csr_bankarray_csrbank1_sram_writer_slot_r = builder_csr_bankarray_interface1_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank1_sram_writer_slot_re = 1'd0;
    builder_csr_bankarray_csrbank1_sram_writer_slot_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 1'd0))) begin
        builder_csr_bankarray_csrbank1_sram_writer_slot_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_sram_writer_slot_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_sram_writer_length_r = builder_csr_bankarray_interface1_bank_bus_dat_w[10:0];
always @(*) begin
    builder_csr_bankarray_csrbank1_sram_writer_length_re = 1'd0;
    builder_csr_bankarray_csrbank1_sram_writer_length_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 1'd1))) begin
        builder_csr_bankarray_csrbank1_sram_writer_length_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_sram_writer_length_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_sram_writer_errors_r = builder_csr_bankarray_interface1_bank_bus_dat_w;
always @(*) begin
    builder_csr_bankarray_csrbank1_sram_writer_errors_re = 1'd0;
    builder_csr_bankarray_csrbank1_sram_writer_errors_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 2'd2))) begin
        builder_csr_bankarray_csrbank1_sram_writer_errors_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_sram_writer_errors_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_sram_writer_ev_status_r = builder_csr_bankarray_interface1_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank1_sram_writer_ev_status_re = 1'd0;
    builder_csr_bankarray_csrbank1_sram_writer_ev_status_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 2'd3))) begin
        builder_csr_bankarray_csrbank1_sram_writer_ev_status_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_sram_writer_ev_status_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_sram_writer_ev_pending_r = builder_csr_bankarray_interface1_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank1_sram_writer_ev_pending_re = 1'd0;
    builder_csr_bankarray_csrbank1_sram_writer_ev_pending_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 3'd4))) begin
        builder_csr_bankarray_csrbank1_sram_writer_ev_pending_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_sram_writer_ev_pending_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_sram_writer_ev_enable_r = builder_csr_bankarray_interface1_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank1_sram_writer_ev_enable_re = 1'd0;
    builder_csr_bankarray_csrbank1_sram_writer_ev_enable_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 3'd5))) begin
        builder_csr_bankarray_csrbank1_sram_writer_ev_enable_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_sram_writer_ev_enable_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign main_basesoc_wishbone_interface_reader_start_r = builder_csr_bankarray_interface1_bank_bus_dat_w[0];
always @(*) begin
    main_basesoc_wishbone_interface_reader_start_re = 1'd0;
    main_basesoc_wishbone_interface_reader_start_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 3'd6))) begin
        main_basesoc_wishbone_interface_reader_start_re = builder_csr_bankarray_interface1_bank_bus_we;
        main_basesoc_wishbone_interface_reader_start_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_sram_reader_ready_r = builder_csr_bankarray_interface1_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank1_sram_reader_ready_re = 1'd0;
    builder_csr_bankarray_csrbank1_sram_reader_ready_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 3'd7))) begin
        builder_csr_bankarray_csrbank1_sram_reader_ready_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_sram_reader_ready_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_sram_reader_level_r = builder_csr_bankarray_interface1_bank_bus_dat_w[1:0];
always @(*) begin
    builder_csr_bankarray_csrbank1_sram_reader_level_re = 1'd0;
    builder_csr_bankarray_csrbank1_sram_reader_level_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 4'd8))) begin
        builder_csr_bankarray_csrbank1_sram_reader_level_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_sram_reader_level_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_sram_reader_slot_r = builder_csr_bankarray_interface1_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank1_sram_reader_slot_re = 1'd0;
    builder_csr_bankarray_csrbank1_sram_reader_slot_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 4'd9))) begin
        builder_csr_bankarray_csrbank1_sram_reader_slot_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_sram_reader_slot_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_sram_reader_length_r = builder_csr_bankarray_interface1_bank_bus_dat_w[10:0];
always @(*) begin
    builder_csr_bankarray_csrbank1_sram_reader_length_re = 1'd0;
    builder_csr_bankarray_csrbank1_sram_reader_length_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 4'd10))) begin
        builder_csr_bankarray_csrbank1_sram_reader_length_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_sram_reader_length_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_sram_reader_ev_status_r = builder_csr_bankarray_interface1_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank1_sram_reader_ev_status_re = 1'd0;
    builder_csr_bankarray_csrbank1_sram_reader_ev_status_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 4'd11))) begin
        builder_csr_bankarray_csrbank1_sram_reader_ev_status_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_sram_reader_ev_status_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_sram_reader_ev_pending_r = builder_csr_bankarray_interface1_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank1_sram_reader_ev_pending_re = 1'd0;
    builder_csr_bankarray_csrbank1_sram_reader_ev_pending_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 4'd12))) begin
        builder_csr_bankarray_csrbank1_sram_reader_ev_pending_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_sram_reader_ev_pending_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_sram_reader_ev_enable_r = builder_csr_bankarray_interface1_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank1_sram_reader_ev_enable_re = 1'd0;
    builder_csr_bankarray_csrbank1_sram_reader_ev_enable_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 4'd13))) begin
        builder_csr_bankarray_csrbank1_sram_reader_ev_enable_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_sram_reader_ev_enable_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_preamble_crc_r = builder_csr_bankarray_interface1_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank1_preamble_crc_re = 1'd0;
    builder_csr_bankarray_csrbank1_preamble_crc_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 4'd14))) begin
        builder_csr_bankarray_csrbank1_preamble_crc_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_preamble_crc_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_rx_datapath_preamble_errors_r = builder_csr_bankarray_interface1_bank_bus_dat_w;
always @(*) begin
    builder_csr_bankarray_csrbank1_rx_datapath_preamble_errors_re = 1'd0;
    builder_csr_bankarray_csrbank1_rx_datapath_preamble_errors_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 4'd15))) begin
        builder_csr_bankarray_csrbank1_rx_datapath_preamble_errors_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_rx_datapath_preamble_errors_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_rx_datapath_crc_errors_r = builder_csr_bankarray_interface1_bank_bus_dat_w;
always @(*) begin
    builder_csr_bankarray_csrbank1_rx_datapath_crc_errors_re = 1'd0;
    builder_csr_bankarray_csrbank1_rx_datapath_crc_errors_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 5'd16))) begin
        builder_csr_bankarray_csrbank1_rx_datapath_crc_errors_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_rx_datapath_crc_errors_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_sram_writer_slot_w = main_basesoc_wishbone_interface_writer_slot_status;
assign main_basesoc_wishbone_interface_writer_slot_rd_stb = builder_csr_bankarray_csrbank1_sram_writer_slot_we;
assign builder_csr_bankarray_csrbank1_sram_writer_length_w = main_basesoc_wishbone_interface_writer_length_status;
assign main_basesoc_wishbone_interface_writer_length_rd_stb = builder_csr_bankarray_csrbank1_sram_writer_length_we;
assign builder_csr_bankarray_csrbank1_sram_writer_errors_w = main_basesoc_wishbone_interface_writer_errors_status;
assign main_basesoc_wishbone_interface_writer_errors_rd_stb = builder_csr_bankarray_csrbank1_sram_writer_errors_we;
assign main_basesoc_wishbone_interface_writer_status_status = main_basesoc_wishbone_interface_writer_available0;
assign builder_csr_bankarray_csrbank1_sram_writer_ev_status_w = main_basesoc_wishbone_interface_writer_status_status;
assign main_basesoc_wishbone_interface_writer_status_rd_stb = builder_csr_bankarray_csrbank1_sram_writer_ev_status_we;
assign main_basesoc_wishbone_interface_writer_pending_status = main_basesoc_wishbone_interface_writer_available1;
assign builder_csr_bankarray_csrbank1_sram_writer_ev_pending_w = main_basesoc_wishbone_interface_writer_pending_status;
assign main_basesoc_wishbone_interface_writer_pending_rd_stb = builder_csr_bankarray_csrbank1_sram_writer_ev_pending_we;
assign main_basesoc_wishbone_interface_writer_available2 = main_basesoc_wishbone_interface_writer_enable_storage;
assign builder_csr_bankarray_csrbank1_sram_writer_ev_enable_w = main_basesoc_wishbone_interface_writer_enable_storage;
assign builder_csr_bankarray_csrbank1_sram_reader_ready_w = main_basesoc_wishbone_interface_reader_ready_status;
assign main_basesoc_wishbone_interface_reader_ready_rd_stb = builder_csr_bankarray_csrbank1_sram_reader_ready_we;
assign builder_csr_bankarray_csrbank1_sram_reader_level_w = main_basesoc_wishbone_interface_reader_level_status;
assign main_basesoc_wishbone_interface_reader_level_rd_stb = builder_csr_bankarray_csrbank1_sram_reader_level_we;
assign builder_csr_bankarray_csrbank1_sram_reader_slot_w = main_basesoc_wishbone_interface_reader_slot_storage;
assign builder_csr_bankarray_csrbank1_sram_reader_length_w = main_basesoc_wishbone_interface_reader_length_storage;
assign main_basesoc_wishbone_interface_reader_status_status = main_basesoc_wishbone_interface_reader_event00;
assign builder_csr_bankarray_csrbank1_sram_reader_ev_status_w = main_basesoc_wishbone_interface_reader_status_status;
assign main_basesoc_wishbone_interface_reader_status_rd_stb = builder_csr_bankarray_csrbank1_sram_reader_ev_status_we;
assign main_basesoc_wishbone_interface_reader_pending_status = main_basesoc_wishbone_interface_reader_event01;
assign builder_csr_bankarray_csrbank1_sram_reader_ev_pending_w = main_basesoc_wishbone_interface_reader_pending_status;
assign main_basesoc_wishbone_interface_reader_pending_rd_stb = builder_csr_bankarray_csrbank1_sram_reader_ev_pending_we;
assign main_basesoc_wishbone_interface_reader_event02 = main_basesoc_wishbone_interface_reader_enable_storage;
assign builder_csr_bankarray_csrbank1_sram_reader_ev_enable_w = main_basesoc_wishbone_interface_reader_enable_storage;
assign builder_csr_bankarray_csrbank1_preamble_crc_w = main_basesoc_core_status;
assign main_basesoc_core_rd_stb = builder_csr_bankarray_csrbank1_preamble_crc_we;
assign builder_csr_bankarray_csrbank1_rx_datapath_preamble_errors_w = main_basesoc_core_preamble_errors_status;
assign main_basesoc_core_preamble_errors_rd_stb = builder_csr_bankarray_csrbank1_rx_datapath_preamble_errors_we;
assign builder_csr_bankarray_csrbank1_rx_datapath_crc_errors_w = main_basesoc_core_crc_errors_status;
assign main_basesoc_core_crc_errors_rd_stb = builder_csr_bankarray_csrbank1_rx_datapath_crc_errors_we;
assign builder_csr_bankarray_csrbank2_sel = (builder_csr_bankarray_interface2_bank_bus_adr[13:9] == 2'd2);
assign builder_csr_bankarray_csrbank2_crg_reset_r = builder_csr_bankarray_interface2_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank2_crg_reset_re = 1'd0;
    builder_csr_bankarray_csrbank2_crg_reset_we = 1'd0;
    if ((builder_csr_bankarray_csrbank2_sel & (builder_csr_bankarray_interface2_bank_bus_adr[8:0] == 1'd0))) begin
        builder_csr_bankarray_csrbank2_crg_reset_re = builder_csr_bankarray_interface2_bank_bus_we;
        builder_csr_bankarray_csrbank2_crg_reset_we = builder_csr_bankarray_interface2_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank2_mdio_w_r = builder_csr_bankarray_interface2_bank_bus_dat_w[2:0];
always @(*) begin
    builder_csr_bankarray_csrbank2_mdio_w_re = 1'd0;
    builder_csr_bankarray_csrbank2_mdio_w_we = 1'd0;
    if ((builder_csr_bankarray_csrbank2_sel & (builder_csr_bankarray_interface2_bank_bus_adr[8:0] == 1'd1))) begin
        builder_csr_bankarray_csrbank2_mdio_w_re = builder_csr_bankarray_interface2_bank_bus_we;
        builder_csr_bankarray_csrbank2_mdio_w_we = builder_csr_bankarray_interface2_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank2_mdio_r_r = builder_csr_bankarray_interface2_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank2_mdio_r_re = 1'd0;
    builder_csr_bankarray_csrbank2_mdio_r_we = 1'd0;
    if ((builder_csr_bankarray_csrbank2_sel & (builder_csr_bankarray_interface2_bank_bus_adr[8:0] == 2'd2))) begin
        builder_csr_bankarray_csrbank2_mdio_r_re = builder_csr_bankarray_interface2_bank_bus_we;
        builder_csr_bankarray_csrbank2_mdio_r_we = builder_csr_bankarray_interface2_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank2_crg_reset_w = main_ethphy_reset_storage;
assign main_ethphy_mdc = main_ethphy__w_storage[0];
assign main_ethphy_oe = main_ethphy__w_storage[1];
assign main_ethphy_w = main_ethphy__w_storage[2];
assign builder_csr_bankarray_csrbank2_mdio_w_w = main_ethphy__w_storage;
assign main_ethphy__r_status = main_ethphy_r;
assign builder_csr_bankarray_csrbank2_mdio_r_w = main_ethphy__r_status;
assign main_ethphy__r_rd_stb = builder_csr_bankarray_csrbank2_mdio_r_we;
assign builder_csr_bankarray_sel = (builder_csr_bankarray_sram_bus_adr[13:9] == 2'd3);
always @(*) begin
    builder_csr_bankarray_sram_bus_dat_r = 32'd0;
    if (builder_csr_bankarray_sel_r) begin
        builder_csr_bankarray_sram_bus_dat_r = builder_csr_bankarray_dat_r;
    end
end
assign builder_csr_bankarray_adr = builder_csr_bankarray_sram_bus_adr[5:0];
assign builder_csr_bankarray_csrbank3_sel = (builder_csr_bankarray_interface3_bank_bus_adr[13:9] == 3'd4);
assign builder_csr_bankarray_csrbank3_out_r = builder_csr_bankarray_interface3_bank_bus_dat_w[7:0];
always @(*) begin
    builder_csr_bankarray_csrbank3_out_re = 1'd0;
    builder_csr_bankarray_csrbank3_out_we = 1'd0;
    if ((builder_csr_bankarray_csrbank3_sel & (builder_csr_bankarray_interface3_bank_bus_adr[8:0] == 1'd0))) begin
        builder_csr_bankarray_csrbank3_out_re = builder_csr_bankarray_interface3_bank_bus_we;
        builder_csr_bankarray_csrbank3_out_we = builder_csr_bankarray_interface3_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank3_out_w = main_storage;
assign builder_csr_bankarray_csrbank4_sel = (builder_csr_bankarray_interface4_bank_bus_adr[13:9] == 3'd5);
assign builder_csr_bankarray_csrbank4_load_r = builder_csr_bankarray_interface4_bank_bus_dat_w;
always @(*) begin
    builder_csr_bankarray_csrbank4_load_re = 1'd0;
    builder_csr_bankarray_csrbank4_load_we = 1'd0;
    if ((builder_csr_bankarray_csrbank4_sel & (builder_csr_bankarray_interface4_bank_bus_adr[8:0] == 1'd0))) begin
        builder_csr_bankarray_csrbank4_load_re = builder_csr_bankarray_interface4_bank_bus_we;
        builder_csr_bankarray_csrbank4_load_we = builder_csr_bankarray_interface4_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank4_reload_r = builder_csr_bankarray_interface4_bank_bus_dat_w;
always @(*) begin
    builder_csr_bankarray_csrbank4_reload_re = 1'd0;
    builder_csr_bankarray_csrbank4_reload_we = 1'd0;
    if ((builder_csr_bankarray_csrbank4_sel & (builder_csr_bankarray_interface4_bank_bus_adr[8:0] == 1'd1))) begin
        builder_csr_bankarray_csrbank4_reload_re = builder_csr_bankarray_interface4_bank_bus_we;
        builder_csr_bankarray_csrbank4_reload_we = builder_csr_bankarray_interface4_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank4_en_r = builder_csr_bankarray_interface4_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank4_en_re = 1'd0;
    builder_csr_bankarray_csrbank4_en_we = 1'd0;
    if ((builder_csr_bankarray_csrbank4_sel & (builder_csr_bankarray_interface4_bank_bus_adr[8:0] == 2'd2))) begin
        builder_csr_bankarray_csrbank4_en_re = builder_csr_bankarray_interface4_bank_bus_we;
        builder_csr_bankarray_csrbank4_en_we = builder_csr_bankarray_interface4_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank4_update_value_r = builder_csr_bankarray_interface4_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank4_update_value_re = 1'd0;
    builder_csr_bankarray_csrbank4_update_value_we = 1'd0;
    if ((builder_csr_bankarray_csrbank4_sel & (builder_csr_bankarray_interface4_bank_bus_adr[8:0] == 2'd3))) begin
        builder_csr_bankarray_csrbank4_update_value_re = builder_csr_bankarray_interface4_bank_bus_we;
        builder_csr_bankarray_csrbank4_update_value_we = builder_csr_bankarray_interface4_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank4_value_r = builder_csr_bankarray_interface4_bank_bus_dat_w;
always @(*) begin
    builder_csr_bankarray_csrbank4_value_re = 1'd0;
    builder_csr_bankarray_csrbank4_value_we = 1'd0;
    if ((builder_csr_bankarray_csrbank4_sel & (builder_csr_bankarray_interface4_bank_bus_adr[8:0] == 3'd4))) begin
        builder_csr_bankarray_csrbank4_value_re = builder_csr_bankarray_interface4_bank_bus_we;
        builder_csr_bankarray_csrbank4_value_we = builder_csr_bankarray_interface4_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank4_ev_status_r = builder_csr_bankarray_interface4_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank4_ev_status_re = 1'd0;
    builder_csr_bankarray_csrbank4_ev_status_we = 1'd0;
    if ((builder_csr_bankarray_csrbank4_sel & (builder_csr_bankarray_interface4_bank_bus_adr[8:0] == 3'd5))) begin
        builder_csr_bankarray_csrbank4_ev_status_re = builder_csr_bankarray_interface4_bank_bus_we;
        builder_csr_bankarray_csrbank4_ev_status_we = builder_csr_bankarray_interface4_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank4_ev_pending_r = builder_csr_bankarray_interface4_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank4_ev_pending_re = 1'd0;
    builder_csr_bankarray_csrbank4_ev_pending_we = 1'd0;
    if ((builder_csr_bankarray_csrbank4_sel & (builder_csr_bankarray_interface4_bank_bus_adr[8:0] == 3'd6))) begin
        builder_csr_bankarray_csrbank4_ev_pending_re = builder_csr_bankarray_interface4_bank_bus_we;
        builder_csr_bankarray_csrbank4_ev_pending_we = builder_csr_bankarray_interface4_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank4_ev_enable_r = builder_csr_bankarray_interface4_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank4_ev_enable_re = 1'd0;
    builder_csr_bankarray_csrbank4_ev_enable_we = 1'd0;
    if ((builder_csr_bankarray_csrbank4_sel & (builder_csr_bankarray_interface4_bank_bus_adr[8:0] == 3'd7))) begin
        builder_csr_bankarray_csrbank4_ev_enable_re = builder_csr_bankarray_interface4_bank_bus_we;
        builder_csr_bankarray_csrbank4_ev_enable_we = builder_csr_bankarray_interface4_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank4_load_w = main_basesoc_timer_load_storage;
assign builder_csr_bankarray_csrbank4_reload_w = main_basesoc_timer_reload_storage;
assign builder_csr_bankarray_csrbank4_en_w = main_basesoc_timer_en_storage;
assign builder_csr_bankarray_csrbank4_update_value_w = main_basesoc_timer_update_value_storage;
assign builder_csr_bankarray_csrbank4_value_w = main_basesoc_timer_value_status;
assign main_basesoc_timer_value_rd_stb = builder_csr_bankarray_csrbank4_value_we;
assign main_basesoc_timer_status_status = main_basesoc_timer_zero0;
assign builder_csr_bankarray_csrbank4_ev_status_w = main_basesoc_timer_status_status;
assign main_basesoc_timer_status_rd_stb = builder_csr_bankarray_csrbank4_ev_status_we;
assign main_basesoc_timer_pending_status = main_basesoc_timer_zero1;
assign builder_csr_bankarray_csrbank4_ev_pending_w = main_basesoc_timer_pending_status;
assign main_basesoc_timer_pending_rd_stb = builder_csr_bankarray_csrbank4_ev_pending_we;
assign main_basesoc_timer_zero2 = main_basesoc_timer_enable_storage;
assign builder_csr_bankarray_csrbank4_ev_enable_w = main_basesoc_timer_enable_storage;
assign builder_csr_bankarray_csrbank5_sel = (builder_csr_bankarray_interface5_bank_bus_adr[13:9] == 3'd6);
assign main_basesoc_uart_core_rxtx_r = builder_csr_bankarray_interface5_bank_bus_dat_w[7:0];
always @(*) begin
    main_basesoc_uart_core_rxtx_re = 1'd0;
    main_basesoc_uart_core_rxtx_we = 1'd0;
    if ((builder_csr_bankarray_csrbank5_sel & (builder_csr_bankarray_interface5_bank_bus_adr[8:0] == 1'd0))) begin
        main_basesoc_uart_core_rxtx_re = builder_csr_bankarray_interface5_bank_bus_we;
        main_basesoc_uart_core_rxtx_we = builder_csr_bankarray_interface5_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank5_txfull_r = builder_csr_bankarray_interface5_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank5_txfull_re = 1'd0;
    builder_csr_bankarray_csrbank5_txfull_we = 1'd0;
    if ((builder_csr_bankarray_csrbank5_sel & (builder_csr_bankarray_interface5_bank_bus_adr[8:0] == 1'd1))) begin
        builder_csr_bankarray_csrbank5_txfull_re = builder_csr_bankarray_interface5_bank_bus_we;
        builder_csr_bankarray_csrbank5_txfull_we = builder_csr_bankarray_interface5_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank5_rxempty_r = builder_csr_bankarray_interface5_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank5_rxempty_re = 1'd0;
    builder_csr_bankarray_csrbank5_rxempty_we = 1'd0;
    if ((builder_csr_bankarray_csrbank5_sel & (builder_csr_bankarray_interface5_bank_bus_adr[8:0] == 2'd2))) begin
        builder_csr_bankarray_csrbank5_rxempty_re = builder_csr_bankarray_interface5_bank_bus_we;
        builder_csr_bankarray_csrbank5_rxempty_we = builder_csr_bankarray_interface5_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank5_ev_status_r = builder_csr_bankarray_interface5_bank_bus_dat_w[1:0];
always @(*) begin
    builder_csr_bankarray_csrbank5_ev_status_re = 1'd0;
    builder_csr_bankarray_csrbank5_ev_status_we = 1'd0;
    if ((builder_csr_bankarray_csrbank5_sel & (builder_csr_bankarray_interface5_bank_bus_adr[8:0] == 2'd3))) begin
        builder_csr_bankarray_csrbank5_ev_status_re = builder_csr_bankarray_interface5_bank_bus_we;
        builder_csr_bankarray_csrbank5_ev_status_we = builder_csr_bankarray_interface5_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank5_ev_pending_r = builder_csr_bankarray_interface5_bank_bus_dat_w[1:0];
always @(*) begin
    builder_csr_bankarray_csrbank5_ev_pending_re = 1'd0;
    builder_csr_bankarray_csrbank5_ev_pending_we = 1'd0;
    if ((builder_csr_bankarray_csrbank5_sel & (builder_csr_bankarray_interface5_bank_bus_adr[8:0] == 3'd4))) begin
        builder_csr_bankarray_csrbank5_ev_pending_re = builder_csr_bankarray_interface5_bank_bus_we;
        builder_csr_bankarray_csrbank5_ev_pending_we = builder_csr_bankarray_interface5_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank5_ev_enable_r = builder_csr_bankarray_interface5_bank_bus_dat_w[1:0];
always @(*) begin
    builder_csr_bankarray_csrbank5_ev_enable_re = 1'd0;
    builder_csr_bankarray_csrbank5_ev_enable_we = 1'd0;
    if ((builder_csr_bankarray_csrbank5_sel & (builder_csr_bankarray_interface5_bank_bus_adr[8:0] == 3'd5))) begin
        builder_csr_bankarray_csrbank5_ev_enable_re = builder_csr_bankarray_interface5_bank_bus_we;
        builder_csr_bankarray_csrbank5_ev_enable_we = builder_csr_bankarray_interface5_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank5_txempty_r = builder_csr_bankarray_interface5_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank5_txempty_re = 1'd0;
    builder_csr_bankarray_csrbank5_txempty_we = 1'd0;
    if ((builder_csr_bankarray_csrbank5_sel & (builder_csr_bankarray_interface5_bank_bus_adr[8:0] == 3'd6))) begin
        builder_csr_bankarray_csrbank5_txempty_re = builder_csr_bankarray_interface5_bank_bus_we;
        builder_csr_bankarray_csrbank5_txempty_we = builder_csr_bankarray_interface5_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank5_rxfull_r = builder_csr_bankarray_interface5_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank5_rxfull_re = 1'd0;
    builder_csr_bankarray_csrbank5_rxfull_we = 1'd0;
    if ((builder_csr_bankarray_csrbank5_sel & (builder_csr_bankarray_interface5_bank_bus_adr[8:0] == 3'd7))) begin
        builder_csr_bankarray_csrbank5_rxfull_re = builder_csr_bankarray_interface5_bank_bus_we;
        builder_csr_bankarray_csrbank5_rxfull_we = builder_csr_bankarray_interface5_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank5_txfull_w = main_basesoc_uart_core_txfull_status;
assign main_basesoc_uart_core_txfull_rd_stb = builder_csr_bankarray_csrbank5_txfull_we;
assign builder_csr_bankarray_csrbank5_rxempty_w = main_basesoc_uart_core_rxempty_status;
assign main_basesoc_uart_core_rxempty_rd_stb = builder_csr_bankarray_csrbank5_rxempty_we;
always @(*) begin
    main_basesoc_uart_core_status_status = 2'd0;
    main_basesoc_uart_core_status_status[0] = main_basesoc_uart_core_tx0;
    main_basesoc_uart_core_status_status[1] = main_basesoc_uart_core_rx0;
end
assign builder_csr_bankarray_csrbank5_ev_status_w = main_basesoc_uart_core_status_status;
assign main_basesoc_uart_core_status_rd_stb = builder_csr_bankarray_csrbank5_ev_status_we;
always @(*) begin
    main_basesoc_uart_core_pending_status = 2'd0;
    main_basesoc_uart_core_pending_status[0] = main_basesoc_uart_core_tx1;
    main_basesoc_uart_core_pending_status[1] = main_basesoc_uart_core_rx1;
end
assign builder_csr_bankarray_csrbank5_ev_pending_w = main_basesoc_uart_core_pending_status;
assign main_basesoc_uart_core_pending_rd_stb = builder_csr_bankarray_csrbank5_ev_pending_we;
assign main_basesoc_uart_core_tx2 = main_basesoc_uart_core_enable_storage[0];
assign main_basesoc_uart_core_rx2 = main_basesoc_uart_core_enable_storage[1];
assign builder_csr_bankarray_csrbank5_ev_enable_w = main_basesoc_uart_core_enable_storage;
assign builder_csr_bankarray_csrbank5_txempty_w = main_basesoc_uart_core_txempty_status;
assign main_basesoc_uart_core_txempty_rd_stb = builder_csr_bankarray_csrbank5_txempty_we;
assign builder_csr_bankarray_csrbank5_rxfull_w = main_basesoc_uart_core_rxfull_status;
assign main_basesoc_uart_core_rxfull_rd_stb = builder_csr_bankarray_csrbank5_rxfull_we;
assign builder_csr_interconnect_adr = builder_interface1_adr;
assign builder_csr_interconnect_re = builder_interface1_re;
assign builder_csr_interconnect_we = builder_interface1_we;
assign builder_csr_interconnect_dat_w = builder_interface1_dat_w;
assign builder_interface1_dat_r = builder_csr_interconnect_dat_r;
assign builder_csr_bankarray_interface0_bank_bus_adr = builder_csr_interconnect_adr;
assign builder_csr_bankarray_interface1_bank_bus_adr = builder_csr_interconnect_adr;
assign builder_csr_bankarray_interface2_bank_bus_adr = builder_csr_interconnect_adr;
assign builder_csr_bankarray_interface3_bank_bus_adr = builder_csr_interconnect_adr;
assign builder_csr_bankarray_interface4_bank_bus_adr = builder_csr_interconnect_adr;
assign builder_csr_bankarray_interface5_bank_bus_adr = builder_csr_interconnect_adr;
assign builder_csr_bankarray_sram_bus_adr = builder_csr_interconnect_adr;
assign builder_csr_bankarray_interface0_bank_bus_re = builder_csr_interconnect_re;
assign builder_csr_bankarray_interface1_bank_bus_re = builder_csr_interconnect_re;
assign builder_csr_bankarray_interface2_bank_bus_re = builder_csr_interconnect_re;
assign builder_csr_bankarray_interface3_bank_bus_re = builder_csr_interconnect_re;
assign builder_csr_bankarray_interface4_bank_bus_re = builder_csr_interconnect_re;
assign builder_csr_bankarray_interface5_bank_bus_re = builder_csr_interconnect_re;
assign builder_csr_bankarray_sram_bus_re = builder_csr_interconnect_re;
assign builder_csr_bankarray_interface0_bank_bus_we = builder_csr_interconnect_we;
assign builder_csr_bankarray_interface1_bank_bus_we = builder_csr_interconnect_we;
assign builder_csr_bankarray_interface2_bank_bus_we = builder_csr_interconnect_we;
assign builder_csr_bankarray_interface3_bank_bus_we = builder_csr_interconnect_we;
assign builder_csr_bankarray_interface4_bank_bus_we = builder_csr_interconnect_we;
assign builder_csr_bankarray_interface5_bank_bus_we = builder_csr_interconnect_we;
assign builder_csr_bankarray_sram_bus_we = builder_csr_interconnect_we;
assign builder_csr_bankarray_interface0_bank_bus_dat_w = builder_csr_interconnect_dat_w;
assign builder_csr_bankarray_interface1_bank_bus_dat_w = builder_csr_interconnect_dat_w;
assign builder_csr_bankarray_interface2_bank_bus_dat_w = builder_csr_interconnect_dat_w;
assign builder_csr_bankarray_interface3_bank_bus_dat_w = builder_csr_interconnect_dat_w;
assign builder_csr_bankarray_interface4_bank_bus_dat_w = builder_csr_interconnect_dat_w;
assign builder_csr_bankarray_interface5_bank_bus_dat_w = builder_csr_interconnect_dat_w;
assign builder_csr_bankarray_sram_bus_dat_w = builder_csr_interconnect_dat_w;
assign builder_csr_interconnect_dat_r = ((((((builder_csr_bankarray_interface0_bank_bus_dat_r | builder_csr_bankarray_interface1_bank_bus_dat_r) | builder_csr_bankarray_interface2_bank_bus_dat_r) | builder_csr_bankarray_interface3_bank_bus_dat_r) | builder_csr_bankarray_interface4_bank_bus_dat_r) | builder_csr_bankarray_interface5_bank_bus_dat_r) | builder_csr_bankarray_sram_bus_dat_r);
always @(*) begin
    builder_rhs_self0 = 30'd0;
    case (builder_grant)
        1'd0: begin
            builder_rhs_self0 = main_basesoc_ibus_adr;
        end
        default: begin
            builder_rhs_self0 = main_basesoc_dbus_adr;
        end
    endcase
end
always @(*) begin
    builder_rhs_self1 = 32'd0;
    case (builder_grant)
        1'd0: begin
            builder_rhs_self1 = main_basesoc_ibus_dat_w;
        end
        default: begin
            builder_rhs_self1 = main_basesoc_dbus_dat_w;
        end
    endcase
end
always @(*) begin
    builder_rhs_self2 = 4'd0;
    case (builder_grant)
        1'd0: begin
            builder_rhs_self2 = main_basesoc_ibus_sel;
        end
        default: begin
            builder_rhs_self2 = main_basesoc_dbus_sel;
        end
    endcase
end
always @(*) begin
    builder_rhs_self3 = 1'd0;
    case (builder_grant)
        1'd0: begin
            builder_rhs_self3 = main_basesoc_ibus_cyc;
        end
        default: begin
            builder_rhs_self3 = main_basesoc_dbus_cyc;
        end
    endcase
end
always @(*) begin
    builder_rhs_self4 = 1'd0;
    case (builder_grant)
        1'd0: begin
            builder_rhs_self4 = main_basesoc_ibus_stb;
        end
        default: begin
            builder_rhs_self4 = main_basesoc_dbus_stb;
        end
    endcase
end
always @(*) begin
    builder_rhs_self5 = 1'd0;
    case (builder_grant)
        1'd0: begin
            builder_rhs_self5 = main_basesoc_ibus_we;
        end
        default: begin
            builder_rhs_self5 = main_basesoc_dbus_we;
        end
    endcase
end
always @(*) begin
    builder_rhs_self6 = 3'd0;
    case (builder_grant)
        1'd0: begin
            builder_rhs_self6 = main_basesoc_ibus_cti;
        end
        default: begin
            builder_rhs_self6 = main_basesoc_dbus_cti;
        end
    endcase
end
always @(*) begin
    builder_rhs_self7 = 2'd0;
    case (builder_grant)
        1'd0: begin
            builder_rhs_self7 = main_basesoc_ibus_bte;
        end
        default: begin
            builder_rhs_self7 = main_basesoc_dbus_bte;
        end
    endcase
end
always @(*) begin
    builder_basiclowerer_self = 32'd0;
    case (builder_csr_data_width)
        default: begin
            builder_basiclowerer_self = builder_interface0_dat_w;
        end
    endcase
end
assign builder_xilinxasyncresetsynchronizerimpl0_async_reset = (~main_crg_locked);
assign builder_xilinxasyncresetsynchronizerimpl1_async_reset = (~main_crg_locked);
assign builder_xilinxasyncresetsynchronizerimpl2_async_reset = (~main_crg_locked);
assign builder_xilinxasyncresetsynchronizerimpl3_async_reset = (~main_crg_locked);
assign builder_xilinxasyncresetsynchronizerimpl4_async_reset = (~main_crg_locked);
assign main_basesoc_uart_core_rx_rx = builder_xilinxmultiregimpl01;
assign builder_xilinxasyncresetsynchronizerimpl5_async_reset = (~main_ethphy_pll_locked);
assign main_ethphy_r = builder_xilinxmultiregimpl11;
assign main_basesoc_core_tx_cdc_write_ext_rst = builder_xilinxmultiregimpl21;
assign main_basesoc_core_tx_cdc_ext_rst_to = builder_xilinxmultiregimpl31;
assign main_basesoc_core_tx_cdc_cdc_produce_rdomain = builder_xilinxmultiregimpl41;
assign main_basesoc_core_tx_cdc_cdc_consume_wdomain = builder_xilinxmultiregimpl51;
assign main_basesoc_core_pulsesynchronizer0_toggle_o = builder_xilinxmultiregimpl61;
assign main_basesoc_core_pulsesynchronizer1_toggle_o = builder_xilinxmultiregimpl71;
assign main_basesoc_core_rx_cdc_write_ext_rst = builder_xilinxmultiregimpl81;
assign main_basesoc_core_rx_cdc_ext_rst_to = builder_xilinxmultiregimpl91;
assign main_basesoc_core_rx_cdc_cdc_produce_rdomain = builder_xilinxmultiregimpl101;
assign main_basesoc_core_rx_cdc_cdc_consume_wdomain = builder_xilinxmultiregimpl111;



always @(posedge eth_rx_clk) begin
    main_ethphy_rx_ctl_d <= main_ethphy_rx_ctl[0];
    main_ethphy_source_valid <= main_ethphy_rx_ctl[0];
    main_ethphy_source_payload_data <= main_ethphy_rx_data;
    if ((~main_ethphy_rx_ctl[0])) begin
        main_ethphy_source_payload_error <= 1'd0;
    end else begin
        if ((~main_ethphy_rx_ctl[1])) begin
            main_ethphy_source_payload_error <= 1'd1;
        end
    end
    builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_state <= builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_next_state;
    if (main_basesoc_core_pulsesynchronizer0_i) begin
        main_basesoc_core_pulsesynchronizer0_toggle_i <= (~main_basesoc_core_pulsesynchronizer0_toggle_i);
    end
    if (main_basesoc_core_liteethmaccrc32checker_is_ongoing2) begin
        main_basesoc_core_liteethmaccrc32checker_packet_error <= 1'd0;
    end else begin
        if ((main_basesoc_core_liteethmaccrc32checker_sink_sink_valid & main_basesoc_core_liteethmaccrc32checker_sink_sink_ready)) begin
            main_basesoc_core_liteethmaccrc32checker_packet_error <= (main_basesoc_core_liteethmaccrc32checker_packet_error | ((main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_error & main_basesoc_core_liteethmaccrc32checker_sink_sink_payload_be) != 1'd0));
        end
    end
    if (main_basesoc_core_liteethmaccrc32checker_crc_ce) begin
        main_basesoc_core_liteethmaccrc32checker_crc_reg <= main_basesoc_core_liteethmaccrc32checker_crc_crc_next;
    end
    if (main_basesoc_core_liteethmaccrc32checker_crc_reset) begin
        main_basesoc_core_liteethmaccrc32checker_crc_reg <= 32'hffffffff;
    end
    if (((main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_we & main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_writable) & (~main_basesoc_core_liteethmaccrc32checker_syncfifo_replace))) begin
        if ((main_basesoc_core_liteethmaccrc32checker_syncfifo_produce == 3'd4)) begin
            main_basesoc_core_liteethmaccrc32checker_syncfifo_produce <= 1'd0;
        end else begin
            main_basesoc_core_liteethmaccrc32checker_syncfifo_produce <= (main_basesoc_core_liteethmaccrc32checker_syncfifo_produce + 1'd1);
        end
    end
    if (main_basesoc_core_liteethmaccrc32checker_syncfifo_do_read) begin
        if ((main_basesoc_core_liteethmaccrc32checker_syncfifo_consume == 3'd4)) begin
            main_basesoc_core_liteethmaccrc32checker_syncfifo_consume <= 1'd0;
        end else begin
            main_basesoc_core_liteethmaccrc32checker_syncfifo_consume <= (main_basesoc_core_liteethmaccrc32checker_syncfifo_consume + 1'd1);
        end
    end
    if (((main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_we & main_basesoc_core_liteethmaccrc32checker_syncfifo_syncfifo_writable) & (~main_basesoc_core_liteethmaccrc32checker_syncfifo_replace))) begin
        if ((~main_basesoc_core_liteethmaccrc32checker_syncfifo_do_read)) begin
            main_basesoc_core_liteethmaccrc32checker_syncfifo_level <= (main_basesoc_core_liteethmaccrc32checker_syncfifo_level + 1'd1);
        end
    end else begin
        if (main_basesoc_core_liteethmaccrc32checker_syncfifo_do_read) begin
            main_basesoc_core_liteethmaccrc32checker_syncfifo_level <= (main_basesoc_core_liteethmaccrc32checker_syncfifo_level - 1'd1);
        end
    end
    if (main_basesoc_core_liteethmaccrc32checker_fifo_reset) begin
        main_basesoc_core_liteethmaccrc32checker_syncfifo_level <= 3'd0;
        main_basesoc_core_liteethmaccrc32checker_syncfifo_produce <= 3'd0;
        main_basesoc_core_liteethmaccrc32checker_syncfifo_consume <= 3'd0;
    end
    builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state <= builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_next_state;
    if (main_basesoc_core_liteethmaccrc32checker_be_next_value_ce0) begin
        main_basesoc_core_liteethmaccrc32checker_be <= main_basesoc_core_liteethmaccrc32checker_be_next_value0;
    end
    if (main_basesoc_core_liteethmaccrc32checker_last_error_next_value_ce1) begin
        main_basesoc_core_liteethmaccrc32checker_last_error <= main_basesoc_core_liteethmaccrc32checker_last_error_next_value1;
    end
    if (((~main_basesoc_core_bufferizeendpoints_pipe_valid_source_valid) | main_basesoc_core_bufferizeendpoints_pipe_valid_source_ready)) begin
        main_basesoc_core_bufferizeendpoints_pipe_valid_source_valid <= main_basesoc_core_bufferizeendpoints_pipe_valid_sink_valid;
        main_basesoc_core_bufferizeendpoints_pipe_valid_source_first <= main_basesoc_core_bufferizeendpoints_pipe_valid_sink_first;
        main_basesoc_core_bufferizeendpoints_pipe_valid_source_last <= main_basesoc_core_bufferizeendpoints_pipe_valid_sink_last;
        main_basesoc_core_bufferizeendpoints_pipe_valid_source_payload_data <= main_basesoc_core_bufferizeendpoints_pipe_valid_sink_payload_data;
        main_basesoc_core_bufferizeendpoints_pipe_valid_source_payload_be <= main_basesoc_core_bufferizeendpoints_pipe_valid_sink_payload_be;
        main_basesoc_core_bufferizeendpoints_pipe_valid_source_payload_error <= main_basesoc_core_bufferizeendpoints_pipe_valid_sink_payload_error;
    end
    if (main_basesoc_core_pulsesynchronizer1_i) begin
        main_basesoc_core_pulsesynchronizer1_toggle_i <= (~main_basesoc_core_pulsesynchronizer1_toggle_i);
    end
    if ((main_basesoc_core_rx_padding_sink_valid & main_basesoc_core_rx_padding_sink_ready)) begin
        if (main_basesoc_core_rx_padding_sink_last) begin
            main_basesoc_core_rx_padding_length <= 1'd0;
        end else begin
            main_basesoc_core_rx_padding_length <= (main_basesoc_core_rx_padding_length + main_basesoc_core_rx_padding_length_inc);
        end
    end
    if ((main_basesoc_core_rx_converter_converter_sink_valid & main_basesoc_core_rx_converter_converter_sink_ready)) begin
    end
    if (main_basesoc_core_rx_converter_converter_source_ready) begin
        main_basesoc_core_rx_converter_converter_strobe_all <= 1'd0;
    end
    if (main_basesoc_core_rx_converter_converter_load_part) begin
        if (((main_basesoc_core_rx_converter_converter_demux == 2'd3) | main_basesoc_core_rx_converter_converter_sink_last)) begin
            main_basesoc_core_rx_converter_converter_demux <= 1'd0;
            main_basesoc_core_rx_converter_converter_strobe_all <= 1'd1;
        end else begin
            main_basesoc_core_rx_converter_converter_demux <= (main_basesoc_core_rx_converter_converter_demux + 1'd1);
        end
    end
    if ((main_basesoc_core_rx_converter_converter_source_valid & main_basesoc_core_rx_converter_converter_source_ready)) begin
        if ((main_basesoc_core_rx_converter_converter_sink_valid & main_basesoc_core_rx_converter_converter_sink_ready)) begin
            main_basesoc_core_rx_converter_converter_source_first <= main_basesoc_core_rx_converter_converter_sink_first;
            main_basesoc_core_rx_converter_converter_source_last <= main_basesoc_core_rx_converter_converter_sink_last;
        end else begin
            main_basesoc_core_rx_converter_converter_source_first <= 1'd0;
            main_basesoc_core_rx_converter_converter_source_last <= 1'd0;
        end
    end else begin
        if ((main_basesoc_core_rx_converter_converter_sink_valid & main_basesoc_core_rx_converter_converter_sink_ready)) begin
            main_basesoc_core_rx_converter_converter_source_first <= (main_basesoc_core_rx_converter_converter_sink_first | main_basesoc_core_rx_converter_converter_source_first);
            main_basesoc_core_rx_converter_converter_source_last <= (main_basesoc_core_rx_converter_converter_sink_last | main_basesoc_core_rx_converter_converter_source_last);
        end
    end
    if (main_basesoc_core_rx_converter_converter_load_part) begin
        case (main_basesoc_core_rx_converter_converter_demux)
            1'd0: begin
                main_basesoc_core_rx_converter_converter_source_payload_data[9:0] <= main_basesoc_core_rx_converter_converter_sink_payload_data;
            end
            1'd1: begin
                main_basesoc_core_rx_converter_converter_source_payload_data[19:10] <= main_basesoc_core_rx_converter_converter_sink_payload_data;
            end
            2'd2: begin
                main_basesoc_core_rx_converter_converter_source_payload_data[29:20] <= main_basesoc_core_rx_converter_converter_sink_payload_data;
            end
            2'd3: begin
                main_basesoc_core_rx_converter_converter_source_payload_data[39:30] <= main_basesoc_core_rx_converter_converter_sink_payload_data;
            end
        endcase
    end
    if (main_basesoc_core_rx_converter_converter_load_part) begin
        main_basesoc_core_rx_converter_converter_source_payload_valid_token_count <= (main_basesoc_core_rx_converter_converter_demux + 1'd1);
    end
    main_basesoc_core_rx_cdc_cdc_graycounter0_q_binary <= main_basesoc_core_rx_cdc_cdc_graycounter0_q_next_binary;
    main_basesoc_core_rx_cdc_cdc_graycounter0_q <= main_basesoc_core_rx_cdc_cdc_graycounter0_q_next;
    if (main_basesoc_core_rx_cdc_cdc_reset_write) begin
        main_basesoc_core_rx_cdc_cdc_graycounter0_q <= 6'd0;
        main_basesoc_core_rx_cdc_cdc_graycounter0_q_binary <= 6'd0;
    end
    if (eth_rx_rst) begin
        main_ethphy_source_valid <= 1'd0;
        main_ethphy_rx_ctl_d <= 1'd0;
        main_basesoc_core_liteethmaccrc32checker_crc_reg <= 32'hffffffff;
        main_basesoc_core_liteethmaccrc32checker_syncfifo_level <= 3'd0;
        main_basesoc_core_liteethmaccrc32checker_syncfifo_produce <= 3'd0;
        main_basesoc_core_liteethmaccrc32checker_syncfifo_consume <= 3'd0;
        main_basesoc_core_liteethmaccrc32checker_last_error <= 1'd0;
        main_basesoc_core_liteethmaccrc32checker_packet_error <= 1'd0;
        main_basesoc_core_bufferizeendpoints_pipe_valid_source_valid <= 1'd0;
        main_basesoc_core_rx_padding_length <= 11'd0;
        main_basesoc_core_rx_converter_converter_demux <= 2'd0;
        main_basesoc_core_rx_converter_converter_strobe_all <= 1'd0;
        main_basesoc_core_rx_cdc_cdc_graycounter0_q <= 6'd0;
        main_basesoc_core_rx_cdc_cdc_graycounter0_q_binary <= 6'd0;
        builder_clockdomainsrenamer_rxdatapath_liteethmacpreamblechecker_state <= 1'd0;
        builder_clockdomainsrenamer_rxdatapath_bufferizeendpoints_state <= 2'd0;
    end
    builder_xilinxmultiregimpl80 <= sys_rst;
    builder_xilinxmultiregimpl81 <= builder_xilinxmultiregimpl80;
    builder_xilinxmultiregimpl110 <= main_basesoc_core_rx_cdc_cdc_graycounter1_q;
    builder_xilinxmultiregimpl111 <= builder_xilinxmultiregimpl110;
end

always @(posedge eth_tx_clk) begin
    main_basesoc_core_tx_cdc_cdc_graycounter1_q_binary <= main_basesoc_core_tx_cdc_cdc_graycounter1_q_next_binary;
    main_basesoc_core_tx_cdc_cdc_graycounter1_q <= main_basesoc_core_tx_cdc_cdc_graycounter1_q_next;
    if (main_basesoc_core_tx_cdc_cdc_reset_read) begin
        main_basesoc_core_tx_cdc_cdc_graycounter1_q <= 6'd0;
        main_basesoc_core_tx_cdc_cdc_graycounter1_q_binary <= 6'd0;
    end
    if ((main_basesoc_core_tx_converter_converter_source_valid & main_basesoc_core_tx_converter_converter_source_ready)) begin
        if ((main_basesoc_core_tx_converter_index == 2'd3)) begin
            main_basesoc_core_tx_converter_index <= 1'd0;
            main_basesoc_core_tx_converter_drop <= 1'd0;
        end else begin
            main_basesoc_core_tx_converter_index <= (main_basesoc_core_tx_converter_index + 1'd1);
            if (main_basesoc_core_tx_converter_packet_end) begin
                main_basesoc_core_tx_converter_drop <= 1'd1;
            end
        end
    end
    if ((main_basesoc_core_tx_converter_converter_source_valid & main_basesoc_core_tx_converter_converter_source_ready)) begin
        if (main_basesoc_core_tx_converter_converter_last) begin
            main_basesoc_core_tx_converter_converter_mux <= 1'd0;
        end else begin
            main_basesoc_core_tx_converter_converter_mux <= (main_basesoc_core_tx_converter_converter_mux + 1'd1);
        end
    end
    if (main_basesoc_core_tx_converter_reset) begin
        main_basesoc_core_tx_converter_converter_mux <= 2'd0;
        main_basesoc_core_tx_converter_index <= 2'd0;
        main_basesoc_core_tx_converter_drop <= 1'd0;
    end
    builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_state <= builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_next_state;
    if (main_basesoc_core_tx_padding_counter_clockdomainsrenamer0_next_value_ce) begin
        main_basesoc_core_tx_padding_counter <= main_basesoc_core_tx_padding_counter_clockdomainsrenamer0_next_value;
    end
    if (main_basesoc_core_tx_padding_reset) begin
        main_basesoc_core_tx_padding_counter <= 16'd0;
        builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_state <= 1'd0;
    end
    if (main_basesoc_core_liteethmaccrc32inserter_is_ongoing0) begin
        main_basesoc_core_liteethmaccrc32inserter_cnt <= 2'd3;
    end else begin
        if ((main_basesoc_core_liteethmaccrc32inserter_is_ongoing1 & (~main_basesoc_core_liteethmaccrc32inserter_cnt_done))) begin
            main_basesoc_core_liteethmaccrc32inserter_cnt <= (main_basesoc_core_liteethmaccrc32inserter_cnt - main_basesoc_core_liteethmaccrc32inserter_source_ready);
        end
    end
    if (main_basesoc_core_liteethmaccrc32inserter_ce) begin
        main_basesoc_core_liteethmaccrc32inserter_reg <= main_basesoc_core_liteethmaccrc32inserter_crc_next;
    end
    if (main_basesoc_core_liteethmaccrc32inserter_reset) begin
        main_basesoc_core_liteethmaccrc32inserter_reg <= 32'hffffffff;
    end
    builder_clockdomainsrenamer_txdatapath_bufferizeendpoints_state <= builder_clockdomainsrenamer_txdatapath_bufferizeendpoints_next_state;
    if (main_basesoc_core_liteethmaccrc32inserter_crc_packet_clockdomainsrenamer1_next_value_ce0) begin
        main_basesoc_core_liteethmaccrc32inserter_crc_packet <= main_basesoc_core_liteethmaccrc32inserter_crc_packet_clockdomainsrenamer1_next_value0;
    end
    if (main_basesoc_core_liteethmaccrc32inserter_be0_clockdomainsrenamer1_next_value_ce1) begin
        main_basesoc_core_liteethmaccrc32inserter_be0 <= main_basesoc_core_liteethmaccrc32inserter_be0_clockdomainsrenamer1_next_value1;
    end
    if (((~main_basesoc_core_pipe_valid_source_valid) | main_basesoc_core_pipe_valid_source_ready)) begin
        main_basesoc_core_pipe_valid_source_valid <= main_basesoc_core_pipe_valid_sink_valid;
        main_basesoc_core_pipe_valid_source_first <= main_basesoc_core_pipe_valid_sink_first;
        main_basesoc_core_pipe_valid_source_last <= main_basesoc_core_pipe_valid_sink_last;
        main_basesoc_core_pipe_valid_source_payload_data <= main_basesoc_core_pipe_valid_sink_payload_data;
        main_basesoc_core_pipe_valid_source_payload_be <= main_basesoc_core_pipe_valid_sink_payload_be;
        main_basesoc_core_pipe_valid_source_payload_error <= main_basesoc_core_pipe_valid_sink_payload_error;
    end
    if (main_basesoc_core_txdatapath_reset) begin
        main_basesoc_core_liteethmaccrc32inserter_reg <= 32'hffffffff;
        main_basesoc_core_liteethmaccrc32inserter_cnt <= 2'd3;
        main_basesoc_core_pipe_valid_source_valid <= 1'd0;
        builder_clockdomainsrenamer_txdatapath_bufferizeendpoints_state <= 2'd0;
    end
    builder_clockdomainsrenamer_txdatapath_liteethmacpreambleinserter_state <= builder_clockdomainsrenamer_txdatapath_liteethmacpreambleinserter_next_state;
    if (main_basesoc_core_tx_preamble_count_clockdomainsrenamer2_next_value_ce) begin
        main_basesoc_core_tx_preamble_count <= main_basesoc_core_tx_preamble_count_clockdomainsrenamer2_next_value;
    end
    if (main_basesoc_core_tx_preamble_reset) begin
        builder_clockdomainsrenamer_txdatapath_liteethmacpreambleinserter_state <= 2'd0;
    end
    builder_clockdomainsrenamer_txdatapath_liteethmacgap_state <= builder_clockdomainsrenamer_txdatapath_liteethmacgap_next_state;
    if (main_basesoc_core_tx_gap_counter_clockdomainsrenamer3_next_value_ce) begin
        main_basesoc_core_tx_gap_counter <= main_basesoc_core_tx_gap_counter_clockdomainsrenamer3_next_value;
    end
    if (main_basesoc_core_tx_gap_reset) begin
        builder_clockdomainsrenamer_txdatapath_liteethmacgap_state <= 1'd0;
    end
    if (eth_tx_rst) begin
        main_basesoc_core_tx_cdc_cdc_graycounter1_q <= 6'd0;
        main_basesoc_core_tx_cdc_cdc_graycounter1_q_binary <= 6'd0;
        main_basesoc_core_tx_converter_converter_mux <= 2'd0;
        main_basesoc_core_tx_converter_index <= 2'd0;
        main_basesoc_core_tx_converter_drop <= 1'd0;
        main_basesoc_core_tx_padding_counter <= 16'd0;
        main_basesoc_core_liteethmaccrc32inserter_reg <= 32'hffffffff;
        main_basesoc_core_liteethmaccrc32inserter_cnt <= 2'd3;
        main_basesoc_core_pipe_valid_source_valid <= 1'd0;
        builder_clockdomainsrenamer_txdatapath_liteethmacpaddinginserter_state <= 1'd0;
        builder_clockdomainsrenamer_txdatapath_bufferizeendpoints_state <= 2'd0;
        builder_clockdomainsrenamer_txdatapath_liteethmacpreambleinserter_state <= 2'd0;
        builder_clockdomainsrenamer_txdatapath_liteethmacgap_state <= 1'd0;
    end
    builder_xilinxmultiregimpl30 <= main_basesoc_core_tx_cdc_write_rst;
    builder_xilinxmultiregimpl31 <= builder_xilinxmultiregimpl30;
    builder_xilinxmultiregimpl40 <= main_basesoc_core_tx_cdc_cdc_graycounter0_q;
    builder_xilinxmultiregimpl41 <= builder_xilinxmultiregimpl40;
end

always @(posedge idelay_clk) begin
    if ((main_crg_reset_counter != 1'd0)) begin
        main_crg_reset_counter <= (main_crg_reset_counter - 1'd1);
    end else begin
        main_crg_ic_reset <= 1'd0;
    end
    if (idelay_rst) begin
        main_crg_reset_counter <= 4'd15;
        main_crg_ic_reset <= 1'd1;
    end
end

always @(posedge sys_clk) begin
    case (builder_grant)
        1'd0: begin
            if ((~builder_request[0])) begin
                if (builder_request[1]) begin
                    builder_grant <= 1'd1;
                end
            end
        end
        1'd1: begin
            if ((~builder_request[1])) begin
                if (builder_request[0]) begin
                    builder_grant <= 1'd0;
                end
            end
        end
    endcase
    builder_slave_sel_r <= builder_slave_sel;
    if (builder_wait) begin
        if ((~builder_done)) begin
            builder_count <= (builder_count - 1'd1);
        end
    end else begin
        builder_count <= 20'd1000000;
    end
    if ((main_basesoc_bus_errors != 32'hffffffff)) begin
        if (main_basesoc_bus_error) begin
            main_basesoc_bus_errors <= (main_basesoc_bus_errors + 1'd1);
        end
    end
    main_basesoc_ram_bus_ack <= 1'd0;
    if (((main_basesoc_ram_bus_cyc & main_basesoc_ram_bus_stb) & ((~main_basesoc_ram_bus_ack) | main_basesoc_adr_burst))) begin
        main_basesoc_ram_bus_ack <= 1'd1;
    end
    main_basesoc_interface0_ram_bus_ack <= 1'd0;
    if (((main_basesoc_interface0_ram_bus_cyc & main_basesoc_interface0_ram_bus_stb) & ((~main_basesoc_interface0_ram_bus_ack) | main_basesoc_sram0_adr_burst))) begin
        main_basesoc_interface0_ram_bus_ack <= 1'd1;
    end
    main_basesoc_interface1_ram_bus_ack <= 1'd0;
    if (((main_basesoc_interface1_ram_bus_cyc & main_basesoc_interface1_ram_bus_stb) & ((~main_basesoc_interface1_ram_bus_ack) | main_basesoc_sram1_adr_burst))) begin
        main_basesoc_interface1_ram_bus_ack <= 1'd1;
    end
    {main_basesoc_uart_core_tx_tick, main_basesoc_uart_core_tx_phase} <= 23'd4947802;
    if (main_basesoc_uart_core_tx_enable) begin
        {main_basesoc_uart_core_tx_tick, main_basesoc_uart_core_tx_phase} <= (main_basesoc_uart_core_tx_phase + 23'd4947802);
    end
    builder_rs232phytx_state <= builder_rs232phytx_next_state;
    if (main_basesoc_uart_core_tx_count_rs232phytx_next_value_ce0) begin
        main_basesoc_uart_core_tx_count <= main_basesoc_uart_core_tx_count_rs232phytx_next_value0;
    end
    if (main_basesoc_serial_tx_rs232phytx_next_value_ce1) begin
        serial_tx <= main_basesoc_serial_tx_rs232phytx_next_value1;
    end
    if (main_basesoc_uart_core_tx_data_rs232phytx_next_value_ce2) begin
        main_basesoc_uart_core_tx_data <= main_basesoc_uart_core_tx_data_rs232phytx_next_value2;
    end
    main_basesoc_uart_core_rx_rx_d <= main_basesoc_uart_core_rx_rx;
    {main_basesoc_uart_core_rx_tick, main_basesoc_uart_core_rx_phase} <= 32'h80000000;
    if (main_basesoc_uart_core_rx_enable) begin
        {main_basesoc_uart_core_rx_tick, main_basesoc_uart_core_rx_phase} <= (main_basesoc_uart_core_rx_phase + 23'd4947802);
    end
    builder_rs232phyrx_state <= builder_rs232phyrx_next_state;
    if (main_basesoc_uart_core_rx_count_rs232phyrx_next_value_ce0) begin
        main_basesoc_uart_core_rx_count <= main_basesoc_uart_core_rx_count_rs232phyrx_next_value0;
    end
    if (main_basesoc_uart_core_rx_data_rs232phyrx_next_value_ce1) begin
        main_basesoc_uart_core_rx_data <= main_basesoc_uart_core_rx_data_rs232phyrx_next_value1;
    end
    if (main_basesoc_uart_core_tx_fifo_syncfifo_re) begin
        main_basesoc_uart_core_tx_fifo_readable <= 1'd1;
    end else begin
        if (main_basesoc_uart_core_tx_fifo_re) begin
            main_basesoc_uart_core_tx_fifo_readable <= 1'd0;
        end
    end
    if (((main_basesoc_uart_core_tx_fifo_syncfifo_we & main_basesoc_uart_core_tx_fifo_syncfifo_writable) & (~main_basesoc_uart_core_tx_fifo_replace))) begin
        main_basesoc_uart_core_tx_fifo_produce <= (main_basesoc_uart_core_tx_fifo_produce + 1'd1);
    end
    if (main_basesoc_uart_core_tx_fifo_do_read) begin
        main_basesoc_uart_core_tx_fifo_consume <= (main_basesoc_uart_core_tx_fifo_consume + 1'd1);
    end
    if (((main_basesoc_uart_core_tx_fifo_syncfifo_we & main_basesoc_uart_core_tx_fifo_syncfifo_writable) & (~main_basesoc_uart_core_tx_fifo_replace))) begin
        if ((~main_basesoc_uart_core_tx_fifo_do_read)) begin
            main_basesoc_uart_core_tx_fifo_level0 <= (main_basesoc_uart_core_tx_fifo_level0 + 1'd1);
        end
    end else begin
        if (main_basesoc_uart_core_tx_fifo_do_read) begin
            main_basesoc_uart_core_tx_fifo_level0 <= (main_basesoc_uart_core_tx_fifo_level0 - 1'd1);
        end
    end
    if (main_basesoc_uart_core_rx_fifo_syncfifo_re) begin
        main_basesoc_uart_core_rx_fifo_readable <= 1'd1;
    end else begin
        if (main_basesoc_uart_core_rx_fifo_re) begin
            main_basesoc_uart_core_rx_fifo_readable <= 1'd0;
        end
    end
    if (((main_basesoc_uart_core_rx_fifo_syncfifo_we & main_basesoc_uart_core_rx_fifo_syncfifo_writable) & (~main_basesoc_uart_core_rx_fifo_replace))) begin
        main_basesoc_uart_core_rx_fifo_produce <= (main_basesoc_uart_core_rx_fifo_produce + 1'd1);
    end
    if (main_basesoc_uart_core_rx_fifo_do_read) begin
        main_basesoc_uart_core_rx_fifo_consume <= (main_basesoc_uart_core_rx_fifo_consume + 1'd1);
    end
    if (((main_basesoc_uart_core_rx_fifo_syncfifo_we & main_basesoc_uart_core_rx_fifo_syncfifo_writable) & (~main_basesoc_uart_core_rx_fifo_replace))) begin
        if ((~main_basesoc_uart_core_rx_fifo_do_read)) begin
            main_basesoc_uart_core_rx_fifo_level0 <= (main_basesoc_uart_core_rx_fifo_level0 + 1'd1);
        end
    end else begin
        if (main_basesoc_uart_core_rx_fifo_do_read) begin
            main_basesoc_uart_core_rx_fifo_level0 <= (main_basesoc_uart_core_rx_fifo_level0 - 1'd1);
        end
    end
    if (main_basesoc_timer_en_storage) begin
        if ((main_basesoc_timer_value == 1'd0)) begin
            main_basesoc_timer_value <= main_basesoc_timer_reload_storage;
        end else begin
            main_basesoc_timer_value <= (main_basesoc_timer_value - 1'd1);
        end
    end else begin
        main_basesoc_timer_value <= main_basesoc_timer_load_storage;
    end
    if (main_basesoc_timer_update_value_wr_stb) begin
        main_basesoc_timer_value_status <= main_basesoc_timer_value;
    end
    if (main_basesoc_timer_zero_clear) begin
        main_basesoc_timer_zero_pending <= 1'd0;
    end
    main_basesoc_timer_zero_trigger_d <= main_basesoc_timer_zero_trigger;
    if ((main_basesoc_timer_zero_trigger & (~main_basesoc_timer_zero_trigger_d))) begin
        main_basesoc_timer_zero_pending <= 1'd1;
    end
    if (main_ethphy_hw_reset_counter_ce) begin
        main_ethphy_hw_reset_counter <= (main_ethphy_hw_reset_counter + 1'd1);
    end
    main_basesoc_core_tx_cdc_cdc_graycounter0_q_binary <= main_basesoc_core_tx_cdc_cdc_graycounter0_q_next_binary;
    main_basesoc_core_tx_cdc_cdc_graycounter0_q <= main_basesoc_core_tx_cdc_cdc_graycounter0_q_next;
    if (main_basesoc_core_tx_cdc_cdc_reset_write) begin
        main_basesoc_core_tx_cdc_cdc_graycounter0_q <= 6'd0;
        main_basesoc_core_tx_cdc_cdc_graycounter0_q_binary <= 6'd0;
    end
    if (main_basesoc_core_pulsesynchronizer0_o) begin
        main_basesoc_core_preamble_errors_status <= (main_basesoc_core_preamble_errors_status + 1'd1);
    end
    if (main_basesoc_core_pulsesynchronizer1_o) begin
        main_basesoc_core_crc_errors_status <= (main_basesoc_core_crc_errors_status + 1'd1);
    end
    main_basesoc_core_pulsesynchronizer0_toggle_o_r <= main_basesoc_core_pulsesynchronizer0_toggle_o;
    main_basesoc_core_pulsesynchronizer1_toggle_o_r <= main_basesoc_core_pulsesynchronizer1_toggle_o;
    main_basesoc_core_rx_cdc_cdc_graycounter1_q_binary <= main_basesoc_core_rx_cdc_cdc_graycounter1_q_next_binary;
    main_basesoc_core_rx_cdc_cdc_graycounter1_q <= main_basesoc_core_rx_cdc_cdc_graycounter1_q_next;
    if (main_basesoc_core_rx_cdc_cdc_reset_read) begin
        main_basesoc_core_rx_cdc_cdc_graycounter1_q <= 6'd0;
        main_basesoc_core_rx_cdc_cdc_graycounter1_q_binary <= 6'd0;
    end
    if (main_basesoc_wishbone_interface_writer_packet_drop) begin
        main_basesoc_wishbone_interface_writer_errors_status <= (main_basesoc_wishbone_interface_writer_errors_status + 1'd1);
    end
    if ((main_basesoc_wishbone_interface_writer_packet_done & main_basesoc_wishbone_interface_writer_stat_fifo_sink_ready)) begin
        if ((main_basesoc_wishbone_interface_writer_slot == 1'd1)) begin
            main_basesoc_wishbone_interface_writer_slot <= 1'd0;
        end else begin
            main_basesoc_wishbone_interface_writer_slot <= (main_basesoc_wishbone_interface_writer_slot + 1'd1);
        end
    end
    builder_clockdomainsrenamer_state <= builder_clockdomainsrenamer_next_state;
    if (main_basesoc_wishbone_interface_writer_packet_length1_liteethmacsramwriter_next_value_ce0) begin
        main_basesoc_wishbone_interface_writer_packet_length1 <= main_basesoc_wishbone_interface_writer_packet_length1_liteethmacsramwriter_next_value0;
    end
    if (main_basesoc_wishbone_interface_writer_packet_pkt_len_liteethmacsramwriter_next_value_ce1) begin
        main_basesoc_wishbone_interface_writer_packet_pkt_len <= main_basesoc_wishbone_interface_writer_packet_pkt_len_liteethmacsramwriter_next_value1;
    end
    if (main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value_ce2) begin
        main_basesoc_wishbone_interface_writer_packet_error1 <= main_basesoc_wishbone_interface_writer_packet_error1_liteethmacsramwriter_next_value2;
    end
    if (((main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_we & main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_writable) & (~main_basesoc_wishbone_interface_writer_stat_fifo_replace))) begin
        main_basesoc_wishbone_interface_writer_stat_fifo_produce <= (main_basesoc_wishbone_interface_writer_stat_fifo_produce + 1'd1);
    end
    if (main_basesoc_wishbone_interface_writer_stat_fifo_do_read) begin
        main_basesoc_wishbone_interface_writer_stat_fifo_consume <= (main_basesoc_wishbone_interface_writer_stat_fifo_consume + 1'd1);
    end
    if (((main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_we & main_basesoc_wishbone_interface_writer_stat_fifo_syncfifo_writable) & (~main_basesoc_wishbone_interface_writer_stat_fifo_replace))) begin
        if ((~main_basesoc_wishbone_interface_writer_stat_fifo_do_read)) begin
            main_basesoc_wishbone_interface_writer_stat_fifo_level <= (main_basesoc_wishbone_interface_writer_stat_fifo_level + 1'd1);
        end
    end else begin
        if (main_basesoc_wishbone_interface_writer_stat_fifo_do_read) begin
            main_basesoc_wishbone_interface_writer_stat_fifo_level <= (main_basesoc_wishbone_interface_writer_stat_fifo_level - 1'd1);
        end
    end
    if (main_basesoc_wishbone_interface_reader_eventsourcepulse_clear) begin
        main_basesoc_wishbone_interface_reader_eventsourcepulse_pending <= 1'd0;
    end
    if (main_basesoc_wishbone_interface_reader_eventsourcepulse_trigger) begin
        main_basesoc_wishbone_interface_reader_eventsourcepulse_pending <= 1'd1;
    end
    builder_clockdomainsrenamer_liteethmacpacketreader_state <= builder_clockdomainsrenamer_liteethmacpacketreader_next_state;
    if (((main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_we & main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_writable) & (~main_basesoc_wishbone_interface_reader_cmd_fifo_replace))) begin
        main_basesoc_wishbone_interface_reader_cmd_fifo_produce <= (main_basesoc_wishbone_interface_reader_cmd_fifo_produce + 1'd1);
    end
    if (main_basesoc_wishbone_interface_reader_cmd_fifo_do_read) begin
        main_basesoc_wishbone_interface_reader_cmd_fifo_consume <= (main_basesoc_wishbone_interface_reader_cmd_fifo_consume + 1'd1);
    end
    if (((main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_we & main_basesoc_wishbone_interface_reader_cmd_fifo_syncfifo_writable) & (~main_basesoc_wishbone_interface_reader_cmd_fifo_replace))) begin
        if ((~main_basesoc_wishbone_interface_reader_cmd_fifo_do_read)) begin
            main_basesoc_wishbone_interface_reader_cmd_fifo_level <= (main_basesoc_wishbone_interface_reader_cmd_fifo_level + 1'd1);
        end
    end else begin
        if (main_basesoc_wishbone_interface_reader_cmd_fifo_do_read) begin
            main_basesoc_wishbone_interface_reader_cmd_fifo_level <= (main_basesoc_wishbone_interface_reader_cmd_fifo_level - 1'd1);
        end
    end
    builder_clockdomainsrenamer_fsm_state <= builder_clockdomainsrenamer_fsm_next_state;
    if (main_basesoc_wishbone_interface_reader_rd_offset_liteethmacsramreader_next_value_ce) begin
        main_basesoc_wishbone_interface_reader_rd_offset <= main_basesoc_wishbone_interface_reader_rd_offset_liteethmacsramreader_next_value;
    end
    main_basesoc_wishbone_interface_interface0_ack <= 1'd0;
    if (((main_basesoc_wishbone_interface_interface0_cyc & main_basesoc_wishbone_interface_interface0_stb) & ((~main_basesoc_wishbone_interface_interface0_ack) | main_basesoc_wishbone_interface_sram0_adr_burst))) begin
        main_basesoc_wishbone_interface_interface0_ack <= 1'd1;
    end
    main_basesoc_wishbone_interface_interface1_ack <= 1'd0;
    if (((main_basesoc_wishbone_interface_interface1_cyc & main_basesoc_wishbone_interface_interface1_stb) & ((~main_basesoc_wishbone_interface_interface1_ack) | main_basesoc_wishbone_interface_sram1_adr_burst))) begin
        main_basesoc_wishbone_interface_interface1_ack <= 1'd1;
    end
    main_basesoc_wishbone_interface_decoder0_slave_sel_r <= main_basesoc_wishbone_interface_decoder0_slave_sel;
    main_basesoc_wishbone_interface_interface2_ack <= 1'd0;
    if (((main_basesoc_wishbone_interface_interface2_cyc & main_basesoc_wishbone_interface_interface2_stb) & ((~main_basesoc_wishbone_interface_interface2_ack) | main_basesoc_wishbone_interface_sram2_adr_burst))) begin
        main_basesoc_wishbone_interface_interface2_ack <= 1'd1;
    end
    main_basesoc_wishbone_interface_interface3_ack <= 1'd0;
    if (((main_basesoc_wishbone_interface_interface3_cyc & main_basesoc_wishbone_interface_interface3_stb) & ((~main_basesoc_wishbone_interface_interface3_ack) | main_basesoc_wishbone_interface_sram3_adr_burst))) begin
        main_basesoc_wishbone_interface_interface3_ack <= 1'd1;
    end
    main_basesoc_wishbone_interface_decoder1_slave_sel_r <= main_basesoc_wishbone_interface_decoder1_slave_sel;
    if (main_done) begin
        main_chaser <= {main_chaser, (~main_chaser[7])};
    end
    if (main_wr_stb) begin
        main_mode <= 1'd1;
    end
    if (main_wait) begin
        if ((~main_done)) begin
            main_count <= (main_count - 1'd1);
        end
    end else begin
        main_count <= 23'd6250000;
    end
    builder_wishbone2csr_state <= builder_wishbone2csr_next_state;
    builder_csr_bankarray_interface0_bank_bus_dat_r <= 1'd0;
    if (builder_csr_bankarray_csrbank0_sel) begin
        case (builder_csr_bankarray_interface0_bank_bus_adr[8:0])
            1'd0: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= builder_csr_bankarray_csrbank0_reset_w;
            end
            1'd1: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= builder_csr_bankarray_csrbank0_scratch_w;
            end
            2'd2: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= builder_csr_bankarray_csrbank0_bus_errors_w;
            end
        endcase
    end
    if (builder_csr_bankarray_csrbank0_reset_re) begin
        main_basesoc_reset_storage <= builder_csr_bankarray_csrbank0_reset_r;
    end
    main_basesoc_reset_wr_stb <= builder_csr_bankarray_csrbank0_reset_re;
    if (builder_csr_bankarray_csrbank0_scratch_re) begin
        main_basesoc_scratch_storage <= builder_csr_bankarray_csrbank0_scratch_r;
    end
    main_basesoc_scratch_wr_stb <= builder_csr_bankarray_csrbank0_scratch_re;
    main_basesoc_bus_errors_wr_stb <= builder_csr_bankarray_csrbank0_bus_errors_re;
    builder_csr_bankarray_interface1_bank_bus_dat_r <= 1'd0;
    if (builder_csr_bankarray_csrbank1_sel) begin
        case (builder_csr_bankarray_interface1_bank_bus_adr[8:0])
            1'd0: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_sram_writer_slot_w;
            end
            1'd1: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_sram_writer_length_w;
            end
            2'd2: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_sram_writer_errors_w;
            end
            2'd3: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_sram_writer_ev_status_w;
            end
            3'd4: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_sram_writer_ev_pending_w;
            end
            3'd5: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_sram_writer_ev_enable_w;
            end
            3'd6: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= main_basesoc_wishbone_interface_reader_start_w;
            end
            3'd7: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_sram_reader_ready_w;
            end
            4'd8: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_sram_reader_level_w;
            end
            4'd9: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_sram_reader_slot_w;
            end
            4'd10: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_sram_reader_length_w;
            end
            4'd11: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_sram_reader_ev_status_w;
            end
            4'd12: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_sram_reader_ev_pending_w;
            end
            4'd13: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_sram_reader_ev_enable_w;
            end
            4'd14: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_preamble_crc_w;
            end
            4'd15: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_rx_datapath_preamble_errors_w;
            end
            5'd16: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_rx_datapath_crc_errors_w;
            end
        endcase
    end
    main_basesoc_wishbone_interface_writer_slot_wr_stb <= builder_csr_bankarray_csrbank1_sram_writer_slot_re;
    main_basesoc_wishbone_interface_writer_length_wr_stb <= builder_csr_bankarray_csrbank1_sram_writer_length_re;
    main_basesoc_wishbone_interface_writer_errors_wr_stb <= builder_csr_bankarray_csrbank1_sram_writer_errors_re;
    main_basesoc_wishbone_interface_writer_status_wr_stb <= builder_csr_bankarray_csrbank1_sram_writer_ev_status_re;
    if (builder_csr_bankarray_csrbank1_sram_writer_ev_pending_re) begin
        main_basesoc_wishbone_interface_writer_pending_wr_data <= builder_csr_bankarray_csrbank1_sram_writer_ev_pending_r;
    end
    main_basesoc_wishbone_interface_writer_pending_wr_stb <= builder_csr_bankarray_csrbank1_sram_writer_ev_pending_re;
    if (builder_csr_bankarray_csrbank1_sram_writer_ev_enable_re) begin
        main_basesoc_wishbone_interface_writer_enable_storage <= builder_csr_bankarray_csrbank1_sram_writer_ev_enable_r;
    end
    main_basesoc_wishbone_interface_writer_enable_wr_stb <= builder_csr_bankarray_csrbank1_sram_writer_ev_enable_re;
    main_basesoc_wishbone_interface_reader_ready_wr_stb <= builder_csr_bankarray_csrbank1_sram_reader_ready_re;
    main_basesoc_wishbone_interface_reader_level_wr_stb <= builder_csr_bankarray_csrbank1_sram_reader_level_re;
    if (builder_csr_bankarray_csrbank1_sram_reader_slot_re) begin
        main_basesoc_wishbone_interface_reader_slot_storage <= builder_csr_bankarray_csrbank1_sram_reader_slot_r;
    end
    main_basesoc_wishbone_interface_reader_slot_wr_stb <= builder_csr_bankarray_csrbank1_sram_reader_slot_re;
    if (builder_csr_bankarray_csrbank1_sram_reader_length_re) begin
        main_basesoc_wishbone_interface_reader_length_storage <= builder_csr_bankarray_csrbank1_sram_reader_length_r;
    end
    main_basesoc_wishbone_interface_reader_length_wr_stb <= builder_csr_bankarray_csrbank1_sram_reader_length_re;
    main_basesoc_wishbone_interface_reader_status_wr_stb <= builder_csr_bankarray_csrbank1_sram_reader_ev_status_re;
    if (builder_csr_bankarray_csrbank1_sram_reader_ev_pending_re) begin
        main_basesoc_wishbone_interface_reader_pending_wr_data <= builder_csr_bankarray_csrbank1_sram_reader_ev_pending_r;
    end
    main_basesoc_wishbone_interface_reader_pending_wr_stb <= builder_csr_bankarray_csrbank1_sram_reader_ev_pending_re;
    if (builder_csr_bankarray_csrbank1_sram_reader_ev_enable_re) begin
        main_basesoc_wishbone_interface_reader_enable_storage <= builder_csr_bankarray_csrbank1_sram_reader_ev_enable_r;
    end
    main_basesoc_wishbone_interface_reader_enable_wr_stb <= builder_csr_bankarray_csrbank1_sram_reader_ev_enable_re;
    main_basesoc_core_wr_stb <= builder_csr_bankarray_csrbank1_preamble_crc_re;
    main_basesoc_core_preamble_errors_wr_stb <= builder_csr_bankarray_csrbank1_rx_datapath_preamble_errors_re;
    main_basesoc_core_crc_errors_wr_stb <= builder_csr_bankarray_csrbank1_rx_datapath_crc_errors_re;
    builder_csr_bankarray_interface2_bank_bus_dat_r <= 1'd0;
    if (builder_csr_bankarray_csrbank2_sel) begin
        case (builder_csr_bankarray_interface2_bank_bus_adr[8:0])
            1'd0: begin
                builder_csr_bankarray_interface2_bank_bus_dat_r <= builder_csr_bankarray_csrbank2_crg_reset_w;
            end
            1'd1: begin
                builder_csr_bankarray_interface2_bank_bus_dat_r <= builder_csr_bankarray_csrbank2_mdio_w_w;
            end
            2'd2: begin
                builder_csr_bankarray_interface2_bank_bus_dat_r <= builder_csr_bankarray_csrbank2_mdio_r_w;
            end
        endcase
    end
    if (builder_csr_bankarray_csrbank2_crg_reset_re) begin
        main_ethphy_reset_storage <= builder_csr_bankarray_csrbank2_crg_reset_r;
    end
    main_ethphy_reset_wr_stb <= builder_csr_bankarray_csrbank2_crg_reset_re;
    if (builder_csr_bankarray_csrbank2_mdio_w_re) begin
        main_ethphy__w_storage <= builder_csr_bankarray_csrbank2_mdio_w_r;
    end
    main_ethphy__w_wr_stb <= builder_csr_bankarray_csrbank2_mdio_w_re;
    main_ethphy__r_wr_stb <= builder_csr_bankarray_csrbank2_mdio_r_re;
    builder_csr_bankarray_sel_r <= builder_csr_bankarray_sel;
    builder_csr_bankarray_interface3_bank_bus_dat_r <= 1'd0;
    if (builder_csr_bankarray_csrbank3_sel) begin
        case (builder_csr_bankarray_interface3_bank_bus_adr[8:0])
            1'd0: begin
                builder_csr_bankarray_interface3_bank_bus_dat_r <= builder_csr_bankarray_csrbank3_out_w;
            end
        endcase
    end
    if (builder_csr_bankarray_csrbank3_out_re) begin
        main_storage <= builder_csr_bankarray_csrbank3_out_r;
    end
    main_wr_stb <= builder_csr_bankarray_csrbank3_out_re;
    builder_csr_bankarray_interface4_bank_bus_dat_r <= 1'd0;
    if (builder_csr_bankarray_csrbank4_sel) begin
        case (builder_csr_bankarray_interface4_bank_bus_adr[8:0])
            1'd0: begin
                builder_csr_bankarray_interface4_bank_bus_dat_r <= builder_csr_bankarray_csrbank4_load_w;
            end
            1'd1: begin
                builder_csr_bankarray_interface4_bank_bus_dat_r <= builder_csr_bankarray_csrbank4_reload_w;
            end
            2'd2: begin
                builder_csr_bankarray_interface4_bank_bus_dat_r <= builder_csr_bankarray_csrbank4_en_w;
            end
            2'd3: begin
                builder_csr_bankarray_interface4_bank_bus_dat_r <= builder_csr_bankarray_csrbank4_update_value_w;
            end
            3'd4: begin
                builder_csr_bankarray_interface4_bank_bus_dat_r <= builder_csr_bankarray_csrbank4_value_w;
            end
            3'd5: begin
                builder_csr_bankarray_interface4_bank_bus_dat_r <= builder_csr_bankarray_csrbank4_ev_status_w;
            end
            3'd6: begin
                builder_csr_bankarray_interface4_bank_bus_dat_r <= builder_csr_bankarray_csrbank4_ev_pending_w;
            end
            3'd7: begin
                builder_csr_bankarray_interface4_bank_bus_dat_r <= builder_csr_bankarray_csrbank4_ev_enable_w;
            end
        endcase
    end
    if (builder_csr_bankarray_csrbank4_load_re) begin
        main_basesoc_timer_load_storage <= builder_csr_bankarray_csrbank4_load_r;
    end
    main_basesoc_timer_load_wr_stb <= builder_csr_bankarray_csrbank4_load_re;
    if (builder_csr_bankarray_csrbank4_reload_re) begin
        main_basesoc_timer_reload_storage <= builder_csr_bankarray_csrbank4_reload_r;
    end
    main_basesoc_timer_reload_wr_stb <= builder_csr_bankarray_csrbank4_reload_re;
    if (builder_csr_bankarray_csrbank4_en_re) begin
        main_basesoc_timer_en_storage <= builder_csr_bankarray_csrbank4_en_r;
    end
    main_basesoc_timer_en_wr_stb <= builder_csr_bankarray_csrbank4_en_re;
    if (builder_csr_bankarray_csrbank4_update_value_re) begin
        main_basesoc_timer_update_value_storage <= builder_csr_bankarray_csrbank4_update_value_r;
    end
    main_basesoc_timer_update_value_wr_stb <= builder_csr_bankarray_csrbank4_update_value_re;
    main_basesoc_timer_value_wr_stb <= builder_csr_bankarray_csrbank4_value_re;
    main_basesoc_timer_status_wr_stb <= builder_csr_bankarray_csrbank4_ev_status_re;
    if (builder_csr_bankarray_csrbank4_ev_pending_re) begin
        main_basesoc_timer_pending_wr_data <= builder_csr_bankarray_csrbank4_ev_pending_r;
    end
    main_basesoc_timer_pending_wr_stb <= builder_csr_bankarray_csrbank4_ev_pending_re;
    if (builder_csr_bankarray_csrbank4_ev_enable_re) begin
        main_basesoc_timer_enable_storage <= builder_csr_bankarray_csrbank4_ev_enable_r;
    end
    main_basesoc_timer_enable_wr_stb <= builder_csr_bankarray_csrbank4_ev_enable_re;
    builder_csr_bankarray_interface5_bank_bus_dat_r <= 1'd0;
    if (builder_csr_bankarray_csrbank5_sel) begin
        case (builder_csr_bankarray_interface5_bank_bus_adr[8:0])
            1'd0: begin
                builder_csr_bankarray_interface5_bank_bus_dat_r <= main_basesoc_uart_core_rxtx_w;
            end
            1'd1: begin
                builder_csr_bankarray_interface5_bank_bus_dat_r <= builder_csr_bankarray_csrbank5_txfull_w;
            end
            2'd2: begin
                builder_csr_bankarray_interface5_bank_bus_dat_r <= builder_csr_bankarray_csrbank5_rxempty_w;
            end
            2'd3: begin
                builder_csr_bankarray_interface5_bank_bus_dat_r <= builder_csr_bankarray_csrbank5_ev_status_w;
            end
            3'd4: begin
                builder_csr_bankarray_interface5_bank_bus_dat_r <= builder_csr_bankarray_csrbank5_ev_pending_w;
            end
            3'd5: begin
                builder_csr_bankarray_interface5_bank_bus_dat_r <= builder_csr_bankarray_csrbank5_ev_enable_w;
            end
            3'd6: begin
                builder_csr_bankarray_interface5_bank_bus_dat_r <= builder_csr_bankarray_csrbank5_txempty_w;
            end
            3'd7: begin
                builder_csr_bankarray_interface5_bank_bus_dat_r <= builder_csr_bankarray_csrbank5_rxfull_w;
            end
        endcase
    end
    main_basesoc_uart_core_txfull_wr_stb <= builder_csr_bankarray_csrbank5_txfull_re;
    main_basesoc_uart_core_rxempty_wr_stb <= builder_csr_bankarray_csrbank5_rxempty_re;
    main_basesoc_uart_core_status_wr_stb <= builder_csr_bankarray_csrbank5_ev_status_re;
    if (builder_csr_bankarray_csrbank5_ev_pending_re) begin
        main_basesoc_uart_core_pending_wr_data <= builder_csr_bankarray_csrbank5_ev_pending_r;
    end
    main_basesoc_uart_core_pending_wr_stb <= builder_csr_bankarray_csrbank5_ev_pending_re;
    if (builder_csr_bankarray_csrbank5_ev_enable_re) begin
        main_basesoc_uart_core_enable_storage <= builder_csr_bankarray_csrbank5_ev_enable_r;
    end
    main_basesoc_uart_core_enable_wr_stb <= builder_csr_bankarray_csrbank5_ev_enable_re;
    main_basesoc_uart_core_txempty_wr_stb <= builder_csr_bankarray_csrbank5_txempty_re;
    main_basesoc_uart_core_rxfull_wr_stb <= builder_csr_bankarray_csrbank5_rxfull_re;
    if (sys_rst) begin
        main_basesoc_reset_storage <= 2'd0;
        main_basesoc_reset_wr_stb <= 1'd0;
        main_basesoc_scratch_storage <= 32'd305419896;
        main_basesoc_scratch_wr_stb <= 1'd0;
        main_basesoc_bus_errors_wr_stb <= 1'd0;
        main_basesoc_bus_errors <= 32'd0;
        main_basesoc_ram_bus_ack <= 1'd0;
        main_basesoc_interface0_ram_bus_ack <= 1'd0;
        main_basesoc_interface1_ram_bus_ack <= 1'd0;
        serial_tx <= 1'd1;
        main_basesoc_uart_core_tx_tick <= 1'd0;
        main_basesoc_uart_core_rx_tick <= 1'd0;
        main_basesoc_uart_core_rx_rx_d <= 1'd0;
        main_basesoc_uart_core_txfull_wr_stb <= 1'd0;
        main_basesoc_uart_core_rxempty_wr_stb <= 1'd0;
        main_basesoc_uart_core_status_wr_stb <= 1'd0;
        main_basesoc_uart_core_pending_wr_stb <= 1'd0;
        main_basesoc_uart_core_pending_wr_data <= 2'd0;
        main_basesoc_uart_core_enable_storage <= 2'd0;
        main_basesoc_uart_core_enable_wr_stb <= 1'd0;
        main_basesoc_uart_core_txempty_wr_stb <= 1'd0;
        main_basesoc_uart_core_rxfull_wr_stb <= 1'd0;
        main_basesoc_uart_core_tx_fifo_readable <= 1'd0;
        main_basesoc_uart_core_tx_fifo_level0 <= 5'd0;
        main_basesoc_uart_core_tx_fifo_produce <= 4'd0;
        main_basesoc_uart_core_tx_fifo_consume <= 4'd0;
        main_basesoc_uart_core_rx_fifo_readable <= 1'd0;
        main_basesoc_uart_core_rx_fifo_level0 <= 5'd0;
        main_basesoc_uart_core_rx_fifo_produce <= 4'd0;
        main_basesoc_uart_core_rx_fifo_consume <= 4'd0;
        main_basesoc_timer_load_storage <= 32'd0;
        main_basesoc_timer_load_wr_stb <= 1'd0;
        main_basesoc_timer_reload_storage <= 32'd0;
        main_basesoc_timer_reload_wr_stb <= 1'd0;
        main_basesoc_timer_en_storage <= 1'd0;
        main_basesoc_timer_en_wr_stb <= 1'd0;
        main_basesoc_timer_update_value_storage <= 1'd0;
        main_basesoc_timer_update_value_wr_stb <= 1'd0;
        main_basesoc_timer_value_status <= 32'd0;
        main_basesoc_timer_value_wr_stb <= 1'd0;
        main_basesoc_timer_zero_pending <= 1'd0;
        main_basesoc_timer_zero_trigger_d <= 1'd0;
        main_basesoc_timer_status_wr_stb <= 1'd0;
        main_basesoc_timer_pending_wr_stb <= 1'd0;
        main_basesoc_timer_pending_wr_data <= 1'd0;
        main_basesoc_timer_enable_storage <= 1'd0;
        main_basesoc_timer_enable_wr_stb <= 1'd0;
        main_basesoc_timer_value <= 32'd0;
        main_ethphy_reset_storage <= 1'd0;
        main_ethphy_reset_wr_stb <= 1'd0;
        main_ethphy_hw_reset_counter <= 9'd0;
        main_ethphy__w_storage <= 3'd0;
        main_ethphy__w_wr_stb <= 1'd0;
        main_ethphy__r_wr_stb <= 1'd0;
        main_basesoc_core_wr_stb <= 1'd0;
        main_basesoc_core_tx_cdc_cdc_graycounter0_q <= 6'd0;
        main_basesoc_core_tx_cdc_cdc_graycounter0_q_binary <= 6'd0;
        main_basesoc_core_preamble_errors_status <= 32'd0;
        main_basesoc_core_preamble_errors_wr_stb <= 1'd0;
        main_basesoc_core_crc_errors_status <= 32'd0;
        main_basesoc_core_crc_errors_wr_stb <= 1'd0;
        main_basesoc_core_rx_cdc_cdc_graycounter1_q <= 6'd0;
        main_basesoc_core_rx_cdc_cdc_graycounter1_q_binary <= 6'd0;
        main_basesoc_wishbone_interface_writer_slot_wr_stb <= 1'd0;
        main_basesoc_wishbone_interface_writer_length_wr_stb <= 1'd0;
        main_basesoc_wishbone_interface_writer_errors_status <= 32'd0;
        main_basesoc_wishbone_interface_writer_errors_wr_stb <= 1'd0;
        main_basesoc_wishbone_interface_writer_status_wr_stb <= 1'd0;
        main_basesoc_wishbone_interface_writer_pending_wr_stb <= 1'd0;
        main_basesoc_wishbone_interface_writer_pending_wr_data <= 1'd0;
        main_basesoc_wishbone_interface_writer_enable_storage <= 1'd0;
        main_basesoc_wishbone_interface_writer_enable_wr_stb <= 1'd0;
        main_basesoc_wishbone_interface_writer_packet_length1 <= 11'd0;
        main_basesoc_wishbone_interface_writer_packet_error1 <= 1'd0;
        main_basesoc_wishbone_interface_writer_packet_pkt_len <= 11'd0;
        main_basesoc_wishbone_interface_writer_slot <= 1'd0;
        main_basesoc_wishbone_interface_writer_stat_fifo_level <= 2'd0;
        main_basesoc_wishbone_interface_writer_stat_fifo_produce <= 1'd0;
        main_basesoc_wishbone_interface_writer_stat_fifo_consume <= 1'd0;
        main_basesoc_wishbone_interface_reader_ready_wr_stb <= 1'd0;
        main_basesoc_wishbone_interface_reader_level_wr_stb <= 1'd0;
        main_basesoc_wishbone_interface_reader_slot_wr_stb <= 1'd0;
        main_basesoc_wishbone_interface_reader_length_wr_stb <= 1'd0;
        main_basesoc_wishbone_interface_reader_eventsourcepulse_pending <= 1'd0;
        main_basesoc_wishbone_interface_reader_status_wr_stb <= 1'd0;
        main_basesoc_wishbone_interface_reader_pending_wr_stb <= 1'd0;
        main_basesoc_wishbone_interface_reader_pending_wr_data <= 1'd0;
        main_basesoc_wishbone_interface_reader_enable_storage <= 1'd0;
        main_basesoc_wishbone_interface_reader_enable_wr_stb <= 1'd0;
        main_basesoc_wishbone_interface_reader_cmd_fifo_level <= 2'd0;
        main_basesoc_wishbone_interface_reader_cmd_fifo_produce <= 1'd0;
        main_basesoc_wishbone_interface_reader_cmd_fifo_consume <= 1'd0;
        main_basesoc_wishbone_interface_reader_rd_offset <= 11'd0;
        main_basesoc_wishbone_interface_interface0_ack <= 1'd0;
        main_basesoc_wishbone_interface_interface1_ack <= 1'd0;
        main_basesoc_wishbone_interface_decoder0_slave_sel_r <= 2'd0;
        main_basesoc_wishbone_interface_interface2_ack <= 1'd0;
        main_basesoc_wishbone_interface_interface3_ack <= 1'd0;
        main_basesoc_wishbone_interface_decoder1_slave_sel_r <= 2'd0;
        main_storage <= 8'd0;
        main_wr_stb <= 1'd0;
        main_chaser <= 8'd0;
        main_mode <= 1'd0;
        main_count <= 23'd6250000;
        builder_grant <= 1'd0;
        builder_slave_sel_r <= 6'd0;
        builder_count <= 20'd1000000;
        builder_csr_bankarray_sel_r <= 1'd0;
        builder_rs232phytx_state <= 1'd0;
        builder_rs232phyrx_state <= 1'd0;
        builder_clockdomainsrenamer_state <= 3'd0;
        builder_clockdomainsrenamer_liteethmacpacketreader_state <= 2'd0;
        builder_clockdomainsrenamer_fsm_state <= 2'd0;
        builder_wishbone2csr_state <= 1'd0;
    end
    builder_xilinxmultiregimpl00 <= serial_rx;
    builder_xilinxmultiregimpl01 <= builder_xilinxmultiregimpl00;
    builder_xilinxmultiregimpl10 <= main_ethphy_data_r;
    builder_xilinxmultiregimpl11 <= builder_xilinxmultiregimpl10;
    builder_xilinxmultiregimpl20 <= eth_tx_rst;
    builder_xilinxmultiregimpl21 <= builder_xilinxmultiregimpl20;
    builder_xilinxmultiregimpl50 <= main_basesoc_core_tx_cdc_cdc_graycounter1_q;
    builder_xilinxmultiregimpl51 <= builder_xilinxmultiregimpl50;
    builder_xilinxmultiregimpl60 <= main_basesoc_core_pulsesynchronizer0_toggle_i;
    builder_xilinxmultiregimpl61 <= builder_xilinxmultiregimpl60;
    builder_xilinxmultiregimpl70 <= main_basesoc_core_pulsesynchronizer1_toggle_i;
    builder_xilinxmultiregimpl71 <= builder_xilinxmultiregimpl70;
    builder_xilinxmultiregimpl90 <= main_basesoc_core_rx_cdc_write_rst;
    builder_xilinxmultiregimpl91 <= builder_xilinxmultiregimpl90;
    builder_xilinxmultiregimpl100 <= main_basesoc_core_rx_cdc_cdc_graycounter0_q;
    builder_xilinxmultiregimpl101 <= builder_xilinxmultiregimpl100;
end



BUFG BUFG(
	.I (main_crg_clkout0),

	.O (main_crg_clkout_buf0)
);

BUFG BUFG_1(
	.I (main_crg_clkout1),

	.O (main_crg_clkout_buf1)
);

BUFG BUFG_2(
	.I (main_crg_clkout2),

	.O (main_crg_clkout_buf2)
);

BUFG BUFG_3(
	.I (main_crg_clkout3),

	.O (main_crg_clkout_buf3)
);

BUFG BUFG_4(
	.I (main_crg_clkout4),

	.O (main_crg_clkout_buf4)
);

IDELAYCTRL IDELAYCTRL(
	.REFCLK (idelay_clk),
	.RST    (main_crg_ic_reset)
);

reg [31:0] rom[0:9196];
initial begin
	$readmemh("digilent_nexys_video_rom.init", rom);
end
reg [31:0] rom_dat0;
always @(posedge sys_clk) begin
	rom_dat0 <= rom[main_basesoc_adr];
end
assign main_basesoc_dat_r = rom_dat0;


reg [31:0] sram[0:2047];
initial begin
	$readmemh("digilent_nexys_video_sram.init", sram);
end
reg [10:0] sram_adr0;
always @(posedge sys_clk) begin : mem_write_block
	integer we_index;
	for(we_index = 0; we_index < 4; we_index=we_index+1)
		if (main_basesoc_sram0_we[we_index])
			sram[main_basesoc_sram0_adr][we_index*8 +: 8] <= main_basesoc_sram0_dat_w[we_index*8 +: 8];
	sram_adr0 <= main_basesoc_sram0_adr;
end
assign main_basesoc_sram0_dat_r = sram[sram_adr0];


reg [31:0] main_ram[0:16383];
initial begin
	$readmemh("digilent_nexys_video_main_ram.init", main_ram);
end
reg [13:0] main_ram_adr0;
always @(posedge sys_clk) begin : mem_write_block_1
	integer we_index_1;
	for(we_index_1 = 0; we_index_1 < 4; we_index_1=we_index_1+1)
		if (main_basesoc_sram1_we[we_index_1])
			main_ram[main_basesoc_sram1_adr][we_index_1*8 +: 8] <= main_basesoc_sram1_dat_w[we_index_1*8 +: 8];
	main_ram_adr0 <= main_basesoc_sram1_adr;
end
assign main_basesoc_sram1_dat_r = main_ram[main_ram_adr0];


reg [7:0] mem[0:44];
initial begin
	$readmemh("digilent_nexys_video_mem.init", mem);
end
reg [7:0] mem_dat0;
always @(posedge sys_clk) begin
	mem_dat0 <= mem[builder_csr_bankarray_adr];
end
assign builder_csr_bankarray_dat_r = mem_dat0;


reg [9:0] storage[0:15];
reg [9:0] storage_dat0;
reg [9:0] storage_dat1;
always @(posedge sys_clk) begin
	if (main_basesoc_uart_core_tx_fifo_wrport_we)
		storage[main_basesoc_uart_core_tx_fifo_wrport_adr] <= main_basesoc_uart_core_tx_fifo_wrport_dat_w;
	storage_dat0 <= storage[main_basesoc_uart_core_tx_fifo_wrport_adr];
end
always @(posedge sys_clk) begin
	if (main_basesoc_uart_core_tx_fifo_rdport_re) begin
		storage_dat1 <= storage[main_basesoc_uart_core_tx_fifo_rdport_adr];
	end
end
assign main_basesoc_uart_core_tx_fifo_wrport_dat_r = storage_dat0;
assign main_basesoc_uart_core_tx_fifo_rdport_dat_r = storage_dat1;


reg [9:0] storage_1[0:15];
reg [9:0] storage_1_dat0;
reg [9:0] storage_1_dat1;
always @(posedge sys_clk) begin
	if (main_basesoc_uart_core_rx_fifo_wrport_we)
		storage_1[main_basesoc_uart_core_rx_fifo_wrport_adr] <= main_basesoc_uart_core_rx_fifo_wrport_dat_w;
	storage_1_dat0 <= storage_1[main_basesoc_uart_core_rx_fifo_wrport_adr];
end
always @(posedge sys_clk) begin
	if (main_basesoc_uart_core_rx_fifo_rdport_re) begin
		storage_1_dat1 <= storage_1[main_basesoc_uart_core_rx_fifo_rdport_adr];
	end
end
assign main_basesoc_uart_core_rx_fifo_wrport_dat_r = storage_1_dat0;
assign main_basesoc_uart_core_rx_fifo_rdport_dat_r = storage_1_dat1;


IBUF IBUF(
	.I (eth_clocks_rx),

	.O (main_ethphy_eth_rx_clk_ibuf)
);

BUFG BUFG_5(
	.I (main_ethphy_eth_rx_clk_ibuf),

	.O (eth_rx_clk)
);

BUFG BUFG_6(
	.I (main_ethphy_clkout0),

	.O (main_ethphy_clkout_buf0)
);

BUFG BUFG_7(
	.I (main_ethphy_clkout1),

	.O (main_ethphy_clkout_buf1)
);

ODDR #(
	.DDR_CLK_EDGE ("SAME_EDGE")
) ODDR (
	.C  (eth_tx_delayed_clk),
	.CE (1'd1),
	.D1 (1'd1),
	.D2 (1'd0),
	.R  (1'd0),
	.S  (1'd0),

	.Q  (main_ethphy_eth_tx_clk_obuf)
);

OBUF OBUF(
	.I (main_ethphy_eth_tx_clk_obuf),

	.O (eth_clocks_tx)
);

ODDR #(
	.DDR_CLK_EDGE ("SAME_EDGE")
) ODDR_1 (
	.C  (eth_tx_clk),
	.CE (1'd1),
	.D1 (main_ethphy_sink_valid),
	.D2 (main_ethphy_sink_valid),
	.R  (1'd0),
	.S  (1'd0),

	.Q  (main_ethphy_tx_ctl_obuf)
);

OBUF OBUF_1(
	.I (main_ethphy_tx_ctl_obuf),

	.O (eth_tx_ctl)
);

ODDR #(
	.DDR_CLK_EDGE ("SAME_EDGE")
) ODDR_2 (
	.C  (eth_tx_clk),
	.CE (1'd1),
	.D1 (main_ethphy_sink_payload_data[0]),
	.D2 (main_ethphy_sink_payload_data[4]),
	.R  (1'd0),
	.S  (1'd0),

	.Q  (main_ethphy_tx_data_obuf[0])
);

OBUF OBUF_2(
	.I (main_ethphy_tx_data_obuf[0]),

	.O (eth_tx_data[0])
);

ODDR #(
	.DDR_CLK_EDGE ("SAME_EDGE")
) ODDR_3 (
	.C  (eth_tx_clk),
	.CE (1'd1),
	.D1 (main_ethphy_sink_payload_data[1]),
	.D2 (main_ethphy_sink_payload_data[5]),
	.R  (1'd0),
	.S  (1'd0),

	.Q  (main_ethphy_tx_data_obuf[1])
);

OBUF OBUF_3(
	.I (main_ethphy_tx_data_obuf[1]),

	.O (eth_tx_data[1])
);

ODDR #(
	.DDR_CLK_EDGE ("SAME_EDGE")
) ODDR_4 (
	.C  (eth_tx_clk),
	.CE (1'd1),
	.D1 (main_ethphy_sink_payload_data[2]),
	.D2 (main_ethphy_sink_payload_data[6]),
	.R  (1'd0),
	.S  (1'd0),

	.Q  (main_ethphy_tx_data_obuf[2])
);

OBUF OBUF_4(
	.I (main_ethphy_tx_data_obuf[2]),

	.O (eth_tx_data[2])
);

ODDR #(
	.DDR_CLK_EDGE ("SAME_EDGE")
) ODDR_5 (
	.C  (eth_tx_clk),
	.CE (1'd1),
	.D1 (main_ethphy_sink_payload_data[3]),
	.D2 (main_ethphy_sink_payload_data[7]),
	.R  (1'd0),
	.S  (1'd0),

	.Q  (main_ethphy_tx_data_obuf[3])
);

OBUF OBUF_5(
	.I (main_ethphy_tx_data_obuf[3]),

	.O (eth_tx_data[3])
);

IBUF IBUF_1(
	.I (eth_rx_ctl),

	.O (main_ethphy_rx_ctl_ibuf)
);

IDELAYE2 #(
	.IDELAY_TYPE      ("FIXED"),
	.IDELAY_VALUE     (5'd26),
	.REFCLK_FREQUENCY (200.0)
) IDELAYE2 (
	.C        (1'd0),
	.CE       (1'd0),
	.IDATAIN  (main_ethphy_rx_ctl_ibuf),
	.INC      (1'd0),
	.LD       (1'd0),
	.LDPIPEEN (1'd0),

	.DATAOUT  (main_ethphy_rx_ctl_idelay)
);

IDDR #(
	.DDR_CLK_EDGE ("SAME_EDGE_PIPELINED")
) IDDR (
	.C  (eth_rx_clk),
	.CE (1'd1),
	.D  (main_ethphy_rx_ctl_idelay),
	.R  (1'd0),
	.S  (1'd0),

	.Q1 (main_ethphy_rx_ctl[0]),
	.Q2 (main_ethphy_rx_ctl[1])
);

IBUF IBUF_2(
	.I (eth_rx_data[0]),

	.O (main_ethphy_rx_data_ibuf[0])
);

IDELAYE2 #(
	.IDELAY_TYPE      ("FIXED"),
	.IDELAY_VALUE     (5'd26),
	.REFCLK_FREQUENCY (200.0)
) IDELAYE2_1 (
	.C        (1'd0),
	.CE       (1'd0),
	.IDATAIN  (main_ethphy_rx_data_ibuf[0]),
	.INC      (1'd0),
	.LD       (1'd0),
	.LDPIPEEN (1'd0),

	.DATAOUT  (main_ethphy_rx_data_idelay[0])
);

IDDR #(
	.DDR_CLK_EDGE ("SAME_EDGE_PIPELINED")
) IDDR_1 (
	.C  (eth_rx_clk),
	.CE (1'd1),
	.D  (main_ethphy_rx_data_idelay[0]),
	.R  (1'd0),
	.S  (1'd0),

	.Q1 (main_ethphy_rx_data[0]),
	.Q2 (main_ethphy_rx_data[4])
);

IBUF IBUF_3(
	.I (eth_rx_data[1]),

	.O (main_ethphy_rx_data_ibuf[1])
);

IDELAYE2 #(
	.IDELAY_TYPE      ("FIXED"),
	.IDELAY_VALUE     (5'd26),
	.REFCLK_FREQUENCY (200.0)
) IDELAYE2_2 (
	.C        (1'd0),
	.CE       (1'd0),
	.IDATAIN  (main_ethphy_rx_data_ibuf[1]),
	.INC      (1'd0),
	.LD       (1'd0),
	.LDPIPEEN (1'd0),

	.DATAOUT  (main_ethphy_rx_data_idelay[1])
);

IDDR #(
	.DDR_CLK_EDGE ("SAME_EDGE_PIPELINED")
) IDDR_2 (
	.C  (eth_rx_clk),
	.CE (1'd1),
	.D  (main_ethphy_rx_data_idelay[1]),
	.R  (1'd0),
	.S  (1'd0),

	.Q1 (main_ethphy_rx_data[1]),
	.Q2 (main_ethphy_rx_data[5])
);

IBUF IBUF_4(
	.I (eth_rx_data[2]),

	.O (main_ethphy_rx_data_ibuf[2])
);

IDELAYE2 #(
	.IDELAY_TYPE      ("FIXED"),
	.IDELAY_VALUE     (5'd26),
	.REFCLK_FREQUENCY (200.0)
) IDELAYE2_3 (
	.C        (1'd0),
	.CE       (1'd0),
	.IDATAIN  (main_ethphy_rx_data_ibuf[2]),
	.INC      (1'd0),
	.LD       (1'd0),
	.LDPIPEEN (1'd0),

	.DATAOUT  (main_ethphy_rx_data_idelay[2])
);

IDDR #(
	.DDR_CLK_EDGE ("SAME_EDGE_PIPELINED")
) IDDR_3 (
	.C  (eth_rx_clk),
	.CE (1'd1),
	.D  (main_ethphy_rx_data_idelay[2]),
	.R  (1'd0),
	.S  (1'd0),

	.Q1 (main_ethphy_rx_data[2]),
	.Q2 (main_ethphy_rx_data[6])
);

IBUF IBUF_5(
	.I (eth_rx_data[3]),

	.O (main_ethphy_rx_data_ibuf[3])
);

IDELAYE2 #(
	.IDELAY_TYPE      ("FIXED"),
	.IDELAY_VALUE     (5'd26),
	.REFCLK_FREQUENCY (200.0)
) IDELAYE2_4 (
	.C        (1'd0),
	.CE       (1'd0),
	.IDATAIN  (main_ethphy_rx_data_ibuf[3]),
	.INC      (1'd0),
	.LD       (1'd0),
	.LDPIPEEN (1'd0),

	.DATAOUT  (main_ethphy_rx_data_idelay[3])
);

IDDR #(
	.DDR_CLK_EDGE ("SAME_EDGE_PIPELINED")
) IDDR_4 (
	.C  (eth_rx_clk),
	.CE (1'd1),
	.D  (main_ethphy_rx_data_idelay[3]),
	.R  (1'd0),
	.S  (1'd0),

	.Q1 (main_ethphy_rx_data[3]),
	.Q2 (main_ethphy_rx_data[7])
);

reg [41:0] storage_2[0:31];
reg [41:0] storage_2_dat0;
reg [41:0] storage_2_dat1;
always @(posedge sys_clk) begin
	if (main_basesoc_core_tx_cdc_cdc_wrport_we)
		storage_2[main_basesoc_core_tx_cdc_cdc_wrport_adr] <= main_basesoc_core_tx_cdc_cdc_wrport_dat_w;
	storage_2_dat0 <= storage_2[main_basesoc_core_tx_cdc_cdc_wrport_adr];
end
always @(posedge eth_tx_clk) begin
	storage_2_dat1 <= storage_2[main_basesoc_core_tx_cdc_cdc_rdport_adr];
end
assign main_basesoc_core_tx_cdc_cdc_wrport_dat_r = storage_2_dat0;
assign main_basesoc_core_tx_cdc_cdc_rdport_dat_r = storage_2_dat1;


reg [11:0] storage_3[0:4];
reg [11:0] storage_3_dat0;
always @(posedge eth_rx_clk) begin
	if (main_basesoc_core_liteethmaccrc32checker_syncfifo_wrport_we)
		storage_3[main_basesoc_core_liteethmaccrc32checker_syncfifo_wrport_adr] <= main_basesoc_core_liteethmaccrc32checker_syncfifo_wrport_dat_w;
	storage_3_dat0 <= storage_3[main_basesoc_core_liteethmaccrc32checker_syncfifo_wrport_adr];
end
always @(posedge eth_rx_clk) begin
end
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_wrport_dat_r = storage_3_dat0;
assign main_basesoc_core_liteethmaccrc32checker_syncfifo_rdport_dat_r = storage_3[main_basesoc_core_liteethmaccrc32checker_syncfifo_rdport_adr];


reg [41:0] storage_4[0:31];
reg [41:0] storage_4_dat0;
reg [41:0] storage_4_dat1;
always @(posedge eth_rx_clk) begin
	if (main_basesoc_core_rx_cdc_cdc_wrport_we)
		storage_4[main_basesoc_core_rx_cdc_cdc_wrport_adr] <= main_basesoc_core_rx_cdc_cdc_wrport_dat_w;
	storage_4_dat0 <= storage_4[main_basesoc_core_rx_cdc_cdc_wrport_adr];
end
always @(posedge sys_clk) begin
	storage_4_dat1 <= storage_4[main_basesoc_core_rx_cdc_cdc_rdport_adr];
end
assign main_basesoc_core_rx_cdc_cdc_wrport_dat_r = storage_4_dat0;
assign main_basesoc_core_rx_cdc_cdc_rdport_dat_r = storage_4_dat1;


reg [13:0] storage_5[0:1];
reg [13:0] storage_5_dat0;
always @(posedge sys_clk) begin
	if (main_basesoc_wishbone_interface_writer_stat_fifo_wrport_we)
		storage_5[main_basesoc_wishbone_interface_writer_stat_fifo_wrport_adr] <= main_basesoc_wishbone_interface_writer_stat_fifo_wrport_dat_w;
	storage_5_dat0 <= storage_5[main_basesoc_wishbone_interface_writer_stat_fifo_wrport_adr];
end
always @(posedge sys_clk) begin
end
assign main_basesoc_wishbone_interface_writer_stat_fifo_wrport_dat_r = storage_5_dat0;
assign main_basesoc_wishbone_interface_writer_stat_fifo_rdport_dat_r = storage_5[main_basesoc_wishbone_interface_writer_stat_fifo_rdport_adr];


reg [31:0] mac_sram_writer_slot0[0:382];
reg [31:0] mac_sram_writer_slot0_dat0;
reg [31:0] mac_sram_writer_slot0_dat1;
always @(posedge sys_clk) begin
	if (main_basesoc_wishbone_interface_writer_memory0_we)
		mac_sram_writer_slot0[main_basesoc_wishbone_interface_writer_memory0_adr] <= main_basesoc_wishbone_interface_writer_memory0_dat_w;
	if (main_basesoc_wishbone_interface_writer_memory0_we)
		mac_sram_writer_slot0_dat0 <= main_basesoc_wishbone_interface_writer_memory0_dat_w;
	else
		mac_sram_writer_slot0_dat0 <= mac_sram_writer_slot0[main_basesoc_wishbone_interface_writer_memory0_adr];
end
always @(posedge sys_clk) begin
	mac_sram_writer_slot0_dat1 <= mac_sram_writer_slot0[main_basesoc_wishbone_interface_sram0_adr];
end
assign main_basesoc_wishbone_interface_writer_memory0_dat_r = mac_sram_writer_slot0_dat0;
assign main_basesoc_wishbone_interface_sram0_dat_r = mac_sram_writer_slot0_dat1;


reg [31:0] mac_sram_writer_slot1[0:382];
reg [31:0] mac_sram_writer_slot1_dat0;
reg [31:0] mac_sram_writer_slot1_dat1;
always @(posedge sys_clk) begin
	if (main_basesoc_wishbone_interface_writer_memory1_we)
		mac_sram_writer_slot1[main_basesoc_wishbone_interface_writer_memory1_adr] <= main_basesoc_wishbone_interface_writer_memory1_dat_w;
	if (main_basesoc_wishbone_interface_writer_memory1_we)
		mac_sram_writer_slot1_dat0 <= main_basesoc_wishbone_interface_writer_memory1_dat_w;
	else
		mac_sram_writer_slot1_dat0 <= mac_sram_writer_slot1[main_basesoc_wishbone_interface_writer_memory1_adr];
end
always @(posedge sys_clk) begin
	mac_sram_writer_slot1_dat1 <= mac_sram_writer_slot1[main_basesoc_wishbone_interface_sram1_adr];
end
assign main_basesoc_wishbone_interface_writer_memory1_dat_r = mac_sram_writer_slot1_dat0;
assign main_basesoc_wishbone_interface_sram1_dat_r = mac_sram_writer_slot1_dat1;


reg [13:0] storage_6[0:1];
reg [13:0] storage_6_dat0;
always @(posedge sys_clk) begin
	if (main_basesoc_wishbone_interface_reader_cmd_fifo_wrport_we)
		storage_6[main_basesoc_wishbone_interface_reader_cmd_fifo_wrport_adr] <= main_basesoc_wishbone_interface_reader_cmd_fifo_wrport_dat_w;
	storage_6_dat0 <= storage_6[main_basesoc_wishbone_interface_reader_cmd_fifo_wrport_adr];
end
always @(posedge sys_clk) begin
end
assign main_basesoc_wishbone_interface_reader_cmd_fifo_wrport_dat_r = storage_6_dat0;
assign main_basesoc_wishbone_interface_reader_cmd_fifo_rdport_dat_r = storage_6[main_basesoc_wishbone_interface_reader_cmd_fifo_rdport_adr];


reg [31:0] mac_sram_reader_slot0[0:382];
reg [31:0] mac_sram_reader_slot0_dat0;
reg [8:0] mac_sram_reader_slot0_adr1;
always @(posedge sys_clk) begin
	if (main_basesoc_wishbone_interface_reader_memory0_re) begin
		mac_sram_reader_slot0_dat0 <= mac_sram_reader_slot0[main_basesoc_wishbone_interface_reader_memory0_adr];
	end
end
always @(posedge sys_clk) begin : mem_write_block_2
	integer we_index_2;
	for(we_index_2 = 0; we_index_2 < 4; we_index_2=we_index_2+1)
		if (main_basesoc_wishbone_interface_sram2_we[we_index_2])
			mac_sram_reader_slot0[main_basesoc_wishbone_interface_sram2_adr][we_index_2*8 +: 8] <= main_basesoc_wishbone_interface_sram2_dat_w[we_index_2*8 +: 8];
	mac_sram_reader_slot0_adr1 <= main_basesoc_wishbone_interface_sram2_adr;
end
assign main_basesoc_wishbone_interface_reader_memory0_dat_r = mac_sram_reader_slot0_dat0;
assign main_basesoc_wishbone_interface_sram2_dat_r = mac_sram_reader_slot0[mac_sram_reader_slot0_adr1];


reg [31:0] mac_sram_reader_slot1[0:382];
reg [31:0] mac_sram_reader_slot1_dat0;
reg [8:0] mac_sram_reader_slot1_adr1;
always @(posedge sys_clk) begin
	if (main_basesoc_wishbone_interface_reader_memory1_re) begin
		mac_sram_reader_slot1_dat0 <= mac_sram_reader_slot1[main_basesoc_wishbone_interface_reader_memory1_adr];
	end
end
always @(posedge sys_clk) begin : mem_write_block_3
	integer we_index_3;
	for(we_index_3 = 0; we_index_3 < 4; we_index_3=we_index_3+1)
		if (main_basesoc_wishbone_interface_sram3_we[we_index_3])
			mac_sram_reader_slot1[main_basesoc_wishbone_interface_sram3_adr][we_index_3*8 +: 8] <= main_basesoc_wishbone_interface_sram3_dat_w[we_index_3*8 +: 8];
	mac_sram_reader_slot1_adr1 <= main_basesoc_wishbone_interface_sram3_adr;
end
assign main_basesoc_wishbone_interface_reader_memory1_dat_r = mac_sram_reader_slot1_dat0;
assign main_basesoc_wishbone_interface_sram3_dat_r = mac_sram_reader_slot1[mac_sram_reader_slot1_adr1];


FDCE FDCE(
	.C   (main_crg_clkin_signal),
	.CE  (1'd1),
	.CLR (1'd0),
	.D   (main_crg_reset),

	.Q   (builder_crg_reset0)
);

FDCE FDCE_1(
	.C   (main_crg_clkin_signal),
	.CE  (1'd1),
	.CLR (1'd0),
	.D   (builder_crg_reset0),

	.Q   (builder_crg_reset1)
);

FDCE FDCE_2(
	.C   (main_crg_clkin_signal),
	.CE  (1'd1),
	.CLR (1'd0),
	.D   (builder_crg_reset1),

	.Q   (builder_crg_reset2)
);

FDCE FDCE_3(
	.C   (main_crg_clkin_signal),
	.CE  (1'd1),
	.CLR (1'd0),
	.D   (builder_crg_reset2),

	.Q   (builder_crg_reset3)
);

FDCE FDCE_4(
	.C   (main_crg_clkin_signal),
	.CE  (1'd1),
	.CLR (1'd0),
	.D   (builder_crg_reset3),

	.Q   (builder_crg_reset4)
);

FDCE FDCE_5(
	.C   (main_crg_clkin_signal),
	.CE  (1'd1),
	.CLR (1'd0),
	.D   (builder_crg_reset4),

	.Q   (builder_crg_reset5)
);

FDCE FDCE_6(
	.C   (main_crg_clkin_signal),
	.CE  (1'd1),
	.CLR (1'd0),
	.D   (builder_crg_reset5),

	.Q   (builder_crg_reset6)
);

FDCE FDCE_7(
	.C   (main_crg_clkin_signal),
	.CE  (1'd1),
	.CLR (1'd0),
	.D   (builder_crg_reset6),

	.Q   (builder_crg_reset7)
);

MMCME2_ADV #(
	.BANDWIDTH        ("OPTIMIZED"),
	.CLKFBOUT_MULT_F  (4'd12),
	.CLKIN1_PERIOD    (10.0),
	.CLKOUT0_DIVIDE_F (4'd12),
	.CLKOUT0_PHASE    (1'd0),
	.CLKOUT1_DIVIDE   (2'd3),
	.CLKOUT1_PHASE    (1'd0),
	.CLKOUT2_DIVIDE   (2'd3),
	.CLKOUT2_PHASE    (7'd90),
	.CLKOUT3_DIVIDE   (3'd6),
	.CLKOUT3_PHASE    (1'd0),
	.CLKOUT4_DIVIDE   (4'd12),
	.CLKOUT4_PHASE    (1'd0),
	.DIVCLK_DIVIDE    (1'd1),
	.REF_JITTER1      (0.01)
) MMCME2_ADV (
	.CLKFBIN  (builder_crg_mmcm_fb),
	.CLKIN1   (main_crg_clkin_signal),
	.PWRDWN   (main_crg_power_down),
	.RST      (builder_crg_reset7),

	.CLKFBOUT (builder_crg_mmcm_fb),
	.CLKOUT0  (main_crg_clkout0),
	.CLKOUT1  (main_crg_clkout1),
	.CLKOUT2  (main_crg_clkout2),
	.CLKOUT3  (main_crg_clkout3),
	.CLKOUT4  (main_crg_clkout4),
	.LOCKED   (main_crg_locked)
);

VexRiscv VexRiscv(
	.clk                    (sys_clk),
	.dBusWishbone_ACK       (main_basesoc_dbus_ack),
	.dBusWishbone_DAT_MISO  (main_basesoc_dbus_dat_r),
	.dBusWishbone_ERR       (main_basesoc_dbus_err),
	.externalInterruptArray (main_basesoc_interrupt),
	.externalResetVector    (main_basesoc_vexriscv),
	.iBusWishbone_ACK       (main_basesoc_ibus_ack),
	.iBusWishbone_DAT_MISO  (main_basesoc_ibus_dat_r),
	.iBusWishbone_ERR       (main_basesoc_ibus_err),
	.reset                  ((sys_rst | main_basesoc_reset)),
	.softwareInterrupt      (1'd0),
	.timerInterrupt         (1'd0),

	.dBusWishbone_ADR       (main_basesoc_dbus_adr),
	.dBusWishbone_BTE       (main_basesoc_dbus_bte),
	.dBusWishbone_CTI       (main_basesoc_dbus_cti),
	.dBusWishbone_CYC       (main_basesoc_dbus_cyc),
	.dBusWishbone_DAT_MOSI  (main_basesoc_dbus_dat_w),
	.dBusWishbone_SEL       (main_basesoc_dbus_sel),
	.dBusWishbone_STB       (main_basesoc_dbus_stb),
	.dBusWishbone_WE        (main_basesoc_dbus_we),
	.iBusWishbone_ADR       (main_basesoc_ibus_adr),
	.iBusWishbone_BTE       (main_basesoc_ibus_bte),
	.iBusWishbone_CTI       (main_basesoc_ibus_cti),
	.iBusWishbone_CYC       (main_basesoc_ibus_cyc),
	.iBusWishbone_DAT_MOSI  (main_basesoc_ibus_dat_w),
	.iBusWishbone_SEL       (main_basesoc_ibus_sel),
	.iBusWishbone_STB       (main_basesoc_ibus_stb),
	.iBusWishbone_WE        (main_basesoc_ibus_we)
);

FDCE FDCE_8(
	.C   (main_ethphy_clkin_signal),
	.CE  (1'd1),
	.CLR (1'd0),
	.D   (main_ethphy_pll_reset),

	.Q   (builder_liteethphyrgmii_reset0)
);

FDCE FDCE_9(
	.C   (main_ethphy_clkin_signal),
	.CE  (1'd1),
	.CLR (1'd0),
	.D   (builder_liteethphyrgmii_reset0),

	.Q   (builder_liteethphyrgmii_reset1)
);

FDCE FDCE_10(
	.C   (main_ethphy_clkin_signal),
	.CE  (1'd1),
	.CLR (1'd0),
	.D   (builder_liteethphyrgmii_reset1),

	.Q   (builder_liteethphyrgmii_reset2)
);

FDCE FDCE_11(
	.C   (main_ethphy_clkin_signal),
	.CE  (1'd1),
	.CLR (1'd0),
	.D   (builder_liteethphyrgmii_reset2),

	.Q   (builder_liteethphyrgmii_reset3)
);

FDCE FDCE_12(
	.C   (main_ethphy_clkin_signal),
	.CE  (1'd1),
	.CLR (1'd0),
	.D   (builder_liteethphyrgmii_reset3),

	.Q   (builder_liteethphyrgmii_reset4)
);

FDCE FDCE_13(
	.C   (main_ethphy_clkin_signal),
	.CE  (1'd1),
	.CLR (1'd0),
	.D   (builder_liteethphyrgmii_reset4),

	.Q   (builder_liteethphyrgmii_reset5)
);

FDCE FDCE_14(
	.C   (main_ethphy_clkin_signal),
	.CE  (1'd1),
	.CLR (1'd0),
	.D   (builder_liteethphyrgmii_reset5),

	.Q   (builder_liteethphyrgmii_reset6)
);

FDCE FDCE_15(
	.C   (main_ethphy_clkin_signal),
	.CE  (1'd1),
	.CLR (1'd0),
	.D   (builder_liteethphyrgmii_reset6),

	.Q   (builder_liteethphyrgmii_reset7)
);

PLLE2_ADV #(
	.CLKFBOUT_MULT  (4'd12),
	.CLKIN1_PERIOD  (8.0),
	.CLKOUT0_DIVIDE (4'd12),
	.CLKOUT0_PHASE  (1'd0),
	.CLKOUT1_DIVIDE (4'd12),
	.CLKOUT1_PHASE  (90.0),
	.DIVCLK_DIVIDE  (1'd1),
	.REF_JITTER1    (0.01),
	.STARTUP_WAIT   ("FALSE")
) PLLE2_ADV (
	.CLKFBIN  (builder_liteethphyrgmii_pll_fb),
	.CLKIN1   (main_ethphy_clkin_signal),
	.PWRDWN   (main_ethphy_pll_power_down),
	.RST      (builder_liteethphyrgmii_reset7),

	.CLKFBOUT (builder_liteethphyrgmii_pll_fb),
	.CLKOUT0  (main_ethphy_clkout0),
	.CLKOUT1  (main_ethphy_clkout1),
	.LOCKED   (main_ethphy_pll_locked)
);

(* ars_ff1 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE (
	.C   (sys_clk),
	.CE  (1'd1),
	.D   (1'd0),
	.PRE (builder_xilinxasyncresetsynchronizerimpl0_async_reset),

	.Q   (builder_xilinxasyncresetsynchronizerimpl0_rst_meta)
);

(* ars_ff2 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_1 (
	.C   (sys_clk),
	.CE  (1'd1),
	.D   (builder_xilinxasyncresetsynchronizerimpl0_rst_meta),
	.PRE (builder_xilinxasyncresetsynchronizerimpl0_async_reset),

	.Q   (builder_xilinxasyncresetsynchronizerimpl0_rst_buf)
);

BUFG BUFG_8(
	.I (builder_xilinxasyncresetsynchronizerimpl0_rst_buf),

	.O (sys_rst)
);

(* ars_ff1 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_2 (
	.C   (sys4x_clk),
	.CE  (1'd1),
	.D   (1'd0),
	.PRE (builder_xilinxasyncresetsynchronizerimpl1_async_reset),

	.Q   (builder_xilinxasyncresetsynchronizerimpl1_rst_meta)
);

(* ars_ff2 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_3 (
	.C   (sys4x_clk),
	.CE  (1'd1),
	.D   (builder_xilinxasyncresetsynchronizerimpl1_rst_meta),
	.PRE (builder_xilinxasyncresetsynchronizerimpl1_async_reset),

	.Q   (sys4x_rst)
);

(* ars_ff1 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_4 (
	.C   (sys4x_dqs_clk),
	.CE  (1'd1),
	.D   (1'd0),
	.PRE (builder_xilinxasyncresetsynchronizerimpl2_async_reset),

	.Q   (builder_xilinxasyncresetsynchronizerimpl2_rst_meta)
);

(* ars_ff2 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_5 (
	.C   (sys4x_dqs_clk),
	.CE  (1'd1),
	.D   (builder_xilinxasyncresetsynchronizerimpl2_rst_meta),
	.PRE (builder_xilinxasyncresetsynchronizerimpl2_async_reset),

	.Q   (sys4x_dqs_rst)
);

(* ars_ff1 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_6 (
	.C   (idelay_clk),
	.CE  (1'd1),
	.D   (1'd0),
	.PRE (builder_xilinxasyncresetsynchronizerimpl3_async_reset),

	.Q   (builder_xilinxasyncresetsynchronizerimpl3_rst_meta)
);

(* ars_ff2 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_7 (
	.C   (idelay_clk),
	.CE  (1'd1),
	.D   (builder_xilinxasyncresetsynchronizerimpl3_rst_meta),
	.PRE (builder_xilinxasyncresetsynchronizerimpl3_async_reset),

	.Q   (idelay_rst)
);

(* ars_ff1 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_8 (
	.C   (clk100_clk),
	.CE  (1'd1),
	.D   (1'd0),
	.PRE (builder_xilinxasyncresetsynchronizerimpl4_async_reset),

	.Q   (builder_xilinxasyncresetsynchronizerimpl4_rst_meta)
);

(* ars_ff2 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_9 (
	.C   (clk100_clk),
	.CE  (1'd1),
	.D   (builder_xilinxasyncresetsynchronizerimpl4_rst_meta),
	.PRE (builder_xilinxasyncresetsynchronizerimpl4_async_reset),

	.Q   (clk100_rst)
);

(* ars_ff1 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_10 (
	.C   (eth_tx_delayed_clk),
	.CE  (1'd1),
	.D   (1'd0),
	.PRE (builder_xilinxasyncresetsynchronizerimpl5_async_reset),

	.Q   (builder_xilinxasyncresetsynchronizerimpl5_rst_meta)
);

(* ars_ff2 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_11 (
	.C   (eth_tx_delayed_clk),
	.CE  (1'd1),
	.D   (builder_xilinxasyncresetsynchronizerimpl5_rst_meta),
	.PRE (builder_xilinxasyncresetsynchronizerimpl5_async_reset),

	.Q   (builder_xilinxasyncresetsynchronizerimpl5_expr)
);

(* ars_ff1 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_12 (
	.C   (eth_tx_clk),
	.CE  (1'd1),
	.D   (1'd0),
	.PRE (main_ethphy_reset),

	.Q   (builder_xilinxasyncresetsynchronizerimpl6_rst_meta)
);

(* ars_ff2 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_13 (
	.C   (eth_tx_clk),
	.CE  (1'd1),
	.D   (builder_xilinxasyncresetsynchronizerimpl6_rst_meta),
	.PRE (main_ethphy_reset),

	.Q   (eth_tx_rst)
);

(* ars_ff1 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_14 (
	.C   (eth_rx_clk),
	.CE  (1'd1),
	.D   (1'd0),
	.PRE (main_ethphy_reset),

	.Q   (builder_xilinxasyncresetsynchronizerimpl7_rst_meta)
);

(* ars_ff2 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_15 (
	.C   (eth_rx_clk),
	.CE  (1'd1),
	.D   (builder_xilinxasyncresetsynchronizerimpl7_rst_meta),
	.PRE (main_ethphy_reset),

	.Q   (eth_rx_rst)
);

IOBUF IOBUF(
	.I  (main_ethphy_data_w),
	.T  ((~main_ethphy_data_oe)),

	.O  (main_ethphy_data_r),

	.IO (eth_mdio)
);

endmodule

