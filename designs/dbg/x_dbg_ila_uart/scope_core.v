
`timescale 1ns / 1ps


module scope_core (
    input  wire          dbg_clk,
    input  wire   [31:0] dbg_probe,
    input  wire          dbg_serial_rx,
    output reg           dbg_serial_tx
);





reg    [31:0] builder_basiclowerer_self = 32'd0;
reg    [19:0] builder_count = 20'd1000000;
wire    [4:0] builder_csr_bankarray_adr;
wire          builder_csr_bankarray_csrbank0_mux_value_r;
reg           builder_csr_bankarray_csrbank0_mux_value_re = 1'd0;
wire          builder_csr_bankarray_csrbank0_mux_value_w;
reg           builder_csr_bankarray_csrbank0_mux_value_we = 1'd0;
wire          builder_csr_bankarray_csrbank0_sel;
wire          builder_csr_bankarray_csrbank0_storage_done_r;
reg           builder_csr_bankarray_csrbank0_storage_done_re = 1'd0;
wire          builder_csr_bankarray_csrbank0_storage_done_w;
reg           builder_csr_bankarray_csrbank0_storage_done_we = 1'd0;
wire          builder_csr_bankarray_csrbank0_storage_enable_r;
reg           builder_csr_bankarray_csrbank0_storage_enable_re = 1'd0;
wire          builder_csr_bankarray_csrbank0_storage_enable_w;
reg           builder_csr_bankarray_csrbank0_storage_enable_we = 1'd0;
wire   [11:0] builder_csr_bankarray_csrbank0_storage_length_r;
reg           builder_csr_bankarray_csrbank0_storage_length_re = 1'd0;
wire   [11:0] builder_csr_bankarray_csrbank0_storage_length_w;
reg           builder_csr_bankarray_csrbank0_storage_length_we = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank0_storage_mem_data_r;
reg           builder_csr_bankarray_csrbank0_storage_mem_data_re = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank0_storage_mem_data_w;
reg           builder_csr_bankarray_csrbank0_storage_mem_data_we = 1'd0;
wire   [11:0] builder_csr_bankarray_csrbank0_storage_mem_level_r;
reg           builder_csr_bankarray_csrbank0_storage_mem_level_re = 1'd0;
wire   [11:0] builder_csr_bankarray_csrbank0_storage_mem_level_w;
reg           builder_csr_bankarray_csrbank0_storage_mem_level_we = 1'd0;
wire   [11:0] builder_csr_bankarray_csrbank0_storage_offset_r;
reg           builder_csr_bankarray_csrbank0_storage_offset_re = 1'd0;
wire   [11:0] builder_csr_bankarray_csrbank0_storage_offset_w;
reg           builder_csr_bankarray_csrbank0_storage_offset_we = 1'd0;
wire   [15:0] builder_csr_bankarray_csrbank0_subsampler_value_r;
reg           builder_csr_bankarray_csrbank0_subsampler_value_re = 1'd0;
wire   [15:0] builder_csr_bankarray_csrbank0_subsampler_value_w;
reg           builder_csr_bankarray_csrbank0_subsampler_value_we = 1'd0;
wire          builder_csr_bankarray_csrbank0_trigger_done_r;
reg           builder_csr_bankarray_csrbank0_trigger_done_re = 1'd0;
wire          builder_csr_bankarray_csrbank0_trigger_done_w;
reg           builder_csr_bankarray_csrbank0_trigger_done_we = 1'd0;
wire          builder_csr_bankarray_csrbank0_trigger_enable_r;
reg           builder_csr_bankarray_csrbank0_trigger_enable_re = 1'd0;
wire          builder_csr_bankarray_csrbank0_trigger_enable_w;
reg           builder_csr_bankarray_csrbank0_trigger_enable_we = 1'd0;
wire          builder_csr_bankarray_csrbank0_trigger_mem_full_r;
reg           builder_csr_bankarray_csrbank0_trigger_mem_full_re = 1'd0;
wire          builder_csr_bankarray_csrbank0_trigger_mem_full_w;
reg           builder_csr_bankarray_csrbank0_trigger_mem_full_we = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank0_trigger_mem_mask_r;
reg           builder_csr_bankarray_csrbank0_trigger_mem_mask_re = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank0_trigger_mem_mask_w;
reg           builder_csr_bankarray_csrbank0_trigger_mem_mask_we = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank0_trigger_mem_value_r;
reg           builder_csr_bankarray_csrbank0_trigger_mem_value_re = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank0_trigger_mem_value_w;
reg           builder_csr_bankarray_csrbank0_trigger_mem_value_we = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank1_bus_errors_r;
reg           builder_csr_bankarray_csrbank1_bus_errors_re = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank1_bus_errors_w;
reg           builder_csr_bankarray_csrbank1_bus_errors_we = 1'd0;
wire    [1:0] builder_csr_bankarray_csrbank1_reset_r;
reg           builder_csr_bankarray_csrbank1_reset_re = 1'd0;
wire    [1:0] builder_csr_bankarray_csrbank1_reset_w;
reg           builder_csr_bankarray_csrbank1_reset_we = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank1_scratch_r;
reg           builder_csr_bankarray_csrbank1_scratch_re = 1'd0;
wire   [31:0] builder_csr_bankarray_csrbank1_scratch_w;
reg           builder_csr_bankarray_csrbank1_scratch_we = 1'd0;
wire          builder_csr_bankarray_csrbank1_sel;
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
wire          builder_grant;
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
reg     [1:0] builder_litescopeanalyzer_next_state = 2'd0;
reg     [1:0] builder_litescopeanalyzer_state = 2'd0;
wire          builder_request;
reg    [29:0] builder_rhs_self0 = 30'd0;
reg    [31:0] builder_rhs_self1 = 32'd0;
reg     [3:0] builder_rhs_self2 = 4'd0;
reg           builder_rhs_self3 = 1'd0;
reg           builder_rhs_self4 = 1'd0;
reg           builder_rhs_self5 = 1'd0;
reg     [2:0] builder_rhs_self6 = 3'd0;
reg     [1:0] builder_rhs_self7 = 2'd0;
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
wire          builder_slave_sel;
reg           builder_slave_sel_r = 1'd0;
reg     [2:0] builder_uartbone_next_state = 3'd0;
reg           builder_uartbone_rs232phyrx_next_state = 1'd0;
reg           builder_uartbone_rs232phyrx_state = 1'd0;
reg           builder_uartbone_rs232phytx_next_state = 1'd0;
reg           builder_uartbone_rs232phytx_state = 1'd0;
reg     [2:0] builder_uartbone_state = 3'd0;
wire          builder_wait;
reg           builder_wishbone2csr_next_state = 1'd0;
reg           builder_wishbone2csr_state = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl00 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl01 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl10 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl100 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl101 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl11 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg    [11:0] builder_xilinxmultiregimpl110 = 12'd0;
(* async_reg = "true", dont_touch = "true" *)
reg    [11:0] builder_xilinxmultiregimpl111 = 12'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg     [2:0] builder_xilinxmultiregimpl120 = 3'd0;
(* async_reg = "true", dont_touch = "true" *)
reg     [2:0] builder_xilinxmultiregimpl121 = 3'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg     [2:0] builder_xilinxmultiregimpl130 = 3'd0;
(* async_reg = "true", dont_touch = "true" *)
reg     [2:0] builder_xilinxmultiregimpl131 = 3'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl140 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl141 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl20 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl21 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl30 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl31 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg     [4:0] builder_xilinxmultiregimpl40 = 5'd0;
(* async_reg = "true", dont_touch = "true" *)
reg     [4:0] builder_xilinxmultiregimpl41 = 5'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg     [4:0] builder_xilinxmultiregimpl50 = 5'd0;
(* async_reg = "true", dont_touch = "true" *)
reg     [4:0] builder_xilinxmultiregimpl51 = 5'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg    [15:0] builder_xilinxmultiregimpl60 = 16'd0;
(* async_reg = "true", dont_touch = "true" *)
reg    [15:0] builder_xilinxmultiregimpl61 = 16'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl70 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           builder_xilinxmultiregimpl71 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg    [11:0] builder_xilinxmultiregimpl80 = 12'd0;
(* async_reg = "true", dont_touch = "true" *)
reg    [11:0] builder_xilinxmultiregimpl81 = 12'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg    [11:0] builder_xilinxmultiregimpl90 = 12'd0;
(* async_reg = "true", dont_touch = "true" *)
reg    [11:0] builder_xilinxmultiregimpl91 = 12'd0;
reg     [1:0] main_addr_bytes_count = 2'd0;
reg     [1:0] main_addr_bytes_count_next_value1 = 2'd0;
reg           main_addr_bytes_count_next_value_ce1 = 1'd0;
reg    [31:0] main_address = 32'd0;
reg    [31:0] main_address_next_value5 = 32'd0;
reg           main_address_next_value_ce5 = 1'd0;
reg           main_analyzer_mux_first = 1'd0;
reg           main_analyzer_mux_last = 1'd0;
wire   [31:0] main_analyzer_mux_payload_data;
reg           main_analyzer_mux_payload_hit = 1'd0;
reg           main_analyzer_mux_ready = 1'd0;
reg           main_analyzer_mux_source_first = 1'd0;
reg           main_analyzer_mux_source_last = 1'd0;
reg    [31:0] main_analyzer_mux_source_payload_data = 32'd0;
reg           main_analyzer_mux_source_payload_hit = 1'd0;
wire          main_analyzer_mux_source_ready;
reg           main_analyzer_mux_source_valid = 1'd0;
wire          main_analyzer_mux_valid;
wire          main_analyzer_mux_value;
reg           main_analyzer_mux_value_storage = 1'd0;
reg           main_analyzer_mux_value_wr_stb = 1'd0;
wire   [33:0] main_analyzer_storage_cdc_asyncfifo_din;
wire   [33:0] main_analyzer_storage_cdc_asyncfifo_dout;
wire          main_analyzer_storage_cdc_asyncfifo_re;
wire          main_analyzer_storage_cdc_asyncfifo_readable;
wire          main_analyzer_storage_cdc_asyncfifo_we;
wire          main_analyzer_storage_cdc_asyncfifo_writable;
wire    [2:0] main_analyzer_storage_cdc_consume_wdomain;
wire          main_analyzer_storage_cdc_fifo_in_first;
wire          main_analyzer_storage_cdc_fifo_in_last;
wire   [31:0] main_analyzer_storage_cdc_fifo_in_payload_data;
wire          main_analyzer_storage_cdc_fifo_out_first;
wire          main_analyzer_storage_cdc_fifo_out_last;
wire   [31:0] main_analyzer_storage_cdc_fifo_out_payload_data;
wire          main_analyzer_storage_cdc_graycounter0_ce;
(* dont_touch = "true" *)
reg     [2:0] main_analyzer_storage_cdc_graycounter0_q = 3'd0;
reg     [2:0] main_analyzer_storage_cdc_graycounter0_q_binary = 3'd0;
wire    [2:0] main_analyzer_storage_cdc_graycounter0_q_next;
reg     [2:0] main_analyzer_storage_cdc_graycounter0_q_next_binary = 3'd0;
wire          main_analyzer_storage_cdc_graycounter1_ce;
(* dont_touch = "true" *)
reg     [2:0] main_analyzer_storage_cdc_graycounter1_q = 3'd0;
reg     [2:0] main_analyzer_storage_cdc_graycounter1_q_binary = 3'd0;
wire    [2:0] main_analyzer_storage_cdc_graycounter1_q_next;
reg     [2:0] main_analyzer_storage_cdc_graycounter1_q_next_binary = 3'd0;
wire    [2:0] main_analyzer_storage_cdc_produce_rdomain;
wire    [1:0] main_analyzer_storage_cdc_rdport_adr;
wire   [33:0] main_analyzer_storage_cdc_rdport_dat_r;
reg           main_analyzer_storage_cdc_sink_first = 1'd0;
reg           main_analyzer_storage_cdc_sink_last = 1'd0;
reg    [31:0] main_analyzer_storage_cdc_sink_payload_data = 32'd0;
wire          main_analyzer_storage_cdc_sink_ready;
reg           main_analyzer_storage_cdc_sink_valid = 1'd0;
wire          main_analyzer_storage_cdc_source_first;
wire          main_analyzer_storage_cdc_source_last;
wire   [31:0] main_analyzer_storage_cdc_source_payload_data;
wire          main_analyzer_storage_cdc_source_ready;
wire          main_analyzer_storage_cdc_source_valid;
wire    [1:0] main_analyzer_storage_cdc_wrport_adr;
wire   [33:0] main_analyzer_storage_cdc_wrport_dat_r;
wire   [33:0] main_analyzer_storage_cdc_wrport_dat_w;
wire          main_analyzer_storage_cdc_wrport_we;
reg    [11:0] main_analyzer_storage_count = 12'h800;
reg           main_analyzer_storage_done0 = 1'd0;
wire          main_analyzer_storage_done1;
wire          main_analyzer_storage_done_rd_stb;
wire          main_analyzer_storage_done_status;
reg           main_analyzer_storage_done_wr_stb = 1'd0;
wire          main_analyzer_storage_enable;
reg           main_analyzer_storage_enable_d = 1'd0;
reg           main_analyzer_storage_enable_storage = 1'd0;
reg           main_analyzer_storage_enable_wr_stb = 1'd0;
reg           main_analyzer_storage_flush = 1'd0;
reg           main_analyzer_storage_flush_read = 1'd0;
wire          main_analyzer_storage_flush_read_sys;
wire   [11:0] main_analyzer_storage_length;
reg    [11:0] main_analyzer_storage_length_storage = 12'd0;
reg           main_analyzer_storage_length_wr_stb = 1'd0;
wire   [11:0] main_analyzer_storage_level;
reg    [10:0] main_analyzer_storage_mem_consume = 11'd0;
wire          main_analyzer_storage_mem_data_rd_stb;
wire   [31:0] main_analyzer_storage_mem_data_status;
reg           main_analyzer_storage_mem_data_wr_stb = 1'd0;
wire          main_analyzer_storage_mem_do_read;
wire          main_analyzer_storage_mem_fifo_in_first;
wire          main_analyzer_storage_mem_fifo_in_last;
wire   [31:0] main_analyzer_storage_mem_fifo_in_payload_data;
wire          main_analyzer_storage_mem_fifo_out_first;
wire          main_analyzer_storage_mem_fifo_out_last;
wire   [31:0] main_analyzer_storage_mem_fifo_out_payload_data;
reg    [11:0] main_analyzer_storage_mem_level0 = 12'd0;
wire   [11:0] main_analyzer_storage_mem_level1;
wire          main_analyzer_storage_mem_level_rd_stb;
wire   [11:0] main_analyzer_storage_mem_level_status;
reg           main_analyzer_storage_mem_level_wr_stb = 1'd0;
reg    [10:0] main_analyzer_storage_mem_produce = 11'd0;
wire   [10:0] main_analyzer_storage_mem_rdport_adr;
wire   [33:0] main_analyzer_storage_mem_rdport_dat_r;
wire          main_analyzer_storage_mem_rdport_re;
wire          main_analyzer_storage_mem_re;
reg           main_analyzer_storage_mem_readable = 1'd0;
reg           main_analyzer_storage_mem_replace = 1'd0;
reg           main_analyzer_storage_mem_sink_first = 1'd0;
reg           main_analyzer_storage_mem_sink_last = 1'd0;
reg    [31:0] main_analyzer_storage_mem_sink_payload_data = 32'd0;
wire          main_analyzer_storage_mem_sink_ready;
reg           main_analyzer_storage_mem_sink_valid = 1'd0;
wire          main_analyzer_storage_mem_source_first;
wire          main_analyzer_storage_mem_source_last;
wire   [31:0] main_analyzer_storage_mem_source_payload_data;
reg           main_analyzer_storage_mem_source_ready = 1'd0;
wire          main_analyzer_storage_mem_source_valid;
wire   [33:0] main_analyzer_storage_mem_syncfifo_din;
wire   [33:0] main_analyzer_storage_mem_syncfifo_dout;
wire          main_analyzer_storage_mem_syncfifo_re;
wire          main_analyzer_storage_mem_syncfifo_readable;
wire          main_analyzer_storage_mem_syncfifo_we;
wire          main_analyzer_storage_mem_syncfifo_writable;
reg    [10:0] main_analyzer_storage_mem_wrport_adr = 11'd0;
wire   [33:0] main_analyzer_storage_mem_wrport_dat_r;
wire   [33:0] main_analyzer_storage_mem_wrport_dat_w;
wire          main_analyzer_storage_mem_wrport_we;
wire   [11:0] main_analyzer_storage_offset;
reg    [11:0] main_analyzer_storage_offset_storage = 12'd0;
reg           main_analyzer_storage_offset_wr_stb = 1'd0;
reg           main_analyzer_storage_post_hit = 1'd0;
wire          main_analyzer_storage_read_source_first;
wire          main_analyzer_storage_read_source_last;
wire   [31:0] main_analyzer_storage_read_source_payload_data;
wire          main_analyzer_storage_read_source_ready;
wire          main_analyzer_storage_read_source_valid;
wire          main_analyzer_storage_sink_sink_first;
wire          main_analyzer_storage_sink_sink_last;
wire   [31:0] main_analyzer_storage_sink_sink_payload_data;
wire          main_analyzer_storage_sink_sink_payload_hit;
reg           main_analyzer_storage_sink_sink_ready = 1'd0;
wire          main_analyzer_storage_sink_sink_valid;
reg           main_analyzer_storage_wait = 1'd0;
reg    [15:0] main_analyzer_subsampler_counter = 16'd0;
wire          main_analyzer_subsampler_done;
wire          main_analyzer_subsampler_sink_first;
wire          main_analyzer_subsampler_sink_last;
wire   [31:0] main_analyzer_subsampler_sink_payload_data;
wire          main_analyzer_subsampler_sink_payload_hit;
wire          main_analyzer_subsampler_sink_ready;
wire          main_analyzer_subsampler_sink_valid;
wire          main_analyzer_subsampler_source_first;
wire          main_analyzer_subsampler_source_last;
wire   [31:0] main_analyzer_subsampler_source_payload_data;
wire          main_analyzer_subsampler_source_payload_hit;
wire          main_analyzer_subsampler_source_ready;
wire          main_analyzer_subsampler_source_valid;
wire   [15:0] main_analyzer_subsampler_value;
reg    [15:0] main_analyzer_subsampler_value_storage = 16'd0;
reg           main_analyzer_subsampler_value_wr_stb = 1'd0;
wire          main_analyzer_trigger_done;
wire          main_analyzer_trigger_done_rd_stb;
wire          main_analyzer_trigger_done_status;
reg           main_analyzer_trigger_done_wr_stb = 1'd0;
wire          main_analyzer_trigger_enable;
reg           main_analyzer_trigger_enable_d = 1'd0;
reg           main_analyzer_trigger_enable_storage = 1'd0;
reg           main_analyzer_trigger_enable_wr_stb = 1'd0;
reg           main_analyzer_trigger_flushing = 1'd0;
wire          main_analyzer_trigger_hit;
wire   [65:0] main_analyzer_trigger_mem_asyncfifo_din;
wire   [65:0] main_analyzer_trigger_mem_asyncfifo_dout;
wire          main_analyzer_trigger_mem_asyncfifo_re;
wire          main_analyzer_trigger_mem_asyncfifo_readable;
wire          main_analyzer_trigger_mem_asyncfifo_we;
wire          main_analyzer_trigger_mem_asyncfifo_writable;
wire    [4:0] main_analyzer_trigger_mem_consume_wdomain;
reg    [65:0] main_analyzer_trigger_mem_dout = 66'd0;
wire          main_analyzer_trigger_mem_fifo_in_first;
wire          main_analyzer_trigger_mem_fifo_in_last;
wire   [31:0] main_analyzer_trigger_mem_fifo_in_payload_mask;
wire   [31:0] main_analyzer_trigger_mem_fifo_in_payload_value;
wire          main_analyzer_trigger_mem_fifo_out_first;
wire          main_analyzer_trigger_mem_fifo_out_last;
wire   [31:0] main_analyzer_trigger_mem_fifo_out_payload_mask;
wire   [31:0] main_analyzer_trigger_mem_fifo_out_payload_value;
wire          main_analyzer_trigger_mem_full_rd_stb;
wire          main_analyzer_trigger_mem_full_status;
reg           main_analyzer_trigger_mem_full_wr_stb = 1'd0;
wire          main_analyzer_trigger_mem_graycounter0_ce;
(* dont_touch = "true" *)
reg     [4:0] main_analyzer_trigger_mem_graycounter0_q = 5'd0;
reg     [4:0] main_analyzer_trigger_mem_graycounter0_q_binary = 5'd0;
wire    [4:0] main_analyzer_trigger_mem_graycounter0_q_next;
reg     [4:0] main_analyzer_trigger_mem_graycounter0_q_next_binary = 5'd0;
wire          main_analyzer_trigger_mem_graycounter1_ce;
(* dont_touch = "true" *)
reg     [4:0] main_analyzer_trigger_mem_graycounter1_q = 5'd0;
reg     [4:0] main_analyzer_trigger_mem_graycounter1_q_binary = 5'd0;
wire    [4:0] main_analyzer_trigger_mem_graycounter1_q_next;
reg     [4:0] main_analyzer_trigger_mem_graycounter1_q_next_binary = 5'd0;
reg    [31:0] main_analyzer_trigger_mem_mask_storage = 32'd0;
reg           main_analyzer_trigger_mem_mask_wr_stb = 1'd0;
wire    [4:0] main_analyzer_trigger_mem_produce_rdomain;
wire    [3:0] main_analyzer_trigger_mem_rdport_adr;
wire   [65:0] main_analyzer_trigger_mem_rdport_dat_r;
wire          main_analyzer_trigger_mem_re;
reg           main_analyzer_trigger_mem_readable = 1'd0;
reg           main_analyzer_trigger_mem_sink_first = 1'd0;
reg           main_analyzer_trigger_mem_sink_last = 1'd0;
wire   [31:0] main_analyzer_trigger_mem_sink_payload_mask;
wire   [31:0] main_analyzer_trigger_mem_sink_payload_value;
wire          main_analyzer_trigger_mem_sink_ready;
wire          main_analyzer_trigger_mem_sink_valid;
wire          main_analyzer_trigger_mem_source_first;
wire          main_analyzer_trigger_mem_source_last;
wire   [31:0] main_analyzer_trigger_mem_source_payload_mask;
wire   [31:0] main_analyzer_trigger_mem_source_payload_value;
wire          main_analyzer_trigger_mem_source_ready;
wire          main_analyzer_trigger_mem_source_valid;
reg    [31:0] main_analyzer_trigger_mem_value_storage = 32'd0;
reg           main_analyzer_trigger_mem_value_wr_stb = 1'd0;
wire          main_analyzer_trigger_mem_write_r;
reg           main_analyzer_trigger_mem_write_re = 1'd0;
reg           main_analyzer_trigger_mem_write_w = 1'd0;
reg           main_analyzer_trigger_mem_write_we = 1'd0;
wire    [3:0] main_analyzer_trigger_mem_wrport_adr;
wire   [65:0] main_analyzer_trigger_mem_wrport_dat_r;
wire   [65:0] main_analyzer_trigger_mem_wrport_dat_w;
wire          main_analyzer_trigger_mem_wrport_we;
reg           main_analyzer_trigger_sink_d_first = 1'd0;
reg           main_analyzer_trigger_sink_d_last = 1'd0;
reg    [31:0] main_analyzer_trigger_sink_d_payload_data = 32'd0;
reg           main_analyzer_trigger_sink_d_payload_hit = 1'd0;
reg           main_analyzer_trigger_sink_d_valid = 1'd0;
wire          main_analyzer_trigger_sink_sink_first;
wire          main_analyzer_trigger_sink_sink_last;
wire   [31:0] main_analyzer_trigger_sink_sink_payload_data;
wire          main_analyzer_trigger_sink_sink_payload_hit;
wire          main_analyzer_trigger_sink_sink_ready;
wire          main_analyzer_trigger_sink_sink_valid;
wire          main_analyzer_trigger_source_source_first;
wire          main_analyzer_trigger_source_source_last;
wire   [31:0] main_analyzer_trigger_source_source_payload_data;
reg           main_analyzer_trigger_source_source_payload_hit = 1'd0;
wire          main_analyzer_trigger_source_source_ready;
wire          main_analyzer_trigger_source_source_valid;
wire          main_bus_error;
reg    [31:0] main_bus_errors = 32'd0;
wire          main_bus_errors_rd_stb;
wire   [31:0] main_bus_errors_status;
reg           main_bus_errors_wr_stb = 1'd0;
reg     [7:0] main_cmd = 8'd0;
reg     [7:0] main_cmd_next_value3 = 8'd0;
reg           main_cmd_next_value_ce3 = 1'd0;
reg    [23:0] main_count = 24'd10000000;
wire          main_cpu_rst;
reg    [31:0] main_data = 32'd0;
reg     [1:0] main_data_bytes_count = 2'd0;
reg     [1:0] main_data_bytes_count_next_value0 = 2'd0;
reg           main_data_bytes_count_next_value_ce0 = 1'd0;
reg    [31:0] main_data_next_value7 = 32'd0;
reg           main_data_next_value_ce7 = 1'd0;
reg           main_dbg_serial_tx_rs232phytx_next_value1 = 1'd0;
reg           main_dbg_serial_tx_rs232phytx_next_value_ce1 = 1'd0;
wire          main_done;
wire   [15:0] main_dq;
reg           main_incr = 1'd0;
reg           main_incr_next_value6 = 1'd0;
reg           main_incr_next_value_ce6 = 1'd0;
reg           main_is_ongoing = 1'd0;
reg     [7:0] main_length = 8'd0;
reg     [7:0] main_length_next_value4 = 8'd0;
reg           main_length_next_value_ce4 = 1'd0;
wire          main_reset;
reg     [1:0] main_reset_storage = 2'd0;
reg           main_reset_wr_stb = 1'd0;
reg     [3:0] main_rx_count = 4'd0;
reg     [3:0] main_rx_count_rs232phyrx_next_value0 = 4'd0;
reg           main_rx_count_rs232phyrx_next_value_ce0 = 1'd0;
reg     [7:0] main_rx_data = 8'd0;
reg     [7:0] main_rx_data_rs232phyrx_next_value1 = 8'd0;
reg           main_rx_data_rs232phyrx_next_value_ce1 = 1'd0;
reg           main_rx_enable = 1'd0;
reg           main_rx_framing_error = 1'd0;
reg           main_rx_overflow = 1'd0;
reg    [31:0] main_rx_phase = 32'd0;
wire          main_rx_rx;
reg           main_rx_rx_d = 1'd0;
reg     [7:0] main_rx_source_payload_data = 8'd0;
reg           main_rx_source_ready = 1'd0;
reg           main_rx_source_valid = 1'd0;
reg           main_rx_tick = 1'd0;
wire   [15:0] main_s;
reg    [31:0] main_scratch_storage = 32'd305419896;
reg           main_scratch_wr_stb = 1'd0;
reg           main_soc_rst = 1'd0;
reg     [3:0] main_tx_count = 4'd0;
reg     [3:0] main_tx_count_rs232phytx_next_value0 = 4'd0;
reg           main_tx_count_rs232phytx_next_value_ce0 = 1'd0;
reg     [7:0] main_tx_data = 8'd0;
reg     [7:0] main_tx_data_rs232phytx_next_value2 = 8'd0;
reg           main_tx_data_rs232phytx_next_value_ce2 = 1'd0;
reg           main_tx_enable = 1'd0;
reg    [31:0] main_tx_phase = 32'd0;
wire          main_tx_sink_last;
reg     [7:0] main_tx_sink_payload_data = 8'd0;
reg           main_tx_sink_ready = 1'd0;
reg           main_tx_sink_valid = 1'd0;
reg           main_tx_tick = 1'd0;
wire          main_wait;
wire          main_wishbone_ack;
wire   [29:0] main_wishbone_adr;
reg     [1:0] main_wishbone_bte = 2'd0;
reg     [2:0] main_wishbone_cti = 3'd0;
reg           main_wishbone_cyc = 1'd0;
wire   [31:0] main_wishbone_dat_r;
wire   [31:0] main_wishbone_dat_w;
wire          main_wishbone_err;
wire    [3:0] main_wishbone_sel;
reg           main_wishbone_stb = 1'd0;
reg           main_wishbone_we = 1'd0;
reg     [7:0] main_words_count = 8'd0;
reg     [7:0] main_words_count_next_value2 = 8'd0;
reg           main_words_count_next_value_ce2 = 1'd0;
wire          scope_clk;
reg           scope_rst = 1'd0;
wire          sys_clk;
reg           sys_rst = 1'd0;


assign sys_clk = dbg_clk;
assign main_dq = dbg_probe[15:0];
assign main_s = dbg_probe[31:16];
assign main_bus_error = builder_error;
assign builder_shared_adr = builder_rhs_self0;
assign builder_shared_dat_w = builder_rhs_self1;
assign builder_shared_sel = builder_rhs_self2;
assign builder_shared_cyc = builder_rhs_self3;
assign builder_shared_stb = builder_rhs_self4;
assign builder_shared_we = builder_rhs_self5;
assign builder_shared_cti = builder_rhs_self6;
assign builder_shared_bte = builder_rhs_self7;
assign main_wishbone_dat_r = builder_shared_dat_r;
assign main_wishbone_ack = (builder_shared_ack & (builder_grant == 1'd0));
assign main_wishbone_err = (builder_shared_err & (builder_grant == 1'd0));
assign builder_request = {main_wishbone_cyc};
assign builder_grant = 1'd0;
assign builder_slave_sel = (builder_shared_adr[29:14] == 1'd0);
assign builder_interface0_adr = builder_shared_adr;
assign builder_interface0_dat_w = builder_shared_dat_w;
assign builder_interface0_sel = builder_shared_sel;
assign builder_interface0_stb = builder_shared_stb;
assign builder_interface0_we = builder_shared_we;
assign builder_interface0_cti = builder_shared_cti;
assign builder_interface0_bte = builder_shared_bte;
assign builder_interface0_cyc = (builder_shared_cyc & builder_slave_sel);
assign builder_shared_err = builder_interface0_err;
assign builder_wait = ((builder_shared_stb & builder_shared_cyc) & (~builder_shared_ack));
always @(*) begin
    builder_error = 1'd0;
    builder_shared_ack = 1'd0;
    builder_shared_dat_r = 32'd0;
    builder_shared_ack = builder_interface0_ack;
    builder_shared_dat_r = ({32{builder_slave_sel_r}} & builder_interface0_dat_r);
    if (builder_done) begin
        builder_shared_dat_r = 32'hffffffff;
        builder_shared_ack = 1'd1;
        builder_error = 1'd1;
    end
end
assign builder_done = (builder_count == 1'd0);
assign main_bus_errors_status = main_bus_errors;
assign main_wait = (~main_is_ongoing);
assign main_reset = main_done;
assign main_wishbone_adr = main_address;
assign main_wishbone_dat_w = main_data;
assign main_wishbone_sel = 4'd15;
always @(*) begin
    main_tx_sink_payload_data = 8'd0;
    case (main_data_bytes_count)
        1'd0: begin
            main_tx_sink_payload_data = main_data[31:24];
        end
        1'd1: begin
            main_tx_sink_payload_data = main_data[31:16];
        end
        2'd2: begin
            main_tx_sink_payload_data = main_data[31:8];
        end
        2'd3: begin
            main_tx_sink_payload_data = main_data;
        end
    endcase
end
assign main_tx_sink_last = ((main_data_bytes_count == 2'd3) & ($signed({1'd0, main_words_count}) == ($signed({1'd0, main_length}) - $signed({1'd0, 1'd1}))));
always @(*) begin
    builder_uartbone_rs232phytx_next_state = 1'd0;
    main_dbg_serial_tx_rs232phytx_next_value1 = 1'd0;
    main_dbg_serial_tx_rs232phytx_next_value_ce1 = 1'd0;
    main_tx_count_rs232phytx_next_value0 = 4'd0;
    main_tx_count_rs232phytx_next_value_ce0 = 1'd0;
    main_tx_data_rs232phytx_next_value2 = 8'd0;
    main_tx_data_rs232phytx_next_value_ce2 = 1'd0;
    main_tx_enable = 1'd0;
    main_tx_sink_ready = 1'd0;
    builder_uartbone_rs232phytx_next_state = builder_uartbone_rs232phytx_state;
    case (builder_uartbone_rs232phytx_state)
        1'd1: begin
            main_tx_enable = 1'd1;
            if (main_tx_tick) begin
                main_dbg_serial_tx_rs232phytx_next_value1 = main_tx_data[0];
                main_dbg_serial_tx_rs232phytx_next_value_ce1 = 1'd1;
                main_tx_count_rs232phytx_next_value0 = (main_tx_count + 1'd1);
                main_tx_count_rs232phytx_next_value_ce0 = 1'd1;
                main_tx_data_rs232phytx_next_value2 = {1'd1, main_tx_data[7:1]};
                main_tx_data_rs232phytx_next_value_ce2 = 1'd1;
                if ((main_tx_count == 4'd9)) begin
                    main_tx_sink_ready = 1'd1;
                    builder_uartbone_rs232phytx_next_state = 1'd0;
                end
            end
        end
        default: begin
            main_tx_count_rs232phytx_next_value0 = 1'd0;
            main_tx_count_rs232phytx_next_value_ce0 = 1'd1;
            main_dbg_serial_tx_rs232phytx_next_value1 = 1'd1;
            main_dbg_serial_tx_rs232phytx_next_value_ce1 = 1'd1;
            if (main_tx_sink_valid) begin
                main_dbg_serial_tx_rs232phytx_next_value1 = 1'd0;
                main_dbg_serial_tx_rs232phytx_next_value_ce1 = 1'd1;
                main_tx_data_rs232phytx_next_value2 = main_tx_sink_payload_data;
                main_tx_data_rs232phytx_next_value_ce2 = 1'd1;
                builder_uartbone_rs232phytx_next_state = 1'd1;
            end
        end
    endcase
end
always @(*) begin
    builder_uartbone_rs232phyrx_next_state = 1'd0;
    main_rx_count_rs232phyrx_next_value0 = 4'd0;
    main_rx_count_rs232phyrx_next_value_ce0 = 1'd0;
    main_rx_data_rs232phyrx_next_value1 = 8'd0;
    main_rx_data_rs232phyrx_next_value_ce1 = 1'd0;
    main_rx_enable = 1'd0;
    main_rx_framing_error = 1'd0;
    main_rx_overflow = 1'd0;
    main_rx_source_payload_data = 8'd0;
    main_rx_source_valid = 1'd0;
    builder_uartbone_rs232phyrx_next_state = builder_uartbone_rs232phyrx_state;
    case (builder_uartbone_rs232phyrx_state)
        1'd1: begin
            main_rx_enable = 1'd1;
            if (main_rx_tick) begin
                main_rx_count_rs232phyrx_next_value0 = (main_rx_count + 1'd1);
                main_rx_count_rs232phyrx_next_value_ce0 = 1'd1;
                main_rx_data_rs232phyrx_next_value1 = {main_rx_rx, main_rx_data[7:1]};
                main_rx_data_rs232phyrx_next_value_ce1 = 1'd1;
                if (((main_rx_count == 1'd0) & (main_rx_rx != 1'd0))) begin
                    builder_uartbone_rs232phyrx_next_state = 1'd0;
                end
                if ((main_rx_count == 4'd9)) begin
                    main_rx_source_valid = (main_rx_rx == 1'd1);
                    main_rx_source_payload_data = main_rx_data;
                    main_rx_framing_error = (main_rx_rx != 1'd1);
                    main_rx_overflow = ((main_rx_rx == 1'd1) & (~main_rx_source_ready));
                    builder_uartbone_rs232phyrx_next_state = 1'd0;
                end
            end
        end
        default: begin
            main_rx_count_rs232phyrx_next_value0 = 1'd0;
            main_rx_count_rs232phyrx_next_value_ce0 = 1'd1;
            if (((main_rx_rx == 1'd0) & (main_rx_rx_d == 1'd1))) begin
                builder_uartbone_rs232phyrx_next_state = 1'd1;
            end
        end
    endcase
end
always @(*) begin
    builder_uartbone_next_state = 3'd0;
    main_addr_bytes_count_next_value1 = 2'd0;
    main_addr_bytes_count_next_value_ce1 = 1'd0;
    main_address_next_value5 = 32'd0;
    main_address_next_value_ce5 = 1'd0;
    main_cmd_next_value3 = 8'd0;
    main_cmd_next_value_ce3 = 1'd0;
    main_data_bytes_count_next_value0 = 2'd0;
    main_data_bytes_count_next_value_ce0 = 1'd0;
    main_data_next_value7 = 32'd0;
    main_data_next_value_ce7 = 1'd0;
    main_incr_next_value6 = 1'd0;
    main_incr_next_value_ce6 = 1'd0;
    main_is_ongoing = 1'd0;
    main_length_next_value4 = 8'd0;
    main_length_next_value_ce4 = 1'd0;
    main_rx_source_ready = 1'd0;
    main_tx_sink_valid = 1'd0;
    main_wishbone_cyc = 1'd0;
    main_wishbone_stb = 1'd0;
    main_wishbone_we = 1'd0;
    main_words_count_next_value2 = 8'd0;
    main_words_count_next_value_ce2 = 1'd0;
    builder_uartbone_next_state = builder_uartbone_state;
    case (builder_uartbone_state)
        1'd1: begin
            main_rx_source_ready = 1'd1;
            if (main_rx_source_valid) begin
                main_length_next_value4 = main_rx_source_payload_data;
                main_length_next_value_ce4 = 1'd1;
                builder_uartbone_next_state = 2'd2;
            end
        end
        2'd2: begin
            main_rx_source_ready = 1'd1;
            if (main_rx_source_valid) begin
                main_address_next_value5 = {main_address, main_rx_source_payload_data};
                main_address_next_value_ce5 = 1'd1;
                main_addr_bytes_count_next_value1 = (main_addr_bytes_count + 1'd1);
                main_addr_bytes_count_next_value_ce1 = 1'd1;
                if ((main_addr_bytes_count == 2'd3)) begin
                    if (((main_cmd == 1'd1) | (main_cmd == 2'd3))) begin
                        main_incr_next_value6 = (main_cmd == 1'd1);
                        main_incr_next_value_ce6 = 1'd1;
                        builder_uartbone_next_state = 2'd3;
                    end else begin
                        if (((main_cmd == 2'd2) | (main_cmd == 3'd4))) begin
                            main_incr_next_value6 = (main_cmd == 2'd2);
                            main_incr_next_value_ce6 = 1'd1;
                            builder_uartbone_next_state = 3'd5;
                        end else begin
                            builder_uartbone_next_state = 1'd0;
                        end
                    end
                end
            end
        end
        2'd3: begin
            main_rx_source_ready = 1'd1;
            if (main_rx_source_valid) begin
                main_data_next_value7 = {main_data, main_rx_source_payload_data};
                main_data_next_value_ce7 = 1'd1;
                main_data_bytes_count_next_value0 = (main_data_bytes_count + 1'd1);
                main_data_bytes_count_next_value_ce0 = 1'd1;
                if ((main_data_bytes_count == 2'd3)) begin
                    builder_uartbone_next_state = 3'd4;
                end
            end
        end
        3'd4: begin
            main_rx_source_ready = 1'd0;
            main_wishbone_stb = 1'd1;
            main_wishbone_we = 1'd1;
            main_wishbone_cyc = 1'd1;
            if (main_wishbone_ack) begin
                main_words_count_next_value2 = (main_words_count + 1'd1);
                main_words_count_next_value_ce2 = 1'd1;
                main_address_next_value5 = (main_address + main_incr);
                main_address_next_value_ce5 = 1'd1;
                if (($signed({1'd0, main_words_count}) == ($signed({1'd0, main_length}) - $signed({1'd0, 1'd1})))) begin
                    builder_uartbone_next_state = 1'd0;
                end else begin
                    builder_uartbone_next_state = 2'd3;
                end
            end
        end
        3'd5: begin
            main_rx_source_ready = 1'd0;
            main_wishbone_stb = 1'd1;
            main_wishbone_we = 1'd0;
            main_wishbone_cyc = 1'd1;
            if (main_wishbone_ack) begin
                main_data_next_value7 = main_wishbone_dat_r;
                main_data_next_value_ce7 = 1'd1;
                builder_uartbone_next_state = 3'd6;
            end
        end
        3'd6: begin
            main_rx_source_ready = 1'd0;
            main_tx_sink_valid = 1'd1;
            if (main_tx_sink_ready) begin
                main_data_bytes_count_next_value0 = (main_data_bytes_count + 1'd1);
                main_data_bytes_count_next_value_ce0 = 1'd1;
                if ((main_data_bytes_count == 2'd3)) begin
                    main_words_count_next_value2 = (main_words_count + 1'd1);
                    main_words_count_next_value_ce2 = 1'd1;
                    main_address_next_value5 = (main_address + main_incr);
                    main_address_next_value_ce5 = 1'd1;
                    if (($signed({1'd0, main_words_count}) == ($signed({1'd0, main_length}) - $signed({1'd0, 1'd1})))) begin
                        builder_uartbone_next_state = 1'd0;
                    end else begin
                        builder_uartbone_next_state = 3'd5;
                    end
                end
            end
        end
        default: begin
            main_is_ongoing = 1'd1;
            main_rx_source_ready = 1'd1;
            main_data_bytes_count_next_value0 = 1'd0;
            main_data_bytes_count_next_value_ce0 = 1'd1;
            main_addr_bytes_count_next_value1 = 1'd0;
            main_addr_bytes_count_next_value_ce1 = 1'd1;
            main_words_count_next_value2 = 1'd0;
            main_words_count_next_value_ce2 = 1'd1;
            if (main_rx_source_valid) begin
                main_cmd_next_value3 = main_rx_source_payload_data;
                main_cmd_next_value_ce3 = 1'd1;
                builder_uartbone_next_state = 1'd1;
            end
        end
    endcase
end
assign main_done = (main_count == 1'd0);
assign scope_clk = sys_clk;
assign main_analyzer_mux_valid = 1'd1;
assign main_analyzer_mux_payload_data = {main_s, main_dq};
always @(*) begin
    main_analyzer_mux_ready = 1'd0;
    main_analyzer_mux_source_first = 1'd0;
    main_analyzer_mux_source_last = 1'd0;
    main_analyzer_mux_source_payload_data = 32'd0;
    main_analyzer_mux_source_payload_hit = 1'd0;
    main_analyzer_mux_source_valid = 1'd0;
    case (main_analyzer_mux_value)
        1'd0: begin
            main_analyzer_mux_source_valid = main_analyzer_mux_valid;
            main_analyzer_mux_ready = main_analyzer_mux_source_ready;
            main_analyzer_mux_source_first = main_analyzer_mux_first;
            main_analyzer_mux_source_last = main_analyzer_mux_last;
            main_analyzer_mux_source_payload_data = main_analyzer_mux_payload_data;
            main_analyzer_mux_source_payload_hit = main_analyzer_mux_payload_hit;
        end
    endcase
end
assign main_analyzer_trigger_mem_sink_valid = main_analyzer_trigger_mem_write_re;
assign main_analyzer_trigger_mem_sink_payload_mask = main_analyzer_trigger_mem_mask_storage;
assign main_analyzer_trigger_mem_sink_payload_value = main_analyzer_trigger_mem_value_storage;
assign main_analyzer_trigger_mem_full_status = (~main_analyzer_trigger_mem_sink_ready);
assign main_analyzer_trigger_sink_sink_ready = 1'd1;
assign main_analyzer_trigger_hit = ((main_analyzer_trigger_sink_d_payload_data & main_analyzer_trigger_mem_source_payload_mask) == (main_analyzer_trigger_mem_source_payload_value & main_analyzer_trigger_mem_source_payload_mask));
assign main_analyzer_trigger_mem_source_ready = (((main_analyzer_trigger_enable & main_analyzer_trigger_sink_d_valid) & main_analyzer_trigger_hit) | main_analyzer_trigger_flushing);
assign main_analyzer_trigger_source_source_valid = main_analyzer_trigger_sink_d_valid;
assign main_analyzer_trigger_source_source_first = main_analyzer_trigger_sink_d_first;
assign main_analyzer_trigger_source_source_last = main_analyzer_trigger_sink_d_last;
assign main_analyzer_trigger_source_source_payload_data = main_analyzer_trigger_sink_d_payload_data;
assign main_analyzer_trigger_done = (~main_analyzer_trigger_mem_source_valid);
always @(*) begin
    main_analyzer_trigger_source_source_payload_hit = 1'd0;
    main_analyzer_trigger_source_source_payload_hit = main_analyzer_trigger_sink_d_payload_hit;
    main_analyzer_trigger_source_source_payload_hit = main_analyzer_trigger_done;
end
assign main_analyzer_trigger_mem_asyncfifo_din = {main_analyzer_trigger_mem_fifo_in_last, main_analyzer_trigger_mem_fifo_in_first, main_analyzer_trigger_mem_fifo_in_payload_value, main_analyzer_trigger_mem_fifo_in_payload_mask};
assign {main_analyzer_trigger_mem_fifo_out_last, main_analyzer_trigger_mem_fifo_out_first, main_analyzer_trigger_mem_fifo_out_payload_value, main_analyzer_trigger_mem_fifo_out_payload_mask} = main_analyzer_trigger_mem_dout;
assign main_analyzer_trigger_mem_sink_ready = main_analyzer_trigger_mem_asyncfifo_writable;
assign main_analyzer_trigger_mem_asyncfifo_we = main_analyzer_trigger_mem_sink_valid;
assign main_analyzer_trigger_mem_fifo_in_first = main_analyzer_trigger_mem_sink_first;
assign main_analyzer_trigger_mem_fifo_in_last = main_analyzer_trigger_mem_sink_last;
assign main_analyzer_trigger_mem_fifo_in_payload_mask = main_analyzer_trigger_mem_sink_payload_mask;
assign main_analyzer_trigger_mem_fifo_in_payload_value = main_analyzer_trigger_mem_sink_payload_value;
assign main_analyzer_trigger_mem_source_valid = main_analyzer_trigger_mem_readable;
assign main_analyzer_trigger_mem_source_first = main_analyzer_trigger_mem_fifo_out_first;
assign main_analyzer_trigger_mem_source_last = main_analyzer_trigger_mem_fifo_out_last;
assign main_analyzer_trigger_mem_source_payload_mask = main_analyzer_trigger_mem_fifo_out_payload_mask;
assign main_analyzer_trigger_mem_source_payload_value = main_analyzer_trigger_mem_fifo_out_payload_value;
assign main_analyzer_trigger_mem_re = main_analyzer_trigger_mem_source_ready;
assign main_analyzer_trigger_mem_asyncfifo_re = (main_analyzer_trigger_mem_re | (~main_analyzer_trigger_mem_readable));
assign main_analyzer_trigger_mem_graycounter0_ce = (main_analyzer_trigger_mem_asyncfifo_writable & main_analyzer_trigger_mem_asyncfifo_we);
assign main_analyzer_trigger_mem_graycounter1_ce = (main_analyzer_trigger_mem_asyncfifo_readable & main_analyzer_trigger_mem_asyncfifo_re);
assign main_analyzer_trigger_mem_asyncfifo_writable = (((main_analyzer_trigger_mem_graycounter0_q[4] == main_analyzer_trigger_mem_consume_wdomain[4]) | (main_analyzer_trigger_mem_graycounter0_q[3] == main_analyzer_trigger_mem_consume_wdomain[3])) | (main_analyzer_trigger_mem_graycounter0_q[2:0] != main_analyzer_trigger_mem_consume_wdomain[2:0]));
assign main_analyzer_trigger_mem_asyncfifo_readable = (main_analyzer_trigger_mem_graycounter1_q != main_analyzer_trigger_mem_produce_rdomain);
assign main_analyzer_trigger_mem_wrport_adr = main_analyzer_trigger_mem_graycounter0_q_binary[3:0];
assign main_analyzer_trigger_mem_wrport_dat_w = main_analyzer_trigger_mem_asyncfifo_din;
assign main_analyzer_trigger_mem_wrport_we = main_analyzer_trigger_mem_graycounter0_ce;
assign main_analyzer_trigger_mem_rdport_adr = main_analyzer_trigger_mem_graycounter1_q_next_binary[3:0];
assign main_analyzer_trigger_mem_asyncfifo_dout = main_analyzer_trigger_mem_rdport_dat_r;
always @(*) begin
    main_analyzer_trigger_mem_graycounter0_q_next_binary = 5'd0;
    if (main_analyzer_trigger_mem_graycounter0_ce) begin
        main_analyzer_trigger_mem_graycounter0_q_next_binary = (main_analyzer_trigger_mem_graycounter0_q_binary + 1'd1);
    end else begin
        main_analyzer_trigger_mem_graycounter0_q_next_binary = main_analyzer_trigger_mem_graycounter0_q_binary;
    end
end
assign main_analyzer_trigger_mem_graycounter0_q_next = (main_analyzer_trigger_mem_graycounter0_q_next_binary ^ main_analyzer_trigger_mem_graycounter0_q_next_binary[4:1]);
always @(*) begin
    main_analyzer_trigger_mem_graycounter1_q_next_binary = 5'd0;
    if (main_analyzer_trigger_mem_graycounter1_ce) begin
        main_analyzer_trigger_mem_graycounter1_q_next_binary = (main_analyzer_trigger_mem_graycounter1_q_binary + 1'd1);
    end else begin
        main_analyzer_trigger_mem_graycounter1_q_next_binary = main_analyzer_trigger_mem_graycounter1_q_binary;
    end
end
assign main_analyzer_trigger_mem_graycounter1_q_next = (main_analyzer_trigger_mem_graycounter1_q_next_binary ^ main_analyzer_trigger_mem_graycounter1_q_next_binary[4:1]);
assign main_analyzer_subsampler_done = (main_analyzer_subsampler_counter == main_analyzer_subsampler_value);
assign main_analyzer_subsampler_sink_ready = main_analyzer_subsampler_source_ready;
assign main_analyzer_subsampler_source_first = main_analyzer_subsampler_sink_first;
assign main_analyzer_subsampler_source_last = main_analyzer_subsampler_sink_last;
assign main_analyzer_subsampler_source_payload_data = main_analyzer_subsampler_sink_payload_data;
assign main_analyzer_subsampler_source_payload_hit = main_analyzer_subsampler_sink_payload_hit;
assign main_analyzer_subsampler_source_valid = (main_analyzer_subsampler_sink_valid & main_analyzer_subsampler_done);
assign main_analyzer_storage_level = main_analyzer_storage_mem_level1;
assign main_analyzer_storage_read_source_valid = main_analyzer_storage_cdc_source_valid;
assign main_analyzer_storage_cdc_source_ready = main_analyzer_storage_read_source_ready;
assign main_analyzer_storage_read_source_first = main_analyzer_storage_cdc_source_first;
assign main_analyzer_storage_read_source_last = main_analyzer_storage_cdc_source_last;
assign main_analyzer_storage_read_source_payload_data = main_analyzer_storage_cdc_source_payload_data;
assign main_analyzer_storage_read_source_ready = ((main_analyzer_storage_mem_data_rd_stb | (~main_analyzer_storage_enable_storage)) | main_analyzer_storage_flush_read_sys);
assign main_analyzer_storage_mem_data_status = main_analyzer_storage_read_source_payload_data;
assign main_analyzer_storage_mem_syncfifo_din = {main_analyzer_storage_mem_fifo_in_last, main_analyzer_storage_mem_fifo_in_first, main_analyzer_storage_mem_fifo_in_payload_data};
assign {main_analyzer_storage_mem_fifo_out_last, main_analyzer_storage_mem_fifo_out_first, main_analyzer_storage_mem_fifo_out_payload_data} = main_analyzer_storage_mem_syncfifo_dout;
assign main_analyzer_storage_mem_sink_ready = main_analyzer_storage_mem_syncfifo_writable;
assign main_analyzer_storage_mem_syncfifo_we = main_analyzer_storage_mem_sink_valid;
assign main_analyzer_storage_mem_fifo_in_first = main_analyzer_storage_mem_sink_first;
assign main_analyzer_storage_mem_fifo_in_last = main_analyzer_storage_mem_sink_last;
assign main_analyzer_storage_mem_fifo_in_payload_data = main_analyzer_storage_mem_sink_payload_data;
assign main_analyzer_storage_mem_source_valid = main_analyzer_storage_mem_readable;
assign main_analyzer_storage_mem_source_first = main_analyzer_storage_mem_fifo_out_first;
assign main_analyzer_storage_mem_source_last = main_analyzer_storage_mem_fifo_out_last;
assign main_analyzer_storage_mem_source_payload_data = main_analyzer_storage_mem_fifo_out_payload_data;
assign main_analyzer_storage_mem_re = main_analyzer_storage_mem_source_ready;
assign main_analyzer_storage_mem_syncfifo_re = (main_analyzer_storage_mem_syncfifo_readable & ((~main_analyzer_storage_mem_readable) | main_analyzer_storage_mem_re));
assign main_analyzer_storage_mem_level1 = (main_analyzer_storage_mem_level0 + main_analyzer_storage_mem_readable);
always @(*) begin
    main_analyzer_storage_mem_wrport_adr = 11'd0;
    if (main_analyzer_storage_mem_replace) begin
        main_analyzer_storage_mem_wrport_adr = (main_analyzer_storage_mem_produce - 1'd1);
    end else begin
        main_analyzer_storage_mem_wrport_adr = main_analyzer_storage_mem_produce;
    end
end
assign main_analyzer_storage_mem_wrport_dat_w = main_analyzer_storage_mem_syncfifo_din;
assign main_analyzer_storage_mem_wrport_we = (main_analyzer_storage_mem_syncfifo_we & (main_analyzer_storage_mem_syncfifo_writable | main_analyzer_storage_mem_replace));
assign main_analyzer_storage_mem_do_read = (main_analyzer_storage_mem_syncfifo_readable & main_analyzer_storage_mem_syncfifo_re);
assign main_analyzer_storage_mem_rdport_adr = main_analyzer_storage_mem_consume;
assign main_analyzer_storage_mem_syncfifo_dout = main_analyzer_storage_mem_rdport_dat_r;
assign main_analyzer_storage_mem_rdport_re = main_analyzer_storage_mem_do_read;
assign main_analyzer_storage_mem_syncfifo_writable = (main_analyzer_storage_mem_level0 != 12'h800);
assign main_analyzer_storage_mem_syncfifo_readable = (main_analyzer_storage_mem_level0 != 1'd0);
assign main_analyzer_storage_cdc_asyncfifo_din = {main_analyzer_storage_cdc_fifo_in_last, main_analyzer_storage_cdc_fifo_in_first, main_analyzer_storage_cdc_fifo_in_payload_data};
assign {main_analyzer_storage_cdc_fifo_out_last, main_analyzer_storage_cdc_fifo_out_first, main_analyzer_storage_cdc_fifo_out_payload_data} = main_analyzer_storage_cdc_asyncfifo_dout;
assign main_analyzer_storage_cdc_sink_ready = main_analyzer_storage_cdc_asyncfifo_writable;
assign main_analyzer_storage_cdc_asyncfifo_we = main_analyzer_storage_cdc_sink_valid;
assign main_analyzer_storage_cdc_fifo_in_first = main_analyzer_storage_cdc_sink_first;
assign main_analyzer_storage_cdc_fifo_in_last = main_analyzer_storage_cdc_sink_last;
assign main_analyzer_storage_cdc_fifo_in_payload_data = main_analyzer_storage_cdc_sink_payload_data;
assign main_analyzer_storage_cdc_source_valid = main_analyzer_storage_cdc_asyncfifo_readable;
assign main_analyzer_storage_cdc_source_first = main_analyzer_storage_cdc_fifo_out_first;
assign main_analyzer_storage_cdc_source_last = main_analyzer_storage_cdc_fifo_out_last;
assign main_analyzer_storage_cdc_source_payload_data = main_analyzer_storage_cdc_fifo_out_payload_data;
assign main_analyzer_storage_cdc_asyncfifo_re = main_analyzer_storage_cdc_source_ready;
assign main_analyzer_storage_cdc_graycounter0_ce = (main_analyzer_storage_cdc_asyncfifo_writable & main_analyzer_storage_cdc_asyncfifo_we);
assign main_analyzer_storage_cdc_graycounter1_ce = (main_analyzer_storage_cdc_asyncfifo_readable & main_analyzer_storage_cdc_asyncfifo_re);
assign main_analyzer_storage_cdc_asyncfifo_writable = (((main_analyzer_storage_cdc_graycounter0_q[2] == main_analyzer_storage_cdc_consume_wdomain[2]) | (main_analyzer_storage_cdc_graycounter0_q[1] == main_analyzer_storage_cdc_consume_wdomain[1])) | (main_analyzer_storage_cdc_graycounter0_q[0] != main_analyzer_storage_cdc_consume_wdomain[0]));
assign main_analyzer_storage_cdc_asyncfifo_readable = (main_analyzer_storage_cdc_graycounter1_q != main_analyzer_storage_cdc_produce_rdomain);
assign main_analyzer_storage_cdc_wrport_adr = main_analyzer_storage_cdc_graycounter0_q_binary[1:0];
assign main_analyzer_storage_cdc_wrport_dat_w = main_analyzer_storage_cdc_asyncfifo_din;
assign main_analyzer_storage_cdc_wrport_we = main_analyzer_storage_cdc_graycounter0_ce;
assign main_analyzer_storage_cdc_rdport_adr = main_analyzer_storage_cdc_graycounter1_q_next_binary[1:0];
assign main_analyzer_storage_cdc_asyncfifo_dout = main_analyzer_storage_cdc_rdport_dat_r;
always @(*) begin
    main_analyzer_storage_cdc_graycounter0_q_next_binary = 3'd0;
    if (main_analyzer_storage_cdc_graycounter0_ce) begin
        main_analyzer_storage_cdc_graycounter0_q_next_binary = (main_analyzer_storage_cdc_graycounter0_q_binary + 1'd1);
    end else begin
        main_analyzer_storage_cdc_graycounter0_q_next_binary = main_analyzer_storage_cdc_graycounter0_q_binary;
    end
end
assign main_analyzer_storage_cdc_graycounter0_q_next = (main_analyzer_storage_cdc_graycounter0_q_next_binary ^ main_analyzer_storage_cdc_graycounter0_q_next_binary[2:1]);
always @(*) begin
    main_analyzer_storage_cdc_graycounter1_q_next_binary = 3'd0;
    if (main_analyzer_storage_cdc_graycounter1_ce) begin
        main_analyzer_storage_cdc_graycounter1_q_next_binary = (main_analyzer_storage_cdc_graycounter1_q_binary + 1'd1);
    end else begin
        main_analyzer_storage_cdc_graycounter1_q_next_binary = main_analyzer_storage_cdc_graycounter1_q_binary;
    end
end
assign main_analyzer_storage_cdc_graycounter1_q_next = (main_analyzer_storage_cdc_graycounter1_q_next_binary ^ main_analyzer_storage_cdc_graycounter1_q_next_binary[2:1]);
assign main_analyzer_storage_done1 = (main_analyzer_storage_count == 1'd0);
always @(*) begin
    builder_litescopeanalyzer_next_state = 2'd0;
    main_analyzer_storage_cdc_sink_first = 1'd0;
    main_analyzer_storage_cdc_sink_last = 1'd0;
    main_analyzer_storage_cdc_sink_payload_data = 32'd0;
    main_analyzer_storage_cdc_sink_valid = 1'd0;
    main_analyzer_storage_done0 = 1'd0;
    main_analyzer_storage_flush = 1'd0;
    main_analyzer_storage_flush_read = 1'd0;
    main_analyzer_storage_mem_sink_first = 1'd0;
    main_analyzer_storage_mem_sink_last = 1'd0;
    main_analyzer_storage_mem_sink_payload_data = 32'd0;
    main_analyzer_storage_mem_sink_valid = 1'd0;
    main_analyzer_storage_mem_source_ready = 1'd0;
    main_analyzer_storage_post_hit = 1'd0;
    main_analyzer_storage_sink_sink_ready = 1'd0;
    main_analyzer_storage_wait = 1'd0;
    builder_litescopeanalyzer_next_state = builder_litescopeanalyzer_state;
    case (builder_litescopeanalyzer_state)
        1'd1: begin
            main_analyzer_storage_sink_sink_ready = 1'd1;
            main_analyzer_storage_wait = 1'd1;
            main_analyzer_storage_mem_source_ready = 1'd1;
            main_analyzer_storage_flush_read = 1'd1;
            if (main_analyzer_storage_done1) begin
                builder_litescopeanalyzer_next_state = 2'd2;
            end
        end
        2'd2: begin
            main_analyzer_storage_mem_sink_valid = main_analyzer_storage_sink_sink_valid;
            main_analyzer_storage_sink_sink_ready = main_analyzer_storage_mem_sink_ready;
            main_analyzer_storage_mem_sink_first = main_analyzer_storage_sink_sink_first;
            main_analyzer_storage_mem_sink_last = main_analyzer_storage_sink_sink_last;
            main_analyzer_storage_mem_sink_payload_data = main_analyzer_storage_sink_sink_payload_data;
            if ((main_analyzer_storage_sink_sink_valid & main_analyzer_storage_sink_sink_payload_hit)) begin
                builder_litescopeanalyzer_next_state = 2'd3;
            end
            main_analyzer_storage_mem_source_ready = (main_analyzer_storage_mem_level1 >= main_analyzer_storage_offset);
        end
        2'd3: begin
            main_analyzer_storage_post_hit = 1'd1;
            main_analyzer_storage_flush = ((main_analyzer_storage_length != 1'd0) & ($signed({1'd0, main_analyzer_storage_mem_level1}) >= ($signed({1'd0, main_analyzer_storage_length}) - $signed({1'd0, 1'd1}))));
            if ((main_analyzer_storage_mem_level1 < main_analyzer_storage_length)) begin
                main_analyzer_storage_mem_sink_valid = main_analyzer_storage_sink_sink_valid;
                main_analyzer_storage_sink_sink_ready = main_analyzer_storage_mem_sink_ready;
                main_analyzer_storage_mem_sink_first = main_analyzer_storage_sink_sink_first;
                main_analyzer_storage_mem_sink_last = main_analyzer_storage_sink_sink_last;
                main_analyzer_storage_mem_sink_payload_data = main_analyzer_storage_sink_sink_payload_data;
            end
            if ((main_analyzer_storage_mem_level1 >= main_analyzer_storage_length)) begin
                builder_litescopeanalyzer_next_state = 1'd0;
            end
        end
        default: begin
            main_analyzer_storage_done0 = 1'd1;
            if ((main_analyzer_storage_enable & (~main_analyzer_storage_enable_d))) begin
                builder_litescopeanalyzer_next_state = 1'd1;
            end
            main_analyzer_storage_sink_sink_ready = 1'd1;
            main_analyzer_storage_cdc_sink_valid = main_analyzer_storage_mem_source_valid;
            main_analyzer_storage_mem_source_ready = main_analyzer_storage_cdc_sink_ready;
            main_analyzer_storage_cdc_sink_first = main_analyzer_storage_mem_source_first;
            main_analyzer_storage_cdc_sink_last = main_analyzer_storage_mem_source_last;
            main_analyzer_storage_cdc_sink_payload_data = main_analyzer_storage_mem_source_payload_data;
        end
    endcase
end
assign main_analyzer_trigger_sink_sink_valid = main_analyzer_mux_source_valid;
assign main_analyzer_mux_source_ready = main_analyzer_trigger_sink_sink_ready;
assign main_analyzer_trigger_sink_sink_first = main_analyzer_mux_source_first;
assign main_analyzer_trigger_sink_sink_last = main_analyzer_mux_source_last;
assign main_analyzer_trigger_sink_sink_payload_data = main_analyzer_mux_source_payload_data;
assign main_analyzer_trigger_sink_sink_payload_hit = main_analyzer_mux_source_payload_hit;
assign main_analyzer_subsampler_sink_valid = main_analyzer_trigger_source_source_valid;
assign main_analyzer_trigger_source_source_ready = main_analyzer_subsampler_sink_ready;
assign main_analyzer_subsampler_sink_first = main_analyzer_trigger_source_source_first;
assign main_analyzer_subsampler_sink_last = main_analyzer_trigger_source_source_last;
assign main_analyzer_subsampler_sink_payload_data = main_analyzer_trigger_source_source_payload_data;
assign main_analyzer_subsampler_sink_payload_hit = main_analyzer_trigger_source_source_payload_hit;
assign main_analyzer_storage_sink_sink_valid = main_analyzer_subsampler_source_valid;
assign main_analyzer_subsampler_source_ready = main_analyzer_storage_sink_sink_ready;
assign main_analyzer_storage_sink_sink_first = main_analyzer_subsampler_source_first;
assign main_analyzer_storage_sink_sink_last = main_analyzer_subsampler_source_last;
assign main_analyzer_storage_sink_sink_payload_data = main_analyzer_subsampler_source_payload_data;
assign main_analyzer_storage_sink_sink_payload_hit = main_analyzer_subsampler_source_payload_hit;
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
assign builder_csr_bankarray_csrbank0_mux_value_r = builder_csr_bankarray_interface0_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank0_mux_value_re = 1'd0;
    builder_csr_bankarray_csrbank0_mux_value_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 1'd0))) begin
        builder_csr_bankarray_csrbank0_mux_value_re = builder_csr_bankarray_interface0_bank_bus_we;
        builder_csr_bankarray_csrbank0_mux_value_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank0_trigger_enable_r = builder_csr_bankarray_interface0_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank0_trigger_enable_re = 1'd0;
    builder_csr_bankarray_csrbank0_trigger_enable_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 1'd1))) begin
        builder_csr_bankarray_csrbank0_trigger_enable_re = builder_csr_bankarray_interface0_bank_bus_we;
        builder_csr_bankarray_csrbank0_trigger_enable_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank0_trigger_done_r = builder_csr_bankarray_interface0_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank0_trigger_done_re = 1'd0;
    builder_csr_bankarray_csrbank0_trigger_done_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 2'd2))) begin
        builder_csr_bankarray_csrbank0_trigger_done_re = builder_csr_bankarray_interface0_bank_bus_we;
        builder_csr_bankarray_csrbank0_trigger_done_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
assign main_analyzer_trigger_mem_write_r = builder_csr_bankarray_interface0_bank_bus_dat_w[0];
always @(*) begin
    main_analyzer_trigger_mem_write_re = 1'd0;
    main_analyzer_trigger_mem_write_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 2'd3))) begin
        main_analyzer_trigger_mem_write_re = builder_csr_bankarray_interface0_bank_bus_we;
        main_analyzer_trigger_mem_write_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank0_trigger_mem_mask_r = builder_csr_bankarray_interface0_bank_bus_dat_w;
always @(*) begin
    builder_csr_bankarray_csrbank0_trigger_mem_mask_re = 1'd0;
    builder_csr_bankarray_csrbank0_trigger_mem_mask_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 3'd4))) begin
        builder_csr_bankarray_csrbank0_trigger_mem_mask_re = builder_csr_bankarray_interface0_bank_bus_we;
        builder_csr_bankarray_csrbank0_trigger_mem_mask_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank0_trigger_mem_value_r = builder_csr_bankarray_interface0_bank_bus_dat_w;
always @(*) begin
    builder_csr_bankarray_csrbank0_trigger_mem_value_re = 1'd0;
    builder_csr_bankarray_csrbank0_trigger_mem_value_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 3'd5))) begin
        builder_csr_bankarray_csrbank0_trigger_mem_value_re = builder_csr_bankarray_interface0_bank_bus_we;
        builder_csr_bankarray_csrbank0_trigger_mem_value_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank0_trigger_mem_full_r = builder_csr_bankarray_interface0_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank0_trigger_mem_full_re = 1'd0;
    builder_csr_bankarray_csrbank0_trigger_mem_full_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 3'd6))) begin
        builder_csr_bankarray_csrbank0_trigger_mem_full_re = builder_csr_bankarray_interface0_bank_bus_we;
        builder_csr_bankarray_csrbank0_trigger_mem_full_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank0_subsampler_value_r = builder_csr_bankarray_interface0_bank_bus_dat_w[15:0];
always @(*) begin
    builder_csr_bankarray_csrbank0_subsampler_value_re = 1'd0;
    builder_csr_bankarray_csrbank0_subsampler_value_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 3'd7))) begin
        builder_csr_bankarray_csrbank0_subsampler_value_re = builder_csr_bankarray_interface0_bank_bus_we;
        builder_csr_bankarray_csrbank0_subsampler_value_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank0_storage_enable_r = builder_csr_bankarray_interface0_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank0_storage_enable_re = 1'd0;
    builder_csr_bankarray_csrbank0_storage_enable_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 4'd8))) begin
        builder_csr_bankarray_csrbank0_storage_enable_re = builder_csr_bankarray_interface0_bank_bus_we;
        builder_csr_bankarray_csrbank0_storage_enable_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank0_storage_done_r = builder_csr_bankarray_interface0_bank_bus_dat_w[0];
always @(*) begin
    builder_csr_bankarray_csrbank0_storage_done_re = 1'd0;
    builder_csr_bankarray_csrbank0_storage_done_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 4'd9))) begin
        builder_csr_bankarray_csrbank0_storage_done_re = builder_csr_bankarray_interface0_bank_bus_we;
        builder_csr_bankarray_csrbank0_storage_done_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank0_storage_length_r = builder_csr_bankarray_interface0_bank_bus_dat_w[11:0];
always @(*) begin
    builder_csr_bankarray_csrbank0_storage_length_re = 1'd0;
    builder_csr_bankarray_csrbank0_storage_length_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 4'd10))) begin
        builder_csr_bankarray_csrbank0_storage_length_re = builder_csr_bankarray_interface0_bank_bus_we;
        builder_csr_bankarray_csrbank0_storage_length_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank0_storage_offset_r = builder_csr_bankarray_interface0_bank_bus_dat_w[11:0];
always @(*) begin
    builder_csr_bankarray_csrbank0_storage_offset_re = 1'd0;
    builder_csr_bankarray_csrbank0_storage_offset_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 4'd11))) begin
        builder_csr_bankarray_csrbank0_storage_offset_re = builder_csr_bankarray_interface0_bank_bus_we;
        builder_csr_bankarray_csrbank0_storage_offset_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank0_storage_mem_level_r = builder_csr_bankarray_interface0_bank_bus_dat_w[11:0];
always @(*) begin
    builder_csr_bankarray_csrbank0_storage_mem_level_re = 1'd0;
    builder_csr_bankarray_csrbank0_storage_mem_level_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 4'd12))) begin
        builder_csr_bankarray_csrbank0_storage_mem_level_re = builder_csr_bankarray_interface0_bank_bus_we;
        builder_csr_bankarray_csrbank0_storage_mem_level_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank0_storage_mem_data_r = builder_csr_bankarray_interface0_bank_bus_dat_w;
always @(*) begin
    builder_csr_bankarray_csrbank0_storage_mem_data_re = 1'd0;
    builder_csr_bankarray_csrbank0_storage_mem_data_we = 1'd0;
    if ((builder_csr_bankarray_csrbank0_sel & (builder_csr_bankarray_interface0_bank_bus_adr[8:0] == 4'd13))) begin
        builder_csr_bankarray_csrbank0_storage_mem_data_re = builder_csr_bankarray_interface0_bank_bus_we;
        builder_csr_bankarray_csrbank0_storage_mem_data_we = builder_csr_bankarray_interface0_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank0_mux_value_w = main_analyzer_mux_value_storage;
assign builder_csr_bankarray_csrbank0_trigger_enable_w = main_analyzer_trigger_enable_storage;
assign builder_csr_bankarray_csrbank0_trigger_done_w = main_analyzer_trigger_done_status;
assign main_analyzer_trigger_done_rd_stb = builder_csr_bankarray_csrbank0_trigger_done_we;
assign builder_csr_bankarray_csrbank0_trigger_mem_mask_w = main_analyzer_trigger_mem_mask_storage;
assign builder_csr_bankarray_csrbank0_trigger_mem_value_w = main_analyzer_trigger_mem_value_storage;
assign builder_csr_bankarray_csrbank0_trigger_mem_full_w = main_analyzer_trigger_mem_full_status;
assign main_analyzer_trigger_mem_full_rd_stb = builder_csr_bankarray_csrbank0_trigger_mem_full_we;
assign builder_csr_bankarray_csrbank0_subsampler_value_w = main_analyzer_subsampler_value_storage;
assign builder_csr_bankarray_csrbank0_storage_enable_w = main_analyzer_storage_enable_storage;
assign builder_csr_bankarray_csrbank0_storage_done_w = main_analyzer_storage_done_status;
assign main_analyzer_storage_done_rd_stb = builder_csr_bankarray_csrbank0_storage_done_we;
assign builder_csr_bankarray_csrbank0_storage_length_w = main_analyzer_storage_length_storage;
assign builder_csr_bankarray_csrbank0_storage_offset_w = main_analyzer_storage_offset_storage;
assign builder_csr_bankarray_csrbank0_storage_mem_level_w = main_analyzer_storage_mem_level_status;
assign main_analyzer_storage_mem_level_rd_stb = builder_csr_bankarray_csrbank0_storage_mem_level_we;
assign builder_csr_bankarray_csrbank0_storage_mem_data_w = main_analyzer_storage_mem_data_status;
assign main_analyzer_storage_mem_data_rd_stb = builder_csr_bankarray_csrbank0_storage_mem_data_we;
assign builder_csr_bankarray_csrbank1_sel = (builder_csr_bankarray_interface1_bank_bus_adr[13:9] == 1'd1);
assign builder_csr_bankarray_csrbank1_reset_r = builder_csr_bankarray_interface1_bank_bus_dat_w[1:0];
always @(*) begin
    builder_csr_bankarray_csrbank1_reset_re = 1'd0;
    builder_csr_bankarray_csrbank1_reset_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 1'd0))) begin
        builder_csr_bankarray_csrbank1_reset_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_reset_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_scratch_r = builder_csr_bankarray_interface1_bank_bus_dat_w;
always @(*) begin
    builder_csr_bankarray_csrbank1_scratch_re = 1'd0;
    builder_csr_bankarray_csrbank1_scratch_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 1'd1))) begin
        builder_csr_bankarray_csrbank1_scratch_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_scratch_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
assign builder_csr_bankarray_csrbank1_bus_errors_r = builder_csr_bankarray_interface1_bank_bus_dat_w;
always @(*) begin
    builder_csr_bankarray_csrbank1_bus_errors_re = 1'd0;
    builder_csr_bankarray_csrbank1_bus_errors_we = 1'd0;
    if ((builder_csr_bankarray_csrbank1_sel & (builder_csr_bankarray_interface1_bank_bus_adr[8:0] == 2'd2))) begin
        builder_csr_bankarray_csrbank1_bus_errors_re = builder_csr_bankarray_interface1_bank_bus_we;
        builder_csr_bankarray_csrbank1_bus_errors_we = builder_csr_bankarray_interface1_bank_bus_re;
    end
end
always @(*) begin
    main_soc_rst = 1'd0;
    if (main_reset_wr_stb) begin
        main_soc_rst = main_reset_storage[0];
    end
end
assign main_cpu_rst = main_reset_storage[1];
assign builder_csr_bankarray_csrbank1_reset_w = main_reset_storage;
assign builder_csr_bankarray_csrbank1_scratch_w = main_scratch_storage;
assign builder_csr_bankarray_csrbank1_bus_errors_w = main_bus_errors_status;
assign main_bus_errors_rd_stb = builder_csr_bankarray_csrbank1_bus_errors_we;
assign builder_csr_bankarray_sel = (builder_csr_bankarray_sram_bus_adr[13:9] == 2'd2);
always @(*) begin
    builder_csr_bankarray_sram_bus_dat_r = 32'd0;
    if (builder_csr_bankarray_sel_r) begin
        builder_csr_bankarray_sram_bus_dat_r = builder_csr_bankarray_dat_r;
    end
end
assign builder_csr_bankarray_adr = builder_csr_bankarray_sram_bus_adr[4:0];
assign builder_csr_interconnect_adr = builder_interface1_adr;
assign builder_csr_interconnect_re = builder_interface1_re;
assign builder_csr_interconnect_we = builder_interface1_we;
assign builder_csr_interconnect_dat_w = builder_interface1_dat_w;
assign builder_interface1_dat_r = builder_csr_interconnect_dat_r;
assign builder_csr_bankarray_interface0_bank_bus_adr = builder_csr_interconnect_adr;
assign builder_csr_bankarray_interface1_bank_bus_adr = builder_csr_interconnect_adr;
assign builder_csr_bankarray_sram_bus_adr = builder_csr_interconnect_adr;
assign builder_csr_bankarray_interface0_bank_bus_re = builder_csr_interconnect_re;
assign builder_csr_bankarray_interface1_bank_bus_re = builder_csr_interconnect_re;
assign builder_csr_bankarray_sram_bus_re = builder_csr_interconnect_re;
assign builder_csr_bankarray_interface0_bank_bus_we = builder_csr_interconnect_we;
assign builder_csr_bankarray_interface1_bank_bus_we = builder_csr_interconnect_we;
assign builder_csr_bankarray_sram_bus_we = builder_csr_interconnect_we;
assign builder_csr_bankarray_interface0_bank_bus_dat_w = builder_csr_interconnect_dat_w;
assign builder_csr_bankarray_interface1_bank_bus_dat_w = builder_csr_interconnect_dat_w;
assign builder_csr_bankarray_sram_bus_dat_w = builder_csr_interconnect_dat_w;
assign builder_csr_interconnect_dat_r = ((builder_csr_bankarray_interface0_bank_bus_dat_r | builder_csr_bankarray_interface1_bank_bus_dat_r) | builder_csr_bankarray_sram_bus_dat_r);
always @(*) begin
    builder_rhs_self0 = 30'd0;
    case (builder_grant)
        default: begin
            builder_rhs_self0 = main_wishbone_adr;
        end
    endcase
end
always @(*) begin
    builder_rhs_self1 = 32'd0;
    case (builder_grant)
        default: begin
            builder_rhs_self1 = main_wishbone_dat_w;
        end
    endcase
end
always @(*) begin
    builder_rhs_self2 = 4'd0;
    case (builder_grant)
        default: begin
            builder_rhs_self2 = main_wishbone_sel;
        end
    endcase
end
always @(*) begin
    builder_rhs_self3 = 1'd0;
    case (builder_grant)
        default: begin
            builder_rhs_self3 = main_wishbone_cyc;
        end
    endcase
end
always @(*) begin
    builder_rhs_self4 = 1'd0;
    case (builder_grant)
        default: begin
            builder_rhs_self4 = main_wishbone_stb;
        end
    endcase
end
always @(*) begin
    builder_rhs_self5 = 1'd0;
    case (builder_grant)
        default: begin
            builder_rhs_self5 = main_wishbone_we;
        end
    endcase
end
always @(*) begin
    builder_rhs_self6 = 3'd0;
    case (builder_grant)
        default: begin
            builder_rhs_self6 = main_wishbone_cti;
        end
    endcase
end
always @(*) begin
    builder_rhs_self7 = 2'd0;
    case (builder_grant)
        default: begin
            builder_rhs_self7 = main_wishbone_bte;
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
assign main_rx_rx = builder_xilinxmultiregimpl01;
assign main_analyzer_mux_value = builder_xilinxmultiregimpl11;
assign main_analyzer_trigger_enable = builder_xilinxmultiregimpl21;
assign main_analyzer_trigger_done_status = builder_xilinxmultiregimpl31;
assign main_analyzer_trigger_mem_produce_rdomain = builder_xilinxmultiregimpl41;
assign main_analyzer_trigger_mem_consume_wdomain = builder_xilinxmultiregimpl51;
assign main_analyzer_subsampler_value = builder_xilinxmultiregimpl61;
assign main_analyzer_storage_enable = builder_xilinxmultiregimpl71;
assign main_analyzer_storage_length = builder_xilinxmultiregimpl81;
assign main_analyzer_storage_offset = builder_xilinxmultiregimpl91;
assign main_analyzer_storage_done_status = builder_xilinxmultiregimpl101;
assign main_analyzer_storage_mem_level_status = builder_xilinxmultiregimpl111;
assign main_analyzer_storage_cdc_produce_rdomain = builder_xilinxmultiregimpl121;
assign main_analyzer_storage_cdc_consume_wdomain = builder_xilinxmultiregimpl131;
assign main_analyzer_storage_flush_read_sys = builder_xilinxmultiregimpl141;



always @(posedge scope_clk) begin
    main_analyzer_trigger_enable_d <= main_analyzer_trigger_enable;
    main_analyzer_trigger_sink_d_valid <= main_analyzer_trigger_sink_sink_valid;
    main_analyzer_trigger_sink_d_payload_data <= main_analyzer_trigger_sink_sink_payload_data;
    if (((~main_analyzer_trigger_enable) & main_analyzer_trigger_enable_d)) begin
        main_analyzer_trigger_flushing <= 1'd1;
    end else begin
        if ((~main_analyzer_trigger_mem_source_valid)) begin
            main_analyzer_trigger_flushing <= 1'd0;
        end
    end
    if ((main_analyzer_trigger_mem_re | (~main_analyzer_trigger_mem_readable))) begin
        main_analyzer_trigger_mem_dout <= main_analyzer_trigger_mem_asyncfifo_dout;
        main_analyzer_trigger_mem_readable <= main_analyzer_trigger_mem_asyncfifo_readable;
    end
    main_analyzer_trigger_mem_graycounter1_q_binary <= main_analyzer_trigger_mem_graycounter1_q_next_binary;
    main_analyzer_trigger_mem_graycounter1_q <= main_analyzer_trigger_mem_graycounter1_q_next;
    if (main_analyzer_subsampler_source_ready) begin
        if (main_analyzer_subsampler_done) begin
            main_analyzer_subsampler_counter <= 1'd0;
        end else begin
            if (main_analyzer_subsampler_sink_valid) begin
                main_analyzer_subsampler_counter <= (main_analyzer_subsampler_counter + 1'd1);
            end
        end
    end
    main_analyzer_storage_enable_d <= main_analyzer_storage_enable;
    if (main_analyzer_storage_mem_syncfifo_re) begin
        main_analyzer_storage_mem_readable <= 1'd1;
    end else begin
        if (main_analyzer_storage_mem_re) begin
            main_analyzer_storage_mem_readable <= 1'd0;
        end
    end
    if (((main_analyzer_storage_mem_syncfifo_we & main_analyzer_storage_mem_syncfifo_writable) & (~main_analyzer_storage_mem_replace))) begin
        main_analyzer_storage_mem_produce <= (main_analyzer_storage_mem_produce + 1'd1);
    end
    if (main_analyzer_storage_mem_do_read) begin
        main_analyzer_storage_mem_consume <= (main_analyzer_storage_mem_consume + 1'd1);
    end
    if (((main_analyzer_storage_mem_syncfifo_we & main_analyzer_storage_mem_syncfifo_writable) & (~main_analyzer_storage_mem_replace))) begin
        if ((~main_analyzer_storage_mem_do_read)) begin
            main_analyzer_storage_mem_level0 <= (main_analyzer_storage_mem_level0 + 1'd1);
        end
    end else begin
        if (main_analyzer_storage_mem_do_read) begin
            main_analyzer_storage_mem_level0 <= (main_analyzer_storage_mem_level0 - 1'd1);
        end
    end
    main_analyzer_storage_cdc_graycounter0_q_binary <= main_analyzer_storage_cdc_graycounter0_q_next_binary;
    main_analyzer_storage_cdc_graycounter0_q <= main_analyzer_storage_cdc_graycounter0_q_next;
    if (main_analyzer_storage_wait) begin
        if ((~main_analyzer_storage_done1)) begin
            main_analyzer_storage_count <= (main_analyzer_storage_count - 1'd1);
        end
    end else begin
        main_analyzer_storage_count <= 12'h800;
    end
    builder_litescopeanalyzer_state <= builder_litescopeanalyzer_next_state;
    if (scope_rst) begin
        main_analyzer_trigger_enable_d <= 1'd0;
        main_analyzer_trigger_mem_readable <= 1'd0;
        main_analyzer_trigger_mem_graycounter1_q <= 5'd0;
        main_analyzer_trigger_mem_graycounter1_q_binary <= 5'd0;
        main_analyzer_trigger_sink_d_valid <= 1'd0;
        main_analyzer_trigger_flushing <= 1'd0;
        main_analyzer_subsampler_counter <= 16'd0;
        main_analyzer_storage_enable_d <= 1'd0;
        main_analyzer_storage_mem_readable <= 1'd0;
        main_analyzer_storage_mem_level0 <= 12'd0;
        main_analyzer_storage_mem_produce <= 11'd0;
        main_analyzer_storage_mem_consume <= 11'd0;
        main_analyzer_storage_cdc_graycounter0_q <= 3'd0;
        main_analyzer_storage_cdc_graycounter0_q_binary <= 3'd0;
        main_analyzer_storage_count <= 12'h800;
        builder_litescopeanalyzer_state <= 2'd0;
    end
    builder_xilinxmultiregimpl10 <= main_analyzer_mux_value_storage;
    builder_xilinxmultiregimpl11 <= builder_xilinxmultiregimpl10;
    builder_xilinxmultiregimpl20 <= main_analyzer_trigger_enable_storage;
    builder_xilinxmultiregimpl21 <= builder_xilinxmultiregimpl20;
    builder_xilinxmultiregimpl40 <= main_analyzer_trigger_mem_graycounter0_q;
    builder_xilinxmultiregimpl41 <= builder_xilinxmultiregimpl40;
    builder_xilinxmultiregimpl60 <= main_analyzer_subsampler_value_storage;
    builder_xilinxmultiregimpl61 <= builder_xilinxmultiregimpl60;
    builder_xilinxmultiregimpl70 <= main_analyzer_storage_enable_storage;
    builder_xilinxmultiregimpl71 <= builder_xilinxmultiregimpl70;
    builder_xilinxmultiregimpl80 <= main_analyzer_storage_length_storage;
    builder_xilinxmultiregimpl81 <= builder_xilinxmultiregimpl80;
    builder_xilinxmultiregimpl90 <= main_analyzer_storage_offset_storage;
    builder_xilinxmultiregimpl91 <= builder_xilinxmultiregimpl90;
    builder_xilinxmultiregimpl130 <= main_analyzer_storage_cdc_graycounter1_q;
    builder_xilinxmultiregimpl131 <= builder_xilinxmultiregimpl130;
end

always @(posedge sys_clk) begin
    builder_slave_sel_r <= builder_slave_sel;
    if (builder_wait) begin
        if ((~builder_done)) begin
            builder_count <= (builder_count - 1'd1);
        end
    end else begin
        builder_count <= 20'd1000000;
    end
    if ((main_bus_errors != 32'hffffffff)) begin
        if (main_bus_error) begin
            main_bus_errors <= (main_bus_errors + 1'd1);
        end
    end
    {main_tx_tick, main_tx_phase} <= 23'd4947802;
    if (main_tx_enable) begin
        {main_tx_tick, main_tx_phase} <= (main_tx_phase + 23'd4947802);
    end
    builder_uartbone_rs232phytx_state <= builder_uartbone_rs232phytx_next_state;
    if (main_tx_count_rs232phytx_next_value_ce0) begin
        main_tx_count <= main_tx_count_rs232phytx_next_value0;
    end
    if (main_dbg_serial_tx_rs232phytx_next_value_ce1) begin
        dbg_serial_tx <= main_dbg_serial_tx_rs232phytx_next_value1;
    end
    if (main_tx_data_rs232phytx_next_value_ce2) begin
        main_tx_data <= main_tx_data_rs232phytx_next_value2;
    end
    main_rx_rx_d <= main_rx_rx;
    {main_rx_tick, main_rx_phase} <= 32'h80000000;
    if (main_rx_enable) begin
        {main_rx_tick, main_rx_phase} <= (main_rx_phase + 23'd4947802);
    end
    builder_uartbone_rs232phyrx_state <= builder_uartbone_rs232phyrx_next_state;
    if (main_rx_count_rs232phyrx_next_value_ce0) begin
        main_rx_count <= main_rx_count_rs232phyrx_next_value0;
    end
    if (main_rx_data_rs232phyrx_next_value_ce1) begin
        main_rx_data <= main_rx_data_rs232phyrx_next_value1;
    end
    builder_uartbone_state <= builder_uartbone_next_state;
    if (main_data_bytes_count_next_value_ce0) begin
        main_data_bytes_count <= main_data_bytes_count_next_value0;
    end
    if (main_addr_bytes_count_next_value_ce1) begin
        main_addr_bytes_count <= main_addr_bytes_count_next_value1;
    end
    if (main_words_count_next_value_ce2) begin
        main_words_count <= main_words_count_next_value2;
    end
    if (main_cmd_next_value_ce3) begin
        main_cmd <= main_cmd_next_value3;
    end
    if (main_length_next_value_ce4) begin
        main_length <= main_length_next_value4;
    end
    if (main_address_next_value_ce5) begin
        main_address <= main_address_next_value5;
    end
    if (main_incr_next_value_ce6) begin
        main_incr <= main_incr_next_value6;
    end
    if (main_data_next_value_ce7) begin
        main_data <= main_data_next_value7;
    end
    if (main_reset) begin
        main_incr <= 1'd0;
        builder_uartbone_state <= 3'd0;
    end
    if (main_wait) begin
        if ((~main_done)) begin
            main_count <= (main_count - 1'd1);
        end
    end else begin
        main_count <= 24'd10000000;
    end
    main_analyzer_trigger_mem_graycounter0_q_binary <= main_analyzer_trigger_mem_graycounter0_q_next_binary;
    main_analyzer_trigger_mem_graycounter0_q <= main_analyzer_trigger_mem_graycounter0_q_next;
    main_analyzer_storage_cdc_graycounter1_q_binary <= main_analyzer_storage_cdc_graycounter1_q_next_binary;
    main_analyzer_storage_cdc_graycounter1_q <= main_analyzer_storage_cdc_graycounter1_q_next;
    builder_wishbone2csr_state <= builder_wishbone2csr_next_state;
    builder_csr_bankarray_interface0_bank_bus_dat_r <= 1'd0;
    if (builder_csr_bankarray_csrbank0_sel) begin
        case (builder_csr_bankarray_interface0_bank_bus_adr[8:0])
            1'd0: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= builder_csr_bankarray_csrbank0_mux_value_w;
            end
            1'd1: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= builder_csr_bankarray_csrbank0_trigger_enable_w;
            end
            2'd2: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= builder_csr_bankarray_csrbank0_trigger_done_w;
            end
            2'd3: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= main_analyzer_trigger_mem_write_w;
            end
            3'd4: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= builder_csr_bankarray_csrbank0_trigger_mem_mask_w;
            end
            3'd5: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= builder_csr_bankarray_csrbank0_trigger_mem_value_w;
            end
            3'd6: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= builder_csr_bankarray_csrbank0_trigger_mem_full_w;
            end
            3'd7: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= builder_csr_bankarray_csrbank0_subsampler_value_w;
            end
            4'd8: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= builder_csr_bankarray_csrbank0_storage_enable_w;
            end
            4'd9: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= builder_csr_bankarray_csrbank0_storage_done_w;
            end
            4'd10: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= builder_csr_bankarray_csrbank0_storage_length_w;
            end
            4'd11: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= builder_csr_bankarray_csrbank0_storage_offset_w;
            end
            4'd12: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= builder_csr_bankarray_csrbank0_storage_mem_level_w;
            end
            4'd13: begin
                builder_csr_bankarray_interface0_bank_bus_dat_r <= builder_csr_bankarray_csrbank0_storage_mem_data_w;
            end
        endcase
    end
    if (builder_csr_bankarray_csrbank0_mux_value_re) begin
        main_analyzer_mux_value_storage <= builder_csr_bankarray_csrbank0_mux_value_r;
    end
    main_analyzer_mux_value_wr_stb <= builder_csr_bankarray_csrbank0_mux_value_re;
    if (builder_csr_bankarray_csrbank0_trigger_enable_re) begin
        main_analyzer_trigger_enable_storage <= builder_csr_bankarray_csrbank0_trigger_enable_r;
    end
    main_analyzer_trigger_enable_wr_stb <= builder_csr_bankarray_csrbank0_trigger_enable_re;
    main_analyzer_trigger_done_wr_stb <= builder_csr_bankarray_csrbank0_trigger_done_re;
    if (builder_csr_bankarray_csrbank0_trigger_mem_mask_re) begin
        main_analyzer_trigger_mem_mask_storage <= builder_csr_bankarray_csrbank0_trigger_mem_mask_r;
    end
    main_analyzer_trigger_mem_mask_wr_stb <= builder_csr_bankarray_csrbank0_trigger_mem_mask_re;
    if (builder_csr_bankarray_csrbank0_trigger_mem_value_re) begin
        main_analyzer_trigger_mem_value_storage <= builder_csr_bankarray_csrbank0_trigger_mem_value_r;
    end
    main_analyzer_trigger_mem_value_wr_stb <= builder_csr_bankarray_csrbank0_trigger_mem_value_re;
    main_analyzer_trigger_mem_full_wr_stb <= builder_csr_bankarray_csrbank0_trigger_mem_full_re;
    if (builder_csr_bankarray_csrbank0_subsampler_value_re) begin
        main_analyzer_subsampler_value_storage <= builder_csr_bankarray_csrbank0_subsampler_value_r;
    end
    main_analyzer_subsampler_value_wr_stb <= builder_csr_bankarray_csrbank0_subsampler_value_re;
    if (builder_csr_bankarray_csrbank0_storage_enable_re) begin
        main_analyzer_storage_enable_storage <= builder_csr_bankarray_csrbank0_storage_enable_r;
    end
    main_analyzer_storage_enable_wr_stb <= builder_csr_bankarray_csrbank0_storage_enable_re;
    main_analyzer_storage_done_wr_stb <= builder_csr_bankarray_csrbank0_storage_done_re;
    if (builder_csr_bankarray_csrbank0_storage_length_re) begin
        main_analyzer_storage_length_storage <= builder_csr_bankarray_csrbank0_storage_length_r;
    end
    main_analyzer_storage_length_wr_stb <= builder_csr_bankarray_csrbank0_storage_length_re;
    if (builder_csr_bankarray_csrbank0_storage_offset_re) begin
        main_analyzer_storage_offset_storage <= builder_csr_bankarray_csrbank0_storage_offset_r;
    end
    main_analyzer_storage_offset_wr_stb <= builder_csr_bankarray_csrbank0_storage_offset_re;
    main_analyzer_storage_mem_level_wr_stb <= builder_csr_bankarray_csrbank0_storage_mem_level_re;
    main_analyzer_storage_mem_data_wr_stb <= builder_csr_bankarray_csrbank0_storage_mem_data_re;
    builder_csr_bankarray_interface1_bank_bus_dat_r <= 1'd0;
    if (builder_csr_bankarray_csrbank1_sel) begin
        case (builder_csr_bankarray_interface1_bank_bus_adr[8:0])
            1'd0: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_reset_w;
            end
            1'd1: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_scratch_w;
            end
            2'd2: begin
                builder_csr_bankarray_interface1_bank_bus_dat_r <= builder_csr_bankarray_csrbank1_bus_errors_w;
            end
        endcase
    end
    if (builder_csr_bankarray_csrbank1_reset_re) begin
        main_reset_storage <= builder_csr_bankarray_csrbank1_reset_r;
    end
    main_reset_wr_stb <= builder_csr_bankarray_csrbank1_reset_re;
    if (builder_csr_bankarray_csrbank1_scratch_re) begin
        main_scratch_storage <= builder_csr_bankarray_csrbank1_scratch_r;
    end
    main_scratch_wr_stb <= builder_csr_bankarray_csrbank1_scratch_re;
    main_bus_errors_wr_stb <= builder_csr_bankarray_csrbank1_bus_errors_re;
    builder_csr_bankarray_sel_r <= builder_csr_bankarray_sel;
    if (sys_rst) begin
        main_reset_storage <= 2'd0;
        main_reset_wr_stb <= 1'd0;
        main_scratch_storage <= 32'd305419896;
        main_scratch_wr_stb <= 1'd0;
        main_bus_errors_wr_stb <= 1'd0;
        main_bus_errors <= 32'd0;
        dbg_serial_tx <= 1'd1;
        main_tx_tick <= 1'd0;
        main_rx_tick <= 1'd0;
        main_rx_rx_d <= 1'd0;
        main_incr <= 1'd0;
        main_count <= 24'd10000000;
        main_analyzer_mux_value_storage <= 1'd0;
        main_analyzer_mux_value_wr_stb <= 1'd0;
        main_analyzer_trigger_enable_storage <= 1'd0;
        main_analyzer_trigger_enable_wr_stb <= 1'd0;
        main_analyzer_trigger_done_wr_stb <= 1'd0;
        main_analyzer_trigger_mem_mask_storage <= 32'd0;
        main_analyzer_trigger_mem_mask_wr_stb <= 1'd0;
        main_analyzer_trigger_mem_value_storage <= 32'd0;
        main_analyzer_trigger_mem_value_wr_stb <= 1'd0;
        main_analyzer_trigger_mem_full_wr_stb <= 1'd0;
        main_analyzer_trigger_mem_graycounter0_q <= 5'd0;
        main_analyzer_trigger_mem_graycounter0_q_binary <= 5'd0;
        main_analyzer_subsampler_value_storage <= 16'd0;
        main_analyzer_subsampler_value_wr_stb <= 1'd0;
        main_analyzer_storage_enable_storage <= 1'd0;
        main_analyzer_storage_enable_wr_stb <= 1'd0;
        main_analyzer_storage_done_wr_stb <= 1'd0;
        main_analyzer_storage_length_storage <= 12'd0;
        main_analyzer_storage_length_wr_stb <= 1'd0;
        main_analyzer_storage_offset_storage <= 12'd0;
        main_analyzer_storage_offset_wr_stb <= 1'd0;
        main_analyzer_storage_mem_level_wr_stb <= 1'd0;
        main_analyzer_storage_mem_data_wr_stb <= 1'd0;
        main_analyzer_storage_cdc_graycounter1_q <= 3'd0;
        main_analyzer_storage_cdc_graycounter1_q_binary <= 3'd0;
        builder_slave_sel_r <= 1'd0;
        builder_count <= 20'd1000000;
        builder_csr_bankarray_sel_r <= 1'd0;
        builder_uartbone_rs232phytx_state <= 1'd0;
        builder_uartbone_rs232phyrx_state <= 1'd0;
        builder_uartbone_state <= 3'd0;
        builder_wishbone2csr_state <= 1'd0;
    end
    builder_xilinxmultiregimpl00 <= dbg_serial_rx;
    builder_xilinxmultiregimpl01 <= builder_xilinxmultiregimpl00;
    builder_xilinxmultiregimpl30 <= main_analyzer_trigger_done;
    builder_xilinxmultiregimpl31 <= builder_xilinxmultiregimpl30;
    builder_xilinxmultiregimpl50 <= main_analyzer_trigger_mem_graycounter1_q;
    builder_xilinxmultiregimpl51 <= builder_xilinxmultiregimpl50;
    builder_xilinxmultiregimpl100 <= main_analyzer_storage_done0;
    builder_xilinxmultiregimpl101 <= builder_xilinxmultiregimpl100;
    builder_xilinxmultiregimpl110 <= main_analyzer_storage_level;
    builder_xilinxmultiregimpl111 <= builder_xilinxmultiregimpl110;
    builder_xilinxmultiregimpl120 <= main_analyzer_storage_cdc_graycounter0_q;
    builder_xilinxmultiregimpl121 <= builder_xilinxmultiregimpl120;
    builder_xilinxmultiregimpl140 <= main_analyzer_storage_flush_read;
    builder_xilinxmultiregimpl141 <= builder_xilinxmultiregimpl140;
end



reg [7:0] mem[0:29];
initial begin
	$readmemh("scope_core_mem.init", mem);
end
reg [7:0] mem_dat0;
always @(posedge sys_clk) begin
	mem_dat0 <= mem[builder_csr_bankarray_adr];
end
assign builder_csr_bankarray_dat_r = mem_dat0;


reg [65:0] storage[0:15];
reg [65:0] storage_dat0;
reg [65:0] storage_dat1;
always @(posedge sys_clk) begin
	if (main_analyzer_trigger_mem_wrport_we)
		storage[main_analyzer_trigger_mem_wrport_adr] <= main_analyzer_trigger_mem_wrport_dat_w;
	storage_dat0 <= storage[main_analyzer_trigger_mem_wrport_adr];
end
always @(posedge scope_clk) begin
	storage_dat1 <= storage[main_analyzer_trigger_mem_rdport_adr];
end
assign main_analyzer_trigger_mem_wrport_dat_r = storage_dat0;
assign main_analyzer_trigger_mem_rdport_dat_r = storage_dat1;


reg [33:0] storage_1[0:2047];
reg [33:0] storage_1_dat0;
reg [33:0] storage_1_dat1;
always @(posedge scope_clk) begin
	if (main_analyzer_storage_mem_wrport_we)
		storage_1[main_analyzer_storage_mem_wrport_adr] <= main_analyzer_storage_mem_wrport_dat_w;
	storage_1_dat0 <= storage_1[main_analyzer_storage_mem_wrport_adr];
end
always @(posedge scope_clk) begin
	if (main_analyzer_storage_mem_rdport_re) begin
		storage_1_dat1 <= storage_1[main_analyzer_storage_mem_rdport_adr];
	end
end
assign main_analyzer_storage_mem_wrport_dat_r = storage_1_dat0;
assign main_analyzer_storage_mem_rdport_dat_r = storage_1_dat1;


reg [33:0] storage_2[0:3];
reg [33:0] storage_2_dat0;
reg [33:0] storage_2_dat1;
always @(posedge scope_clk) begin
	if (main_analyzer_storage_cdc_wrport_we)
		storage_2[main_analyzer_storage_cdc_wrport_adr] <= main_analyzer_storage_cdc_wrport_dat_w;
	storage_2_dat0 <= storage_2[main_analyzer_storage_cdc_wrport_adr];
end
always @(posedge sys_clk) begin
	storage_2_dat1 <= storage_2[main_analyzer_storage_cdc_rdport_adr];
end
assign main_analyzer_storage_cdc_wrport_dat_r = storage_2_dat0;
assign main_analyzer_storage_cdc_rdport_dat_r = storage_2_dat1;


endmodule

