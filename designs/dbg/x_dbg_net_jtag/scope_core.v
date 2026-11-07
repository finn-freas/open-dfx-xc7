
`timescale 1ns / 1ps


module scope_core (
    input  wire          dbg_clk,
    input  wire   [15:0] dbg_probe
);





reg           analyzer_mux_first = 1'd0;
reg           analyzer_mux_last = 1'd0;
wire   [15:0] analyzer_mux_payload_data;
reg           analyzer_mux_payload_hit = 1'd0;
reg           analyzer_mux_ready = 1'd0;
reg           analyzer_mux_source_first = 1'd0;
reg           analyzer_mux_source_last = 1'd0;
reg    [15:0] analyzer_mux_source_payload_data = 16'd0;
reg           analyzer_mux_source_payload_hit = 1'd0;
wire          analyzer_mux_source_ready;
reg           analyzer_mux_source_valid = 1'd0;
wire          analyzer_mux_valid;
wire          analyzer_mux_value;
reg           analyzer_mux_value_storage = 1'd0;
reg           analyzer_mux_value_wr_stb = 1'd0;
wire   [17:0] analyzer_storage_cdc_asyncfifo_din;
wire   [17:0] analyzer_storage_cdc_asyncfifo_dout;
wire          analyzer_storage_cdc_asyncfifo_re;
wire          analyzer_storage_cdc_asyncfifo_readable;
wire          analyzer_storage_cdc_asyncfifo_we;
wire          analyzer_storage_cdc_asyncfifo_writable;
wire    [2:0] analyzer_storage_cdc_consume_wdomain;
wire          analyzer_storage_cdc_fifo_in_first;
wire          analyzer_storage_cdc_fifo_in_last;
wire   [15:0] analyzer_storage_cdc_fifo_in_payload_data;
wire          analyzer_storage_cdc_fifo_out_first;
wire          analyzer_storage_cdc_fifo_out_last;
wire   [15:0] analyzer_storage_cdc_fifo_out_payload_data;
wire          analyzer_storage_cdc_graycounter0_ce;
(* dont_touch = "true" *)
reg     [2:0] analyzer_storage_cdc_graycounter0_q = 3'd0;
reg     [2:0] analyzer_storage_cdc_graycounter0_q_binary = 3'd0;
wire    [2:0] analyzer_storage_cdc_graycounter0_q_next;
reg     [2:0] analyzer_storage_cdc_graycounter0_q_next_binary = 3'd0;
wire          analyzer_storage_cdc_graycounter1_ce;
(* dont_touch = "true" *)
reg     [2:0] analyzer_storage_cdc_graycounter1_q = 3'd0;
reg     [2:0] analyzer_storage_cdc_graycounter1_q_binary = 3'd0;
wire    [2:0] analyzer_storage_cdc_graycounter1_q_next;
reg     [2:0] analyzer_storage_cdc_graycounter1_q_next_binary = 3'd0;
wire    [2:0] analyzer_storage_cdc_produce_rdomain;
wire    [1:0] analyzer_storage_cdc_rdport_adr;
wire   [17:0] analyzer_storage_cdc_rdport_dat_r;
reg           analyzer_storage_cdc_sink_first = 1'd0;
reg           analyzer_storage_cdc_sink_last = 1'd0;
reg    [15:0] analyzer_storage_cdc_sink_payload_data = 16'd0;
wire          analyzer_storage_cdc_sink_ready;
reg           analyzer_storage_cdc_sink_valid = 1'd0;
wire          analyzer_storage_cdc_source_first;
wire          analyzer_storage_cdc_source_last;
wire   [15:0] analyzer_storage_cdc_source_payload_data;
wire          analyzer_storage_cdc_source_ready;
wire          analyzer_storage_cdc_source_valid;
wire    [1:0] analyzer_storage_cdc_wrport_adr;
wire   [17:0] analyzer_storage_cdc_wrport_dat_r;
wire   [17:0] analyzer_storage_cdc_wrport_dat_w;
wire          analyzer_storage_cdc_wrport_we;
reg    [10:0] analyzer_storage_count = 11'h400;
reg           analyzer_storage_done0 = 1'd0;
wire          analyzer_storage_done1;
wire          analyzer_storage_done_rd_stb;
wire          analyzer_storage_done_status;
reg           analyzer_storage_done_wr_stb = 1'd0;
wire          analyzer_storage_enable;
reg           analyzer_storage_enable_d = 1'd0;
reg           analyzer_storage_enable_storage = 1'd0;
reg           analyzer_storage_enable_wr_stb = 1'd0;
reg           analyzer_storage_flush = 1'd0;
reg           analyzer_storage_flush_read = 1'd0;
wire          analyzer_storage_flush_read_sys;
wire   [10:0] analyzer_storage_length;
reg    [10:0] analyzer_storage_length_storage = 11'd0;
reg           analyzer_storage_length_wr_stb = 1'd0;
wire   [10:0] analyzer_storage_level;
reg     [9:0] analyzer_storage_mem_consume = 10'd0;
wire          analyzer_storage_mem_data_rd_stb;
wire   [15:0] analyzer_storage_mem_data_status;
reg           analyzer_storage_mem_data_wr_stb = 1'd0;
wire          analyzer_storage_mem_do_read;
wire          analyzer_storage_mem_fifo_in_first;
wire          analyzer_storage_mem_fifo_in_last;
wire   [15:0] analyzer_storage_mem_fifo_in_payload_data;
wire          analyzer_storage_mem_fifo_out_first;
wire          analyzer_storage_mem_fifo_out_last;
wire   [15:0] analyzer_storage_mem_fifo_out_payload_data;
reg    [10:0] analyzer_storage_mem_level0 = 11'd0;
wire   [10:0] analyzer_storage_mem_level1;
wire          analyzer_storage_mem_level_rd_stb;
wire   [10:0] analyzer_storage_mem_level_status;
reg           analyzer_storage_mem_level_wr_stb = 1'd0;
reg     [9:0] analyzer_storage_mem_produce = 10'd0;
wire    [9:0] analyzer_storage_mem_rdport_adr;
wire   [17:0] analyzer_storage_mem_rdport_dat_r;
wire          analyzer_storage_mem_rdport_re;
wire          analyzer_storage_mem_re;
reg           analyzer_storage_mem_readable = 1'd0;
reg           analyzer_storage_mem_replace = 1'd0;
reg           analyzer_storage_mem_sink_first = 1'd0;
reg           analyzer_storage_mem_sink_last = 1'd0;
reg    [15:0] analyzer_storage_mem_sink_payload_data = 16'd0;
wire          analyzer_storage_mem_sink_ready;
reg           analyzer_storage_mem_sink_valid = 1'd0;
wire          analyzer_storage_mem_source_first;
wire          analyzer_storage_mem_source_last;
wire   [15:0] analyzer_storage_mem_source_payload_data;
reg           analyzer_storage_mem_source_ready = 1'd0;
wire          analyzer_storage_mem_source_valid;
wire   [17:0] analyzer_storage_mem_syncfifo_din;
wire   [17:0] analyzer_storage_mem_syncfifo_dout;
wire          analyzer_storage_mem_syncfifo_re;
wire          analyzer_storage_mem_syncfifo_readable;
wire          analyzer_storage_mem_syncfifo_we;
wire          analyzer_storage_mem_syncfifo_writable;
reg     [9:0] analyzer_storage_mem_wrport_adr = 10'd0;
wire   [17:0] analyzer_storage_mem_wrport_dat_r;
wire   [17:0] analyzer_storage_mem_wrport_dat_w;
wire          analyzer_storage_mem_wrport_we;
wire   [10:0] analyzer_storage_offset;
reg    [10:0] analyzer_storage_offset_storage = 11'd0;
reg           analyzer_storage_offset_wr_stb = 1'd0;
reg           analyzer_storage_post_hit = 1'd0;
wire          analyzer_storage_read_source_first;
wire          analyzer_storage_read_source_last;
wire   [15:0] analyzer_storage_read_source_payload_data;
wire          analyzer_storage_read_source_ready;
wire          analyzer_storage_read_source_valid;
wire          analyzer_storage_sink_sink_first;
wire          analyzer_storage_sink_sink_last;
wire   [15:0] analyzer_storage_sink_sink_payload_data;
wire          analyzer_storage_sink_sink_payload_hit;
reg           analyzer_storage_sink_sink_ready = 1'd0;
wire          analyzer_storage_sink_sink_valid;
reg           analyzer_storage_wait = 1'd0;
reg    [15:0] analyzer_subsampler_counter = 16'd0;
wire          analyzer_subsampler_done;
wire          analyzer_subsampler_sink_first;
wire          analyzer_subsampler_sink_last;
wire   [15:0] analyzer_subsampler_sink_payload_data;
wire          analyzer_subsampler_sink_payload_hit;
wire          analyzer_subsampler_sink_ready;
wire          analyzer_subsampler_sink_valid;
wire          analyzer_subsampler_source_first;
wire          analyzer_subsampler_source_last;
wire   [15:0] analyzer_subsampler_source_payload_data;
wire          analyzer_subsampler_source_payload_hit;
wire          analyzer_subsampler_source_ready;
wire          analyzer_subsampler_source_valid;
wire   [15:0] analyzer_subsampler_value;
reg    [15:0] analyzer_subsampler_value_storage = 16'd0;
reg           analyzer_subsampler_value_wr_stb = 1'd0;
wire          analyzer_trigger_done;
wire          analyzer_trigger_done_rd_stb;
wire          analyzer_trigger_done_status;
reg           analyzer_trigger_done_wr_stb = 1'd0;
wire          analyzer_trigger_enable;
reg           analyzer_trigger_enable_d = 1'd0;
reg           analyzer_trigger_enable_storage = 1'd0;
reg           analyzer_trigger_enable_wr_stb = 1'd0;
reg           analyzer_trigger_flushing = 1'd0;
wire          analyzer_trigger_hit;
wire   [33:0] analyzer_trigger_mem_asyncfifo_din;
wire   [33:0] analyzer_trigger_mem_asyncfifo_dout;
wire          analyzer_trigger_mem_asyncfifo_re;
wire          analyzer_trigger_mem_asyncfifo_readable;
wire          analyzer_trigger_mem_asyncfifo_we;
wire          analyzer_trigger_mem_asyncfifo_writable;
wire    [4:0] analyzer_trigger_mem_consume_wdomain;
reg    [33:0] analyzer_trigger_mem_dout = 34'd0;
wire          analyzer_trigger_mem_fifo_in_first;
wire          analyzer_trigger_mem_fifo_in_last;
wire   [15:0] analyzer_trigger_mem_fifo_in_payload_mask;
wire   [15:0] analyzer_trigger_mem_fifo_in_payload_value;
wire          analyzer_trigger_mem_fifo_out_first;
wire          analyzer_trigger_mem_fifo_out_last;
wire   [15:0] analyzer_trigger_mem_fifo_out_payload_mask;
wire   [15:0] analyzer_trigger_mem_fifo_out_payload_value;
wire          analyzer_trigger_mem_full_rd_stb;
wire          analyzer_trigger_mem_full_status;
reg           analyzer_trigger_mem_full_wr_stb = 1'd0;
wire          analyzer_trigger_mem_graycounter0_ce;
(* dont_touch = "true" *)
reg     [4:0] analyzer_trigger_mem_graycounter0_q = 5'd0;
reg     [4:0] analyzer_trigger_mem_graycounter0_q_binary = 5'd0;
wire    [4:0] analyzer_trigger_mem_graycounter0_q_next;
reg     [4:0] analyzer_trigger_mem_graycounter0_q_next_binary = 5'd0;
wire          analyzer_trigger_mem_graycounter1_ce;
(* dont_touch = "true" *)
reg     [4:0] analyzer_trigger_mem_graycounter1_q = 5'd0;
reg     [4:0] analyzer_trigger_mem_graycounter1_q_binary = 5'd0;
wire    [4:0] analyzer_trigger_mem_graycounter1_q_next;
reg     [4:0] analyzer_trigger_mem_graycounter1_q_next_binary = 5'd0;
reg    [15:0] analyzer_trigger_mem_mask_storage = 16'd0;
reg           analyzer_trigger_mem_mask_wr_stb = 1'd0;
wire    [4:0] analyzer_trigger_mem_produce_rdomain;
wire    [3:0] analyzer_trigger_mem_rdport_adr;
wire   [33:0] analyzer_trigger_mem_rdport_dat_r;
wire          analyzer_trigger_mem_re;
reg           analyzer_trigger_mem_readable = 1'd0;
reg           analyzer_trigger_mem_sink_first = 1'd0;
reg           analyzer_trigger_mem_sink_last = 1'd0;
wire   [15:0] analyzer_trigger_mem_sink_payload_mask;
wire   [15:0] analyzer_trigger_mem_sink_payload_value;
wire          analyzer_trigger_mem_sink_ready;
wire          analyzer_trigger_mem_sink_valid;
wire          analyzer_trigger_mem_source_first;
wire          analyzer_trigger_mem_source_last;
wire   [15:0] analyzer_trigger_mem_source_payload_mask;
wire   [15:0] analyzer_trigger_mem_source_payload_value;
wire          analyzer_trigger_mem_source_ready;
wire          analyzer_trigger_mem_source_valid;
reg    [15:0] analyzer_trigger_mem_value_storage = 16'd0;
reg           analyzer_trigger_mem_value_wr_stb = 1'd0;
wire          analyzer_trigger_mem_write_r;
reg           analyzer_trigger_mem_write_re = 1'd0;
reg           analyzer_trigger_mem_write_w = 1'd0;
reg           analyzer_trigger_mem_write_we = 1'd0;
wire    [3:0] analyzer_trigger_mem_wrport_adr;
wire   [33:0] analyzer_trigger_mem_wrport_dat_r;
wire   [33:0] analyzer_trigger_mem_wrport_dat_w;
wire          analyzer_trigger_mem_wrport_we;
reg           analyzer_trigger_sink_d_first = 1'd0;
reg           analyzer_trigger_sink_d_last = 1'd0;
reg    [15:0] analyzer_trigger_sink_d_payload_data = 16'd0;
reg           analyzer_trigger_sink_d_payload_hit = 1'd0;
reg           analyzer_trigger_sink_d_valid = 1'd0;
wire          analyzer_trigger_sink_sink_first;
wire          analyzer_trigger_sink_sink_last;
wire   [15:0] analyzer_trigger_sink_sink_payload_data;
wire          analyzer_trigger_sink_sink_payload_hit;
wire          analyzer_trigger_sink_sink_ready;
wire          analyzer_trigger_sink_sink_valid;
wire          analyzer_trigger_source_source_first;
wire          analyzer_trigger_source_source_last;
wire   [15:0] analyzer_trigger_source_source_payload_data;
reg           analyzer_trigger_source_source_payload_hit = 1'd0;
wire          analyzer_trigger_source_source_ready;
wire          analyzer_trigger_source_source_valid;
reg    [31:0] basiclowerer_self = 32'd0;
wire          bus_error;
reg    [31:0] bus_errors = 32'd0;
wire          bus_errors_rd_stb;
wire   [31:0] bus_errors_status;
reg           bus_errors_wr_stb = 1'd0;
reg    [19:0] count = 20'd1000000;
wire          cpu_rst;
wire    [4:0] csr_bankarray_adr;
wire          csr_bankarray_csrbank0_mux_value_r;
reg           csr_bankarray_csrbank0_mux_value_re = 1'd0;
wire          csr_bankarray_csrbank0_mux_value_w;
reg           csr_bankarray_csrbank0_mux_value_we = 1'd0;
wire          csr_bankarray_csrbank0_sel;
wire          csr_bankarray_csrbank0_storage_done_r;
reg           csr_bankarray_csrbank0_storage_done_re = 1'd0;
wire          csr_bankarray_csrbank0_storage_done_w;
reg           csr_bankarray_csrbank0_storage_done_we = 1'd0;
wire          csr_bankarray_csrbank0_storage_enable_r;
reg           csr_bankarray_csrbank0_storage_enable_re = 1'd0;
wire          csr_bankarray_csrbank0_storage_enable_w;
reg           csr_bankarray_csrbank0_storage_enable_we = 1'd0;
wire   [10:0] csr_bankarray_csrbank0_storage_length_r;
reg           csr_bankarray_csrbank0_storage_length_re = 1'd0;
wire   [10:0] csr_bankarray_csrbank0_storage_length_w;
reg           csr_bankarray_csrbank0_storage_length_we = 1'd0;
wire   [15:0] csr_bankarray_csrbank0_storage_mem_data_r;
reg           csr_bankarray_csrbank0_storage_mem_data_re = 1'd0;
wire   [15:0] csr_bankarray_csrbank0_storage_mem_data_w;
reg           csr_bankarray_csrbank0_storage_mem_data_we = 1'd0;
wire   [10:0] csr_bankarray_csrbank0_storage_mem_level_r;
reg           csr_bankarray_csrbank0_storage_mem_level_re = 1'd0;
wire   [10:0] csr_bankarray_csrbank0_storage_mem_level_w;
reg           csr_bankarray_csrbank0_storage_mem_level_we = 1'd0;
wire   [10:0] csr_bankarray_csrbank0_storage_offset_r;
reg           csr_bankarray_csrbank0_storage_offset_re = 1'd0;
wire   [10:0] csr_bankarray_csrbank0_storage_offset_w;
reg           csr_bankarray_csrbank0_storage_offset_we = 1'd0;
wire   [15:0] csr_bankarray_csrbank0_subsampler_value_r;
reg           csr_bankarray_csrbank0_subsampler_value_re = 1'd0;
wire   [15:0] csr_bankarray_csrbank0_subsampler_value_w;
reg           csr_bankarray_csrbank0_subsampler_value_we = 1'd0;
wire          csr_bankarray_csrbank0_trigger_done_r;
reg           csr_bankarray_csrbank0_trigger_done_re = 1'd0;
wire          csr_bankarray_csrbank0_trigger_done_w;
reg           csr_bankarray_csrbank0_trigger_done_we = 1'd0;
wire          csr_bankarray_csrbank0_trigger_enable_r;
reg           csr_bankarray_csrbank0_trigger_enable_re = 1'd0;
wire          csr_bankarray_csrbank0_trigger_enable_w;
reg           csr_bankarray_csrbank0_trigger_enable_we = 1'd0;
wire          csr_bankarray_csrbank0_trigger_mem_full_r;
reg           csr_bankarray_csrbank0_trigger_mem_full_re = 1'd0;
wire          csr_bankarray_csrbank0_trigger_mem_full_w;
reg           csr_bankarray_csrbank0_trigger_mem_full_we = 1'd0;
wire   [15:0] csr_bankarray_csrbank0_trigger_mem_mask_r;
reg           csr_bankarray_csrbank0_trigger_mem_mask_re = 1'd0;
wire   [15:0] csr_bankarray_csrbank0_trigger_mem_mask_w;
reg           csr_bankarray_csrbank0_trigger_mem_mask_we = 1'd0;
wire   [15:0] csr_bankarray_csrbank0_trigger_mem_value_r;
reg           csr_bankarray_csrbank0_trigger_mem_value_re = 1'd0;
wire   [15:0] csr_bankarray_csrbank0_trigger_mem_value_w;
reg           csr_bankarray_csrbank0_trigger_mem_value_we = 1'd0;
wire   [31:0] csr_bankarray_csrbank1_bus_errors_r;
reg           csr_bankarray_csrbank1_bus_errors_re = 1'd0;
wire   [31:0] csr_bankarray_csrbank1_bus_errors_w;
reg           csr_bankarray_csrbank1_bus_errors_we = 1'd0;
wire    [1:0] csr_bankarray_csrbank1_reset_r;
reg           csr_bankarray_csrbank1_reset_re = 1'd0;
wire    [1:0] csr_bankarray_csrbank1_reset_w;
reg           csr_bankarray_csrbank1_reset_we = 1'd0;
wire   [31:0] csr_bankarray_csrbank1_scratch_r;
reg           csr_bankarray_csrbank1_scratch_re = 1'd0;
wire   [31:0] csr_bankarray_csrbank1_scratch_w;
reg           csr_bankarray_csrbank1_scratch_we = 1'd0;
wire          csr_bankarray_csrbank1_sel;
wire    [7:0] csr_bankarray_dat_r;
wire   [13:0] csr_bankarray_interface0_bank_bus_adr;
reg    [31:0] csr_bankarray_interface0_bank_bus_dat_r = 32'd0;
wire   [31:0] csr_bankarray_interface0_bank_bus_dat_w;
wire          csr_bankarray_interface0_bank_bus_re;
wire          csr_bankarray_interface0_bank_bus_we;
wire   [13:0] csr_bankarray_interface1_bank_bus_adr;
reg    [31:0] csr_bankarray_interface1_bank_bus_dat_r = 32'd0;
wire   [31:0] csr_bankarray_interface1_bank_bus_dat_w;
wire          csr_bankarray_interface1_bank_bus_re;
wire          csr_bankarray_interface1_bank_bus_we;
wire          csr_bankarray_sel;
reg           csr_bankarray_sel_r = 1'd0;
wire   [13:0] csr_bankarray_sram_bus_adr;
reg    [31:0] csr_bankarray_sram_bus_dat_r = 32'd0;
wire   [31:0] csr_bankarray_sram_bus_dat_w;
wire          csr_bankarray_sram_bus_re;
wire          csr_bankarray_sram_bus_we;
reg           csr_data_width = 1'd0;
wire   [13:0] csr_interconnect_adr;
wire   [31:0] csr_interconnect_dat_r;
wire   [31:0] csr_interconnect_dat_w;
wire          csr_interconnect_re;
wire          csr_interconnect_we;
wire          done;
wire   [15:0] dq;
reg           error = 1'd0;
wire          from242_clk;
wire          from242_rst;
wire          from91_clk;
wire          from91_rst;
wire          grant;
reg           interface0_ack = 1'd0;
wire   [29:0] interface0_adr;
wire    [1:0] interface0_bte;
wire    [2:0] interface0_cti;
wire          interface0_cyc;
reg    [31:0] interface0_dat_r = 32'd0;
wire   [31:0] interface0_dat_w;
reg           interface0_err = 1'd0;
wire    [3:0] interface0_sel;
wire          interface0_stb;
wire          interface0_we;
reg    [13:0] interface1_adr = 14'd0;
wire   [31:0] interface1_dat_r;
reg    [31:0] interface1_dat_w = 32'd0;
reg           interface1_re = 1'd0;
reg           interface1_we = 1'd0;
wire          jtag_clk;
wire          jtag_rst;
reg     [1:0] jtagbone_addr_bytes_count = 2'd0;
reg     [1:0] jtagbone_addr_bytes_count_resetinserter_next_value1 = 2'd0;
reg           jtagbone_addr_bytes_count_resetinserter_next_value_ce1 = 1'd0;
reg    [31:0] jtagbone_address = 32'd0;
reg    [31:0] jtagbone_address_resetinserter_next_value5 = 32'd0;
reg           jtagbone_address_resetinserter_next_value_ce5 = 1'd0;
reg     [7:0] jtagbone_cmd = 8'd0;
reg     [7:0] jtagbone_cmd_resetinserter_next_value3 = 8'd0;
reg           jtagbone_cmd_resetinserter_next_value_ce3 = 1'd0;
reg    [23:0] jtagbone_count = 24'd10000000;
reg    [31:0] jtagbone_data = 32'd0;
reg     [1:0] jtagbone_data_bytes_count = 2'd0;
reg     [1:0] jtagbone_data_bytes_count_resetinserter_next_value0 = 2'd0;
reg           jtagbone_data_bytes_count_resetinserter_next_value_ce0 = 1'd0;
reg    [31:0] jtagbone_data_resetinserter_next_value7 = 32'd0;
reg           jtagbone_data_resetinserter_next_value_ce7 = 1'd0;
wire          jtagbone_done;
reg           jtagbone_incr = 1'd0;
reg           jtagbone_incr_resetinserter_next_value6 = 1'd0;
reg           jtagbone_incr_resetinserter_next_value_ce6 = 1'd0;
reg           jtagbone_is_ongoing = 1'd0;
reg     [7:0] jtagbone_length = 8'd0;
reg     [7:0] jtagbone_length_resetinserter_next_value4 = 8'd0;
reg           jtagbone_length_resetinserter_next_value_ce4 = 1'd0;
reg     [2:0] jtagbone_phy_count = 3'd0;
reg     [2:0] jtagbone_phy_count_jtagphy_next_value2 = 3'd0;
reg           jtagbone_phy_count_jtagphy_next_value_ce2 = 1'd0;
reg     [7:0] jtagbone_phy_data = 8'd0;
reg     [7:0] jtagbone_phy_data_jtagphy_next_value1 = 8'd0;
reg           jtagbone_phy_data_jtagphy_next_value_ce1 = 1'd0;
wire          jtagbone_phy_fsm_reset;
wire          jtagbone_phy_jtag_capture;
wire          jtagbone_phy_jtag_reset;
wire          jtagbone_phy_jtag_sel;
wire          jtagbone_phy_jtag_shift;
wire          jtagbone_phy_jtag_tck;
wire          jtagbone_phy_jtag_tdi;
reg           jtagbone_phy_jtag_tdo = 1'd0;
wire          jtagbone_phy_jtag_tms;
wire          jtagbone_phy_jtag_update;
reg           jtagbone_phy_ready = 1'd0;
wire          jtagbone_phy_rx_cdc_cd_rst;
wire    [9:0] jtagbone_phy_rx_cdc_cdc_asyncfifo_din;
wire    [9:0] jtagbone_phy_rx_cdc_cdc_asyncfifo_dout;
wire          jtagbone_phy_rx_cdc_cdc_asyncfifo_re;
wire          jtagbone_phy_rx_cdc_cdc_asyncfifo_readable;
wire          jtagbone_phy_rx_cdc_cdc_asyncfifo_we;
wire          jtagbone_phy_rx_cdc_cdc_asyncfifo_writable;
wire    [2:0] jtagbone_phy_rx_cdc_cdc_consume_wdomain;
wire          jtagbone_phy_rx_cdc_cdc_fifo_in_first;
wire          jtagbone_phy_rx_cdc_cdc_fifo_in_last;
wire    [7:0] jtagbone_phy_rx_cdc_cdc_fifo_in_payload_data;
wire          jtagbone_phy_rx_cdc_cdc_fifo_out_first;
wire          jtagbone_phy_rx_cdc_cdc_fifo_out_last;
wire    [7:0] jtagbone_phy_rx_cdc_cdc_fifo_out_payload_data;
wire          jtagbone_phy_rx_cdc_cdc_graycounter0_ce;
(* dont_touch = "true" *)
reg     [2:0] jtagbone_phy_rx_cdc_cdc_graycounter0_q = 3'd0;
reg     [2:0] jtagbone_phy_rx_cdc_cdc_graycounter0_q_binary = 3'd0;
wire    [2:0] jtagbone_phy_rx_cdc_cdc_graycounter0_q_next;
reg     [2:0] jtagbone_phy_rx_cdc_cdc_graycounter0_q_next_binary = 3'd0;
wire          jtagbone_phy_rx_cdc_cdc_graycounter1_ce;
(* dont_touch = "true" *)
reg     [2:0] jtagbone_phy_rx_cdc_cdc_graycounter1_q = 3'd0;
reg     [2:0] jtagbone_phy_rx_cdc_cdc_graycounter1_q_binary = 3'd0;
wire    [2:0] jtagbone_phy_rx_cdc_cdc_graycounter1_q_next;
reg     [2:0] jtagbone_phy_rx_cdc_cdc_graycounter1_q_next_binary = 3'd0;
wire    [2:0] jtagbone_phy_rx_cdc_cdc_produce_rdomain;
wire    [1:0] jtagbone_phy_rx_cdc_cdc_rdport_adr;
wire    [9:0] jtagbone_phy_rx_cdc_cdc_rdport_dat_r;
wire          jtagbone_phy_rx_cdc_cdc_sink_first;
wire          jtagbone_phy_rx_cdc_cdc_sink_last;
wire    [7:0] jtagbone_phy_rx_cdc_cdc_sink_payload_data;
wire          jtagbone_phy_rx_cdc_cdc_sink_ready;
wire          jtagbone_phy_rx_cdc_cdc_sink_valid;
wire          jtagbone_phy_rx_cdc_cdc_source_first;
wire          jtagbone_phy_rx_cdc_cdc_source_last;
wire    [7:0] jtagbone_phy_rx_cdc_cdc_source_payload_data;
wire          jtagbone_phy_rx_cdc_cdc_source_ready;
wire          jtagbone_phy_rx_cdc_cdc_source_valid;
wire    [1:0] jtagbone_phy_rx_cdc_cdc_wrport_adr;
wire    [9:0] jtagbone_phy_rx_cdc_cdc_wrport_dat_r;
wire    [9:0] jtagbone_phy_rx_cdc_cdc_wrport_dat_w;
wire          jtagbone_phy_rx_cdc_cdc_wrport_we;
reg           jtagbone_phy_rx_cdc_sink_sink_first = 1'd0;
reg           jtagbone_phy_rx_cdc_sink_sink_last = 1'd0;
wire    [7:0] jtagbone_phy_rx_cdc_sink_sink_payload_data;
wire          jtagbone_phy_rx_cdc_sink_sink_ready;
wire          jtagbone_phy_rx_cdc_sink_sink_valid;
wire          jtagbone_phy_rx_cdc_source_source_first;
wire          jtagbone_phy_rx_cdc_source_source_last;
wire    [7:0] jtagbone_phy_rx_cdc_source_source_payload_data;
wire          jtagbone_phy_rx_cdc_source_source_ready;
wire          jtagbone_phy_rx_cdc_source_source_valid;
reg     [7:0] jtagbone_phy_rx_data = 8'd0;
reg           jtagbone_phy_rx_valid = 1'd0;
reg           jtagbone_phy_rx_valid_in = 1'd0;
reg           jtagbone_phy_rx_valid_in_jtagphy_next_value3 = 1'd0;
reg           jtagbone_phy_rx_valid_in_jtagphy_next_value_ce3 = 1'd0;
reg           jtagbone_phy_shift_d = 1'd0;
wire          jtagbone_phy_shift_falling;
reg           jtagbone_phy_sink_first = 1'd0;
wire          jtagbone_phy_sink_last;
reg     [7:0] jtagbone_phy_sink_payload_data = 8'd0;
wire          jtagbone_phy_sink_ready;
reg           jtagbone_phy_sink_valid = 1'd0;
wire          jtagbone_phy_source_first;
wire          jtagbone_phy_source_last;
wire    [7:0] jtagbone_phy_source_payload_data;
reg           jtagbone_phy_source_ready = 1'd0;
wire          jtagbone_phy_source_valid;
wire          jtagbone_phy_tx_cdc_cd_rst;
wire    [9:0] jtagbone_phy_tx_cdc_cdc_asyncfifo_din;
wire    [9:0] jtagbone_phy_tx_cdc_cdc_asyncfifo_dout;
wire          jtagbone_phy_tx_cdc_cdc_asyncfifo_re;
wire          jtagbone_phy_tx_cdc_cdc_asyncfifo_readable;
wire          jtagbone_phy_tx_cdc_cdc_asyncfifo_we;
wire          jtagbone_phy_tx_cdc_cdc_asyncfifo_writable;
wire    [2:0] jtagbone_phy_tx_cdc_cdc_consume_wdomain;
wire          jtagbone_phy_tx_cdc_cdc_fifo_in_first;
wire          jtagbone_phy_tx_cdc_cdc_fifo_in_last;
wire    [7:0] jtagbone_phy_tx_cdc_cdc_fifo_in_payload_data;
wire          jtagbone_phy_tx_cdc_cdc_fifo_out_first;
wire          jtagbone_phy_tx_cdc_cdc_fifo_out_last;
wire    [7:0] jtagbone_phy_tx_cdc_cdc_fifo_out_payload_data;
wire          jtagbone_phy_tx_cdc_cdc_graycounter0_ce;
(* dont_touch = "true" *)
reg     [2:0] jtagbone_phy_tx_cdc_cdc_graycounter0_q = 3'd0;
reg     [2:0] jtagbone_phy_tx_cdc_cdc_graycounter0_q_binary = 3'd0;
wire    [2:0] jtagbone_phy_tx_cdc_cdc_graycounter0_q_next;
reg     [2:0] jtagbone_phy_tx_cdc_cdc_graycounter0_q_next_binary = 3'd0;
wire          jtagbone_phy_tx_cdc_cdc_graycounter1_ce;
(* dont_touch = "true" *)
reg     [2:0] jtagbone_phy_tx_cdc_cdc_graycounter1_q = 3'd0;
reg     [2:0] jtagbone_phy_tx_cdc_cdc_graycounter1_q_binary = 3'd0;
wire    [2:0] jtagbone_phy_tx_cdc_cdc_graycounter1_q_next;
reg     [2:0] jtagbone_phy_tx_cdc_cdc_graycounter1_q_next_binary = 3'd0;
wire    [2:0] jtagbone_phy_tx_cdc_cdc_produce_rdomain;
wire    [1:0] jtagbone_phy_tx_cdc_cdc_rdport_adr;
wire    [9:0] jtagbone_phy_tx_cdc_cdc_rdport_dat_r;
wire          jtagbone_phy_tx_cdc_cdc_sink_first;
wire          jtagbone_phy_tx_cdc_cdc_sink_last;
wire    [7:0] jtagbone_phy_tx_cdc_cdc_sink_payload_data;
wire          jtagbone_phy_tx_cdc_cdc_sink_ready;
wire          jtagbone_phy_tx_cdc_cdc_sink_valid;
wire          jtagbone_phy_tx_cdc_cdc_source_first;
wire          jtagbone_phy_tx_cdc_cdc_source_last;
wire    [7:0] jtagbone_phy_tx_cdc_cdc_source_payload_data;
wire          jtagbone_phy_tx_cdc_cdc_source_ready;
wire          jtagbone_phy_tx_cdc_cdc_source_valid;
wire    [1:0] jtagbone_phy_tx_cdc_cdc_wrport_adr;
wire    [9:0] jtagbone_phy_tx_cdc_cdc_wrport_dat_r;
wire    [9:0] jtagbone_phy_tx_cdc_cdc_wrport_dat_w;
wire          jtagbone_phy_tx_cdc_cdc_wrport_we;
wire          jtagbone_phy_tx_cdc_sink_sink_first;
wire          jtagbone_phy_tx_cdc_sink_sink_last;
wire    [7:0] jtagbone_phy_tx_cdc_sink_sink_payload_data;
wire          jtagbone_phy_tx_cdc_sink_sink_ready;
wire          jtagbone_phy_tx_cdc_sink_sink_valid;
wire          jtagbone_phy_tx_cdc_source_source_first;
wire          jtagbone_phy_tx_cdc_source_source_last;
wire    [7:0] jtagbone_phy_tx_cdc_source_source_payload_data;
reg           jtagbone_phy_tx_cdc_source_source_ready = 1'd0;
wire          jtagbone_phy_tx_cdc_source_source_valid;
reg           jtagbone_phy_update_ready = 1'd0;
reg           jtagbone_phy_update_rx = 1'd0;
reg           jtagbone_phy_valid = 1'd0;
reg           jtagbone_phy_valid_jtagphy_next_value0 = 1'd0;
reg           jtagbone_phy_valid_jtagphy_next_value_ce0 = 1'd0;
wire          jtagbone_reset;
wire          jtagbone_wait;
wire          jtagbone_wishbone_ack;
wire   [29:0] jtagbone_wishbone_adr;
reg     [1:0] jtagbone_wishbone_bte = 2'd0;
reg     [2:0] jtagbone_wishbone_cti = 3'd0;
reg           jtagbone_wishbone_cyc = 1'd0;
wire   [31:0] jtagbone_wishbone_dat_r;
wire   [31:0] jtagbone_wishbone_dat_w;
wire          jtagbone_wishbone_err;
wire    [3:0] jtagbone_wishbone_sel;
reg           jtagbone_wishbone_stb = 1'd0;
reg           jtagbone_wishbone_we = 1'd0;
reg     [7:0] jtagbone_words_count = 8'd0;
reg     [7:0] jtagbone_words_count_resetinserter_next_value2 = 8'd0;
reg           jtagbone_words_count_resetinserter_next_value_ce2 = 1'd0;
reg     [1:0] jtagphy_next_state = 2'd0;
reg     [1:0] jtagphy_state = 2'd0;
reg     [1:0] litescopeanalyzer_next_state = 2'd0;
reg     [1:0] litescopeanalyzer_state = 2'd0;
wire          request;
reg     [1:0] reset_storage = 2'd0;
reg           reset_wr_stb = 1'd0;
reg     [2:0] resetinserter_next_state = 3'd0;
reg     [2:0] resetinserter_state = 3'd0;
reg    [29:0] rhs_self0 = 30'd0;
reg    [31:0] rhs_self1 = 32'd0;
reg     [3:0] rhs_self2 = 4'd0;
reg           rhs_self3 = 1'd0;
reg           rhs_self4 = 1'd0;
reg           rhs_self5 = 1'd0;
reg     [2:0] rhs_self6 = 3'd0;
reg     [1:0] rhs_self7 = 2'd0;
wire          rst_meta0;
wire          rst_meta1;
wire          rst_meta2;
wire          rst_meta3;
wire          rst_meta4;
wire          scope_clk;
reg           scope_rst = 1'd0;
reg    [31:0] scratch_storage = 32'd305419896;
reg           scratch_wr_stb = 1'd0;
reg           shared_ack = 1'd0;
wire   [29:0] shared_adr;
wire    [1:0] shared_bte;
wire    [2:0] shared_cti;
wire          shared_cyc;
reg    [31:0] shared_dat_r = 32'd0;
wire   [31:0] shared_dat_w;
wire          shared_err;
wire    [3:0] shared_sel;
wire          shared_stb;
wire          shared_we;
wire          slave_sel;
reg           slave_sel_r = 1'd0;
reg           soc_rst = 1'd0;
wire          sys_clk;
reg           sys_rst = 1'd0;
wire          to242_clk;
wire          to242_rst;
wire          to91_clk;
wire          to91_rst;
wire          wait_1;
reg           wishbone2csr_next_state = 1'd0;
reg           wishbone2csr_state = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg     [2:0] xilinxmultiregimpl00 = 3'd0;
(* async_reg = "true", dont_touch = "true" *)
reg     [2:0] xilinxmultiregimpl01 = 3'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg     [2:0] xilinxmultiregimpl10 = 3'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           xilinxmultiregimpl100 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           xilinxmultiregimpl101 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg     [2:0] xilinxmultiregimpl11 = 3'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg    [10:0] xilinxmultiregimpl110 = 11'd0;
(* async_reg = "true", dont_touch = "true" *)
reg    [10:0] xilinxmultiregimpl111 = 11'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg    [10:0] xilinxmultiregimpl120 = 11'd0;
(* async_reg = "true", dont_touch = "true" *)
reg    [10:0] xilinxmultiregimpl121 = 11'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           xilinxmultiregimpl130 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           xilinxmultiregimpl131 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg    [10:0] xilinxmultiregimpl140 = 11'd0;
(* async_reg = "true", dont_touch = "true" *)
reg    [10:0] xilinxmultiregimpl141 = 11'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg     [2:0] xilinxmultiregimpl150 = 3'd0;
(* async_reg = "true", dont_touch = "true" *)
reg     [2:0] xilinxmultiregimpl151 = 3'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg     [2:0] xilinxmultiregimpl160 = 3'd0;
(* async_reg = "true", dont_touch = "true" *)
reg     [2:0] xilinxmultiregimpl161 = 3'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           xilinxmultiregimpl170 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           xilinxmultiregimpl171 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg     [2:0] xilinxmultiregimpl20 = 3'd0;
(* async_reg = "true", dont_touch = "true" *)
reg     [2:0] xilinxmultiregimpl21 = 3'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg     [2:0] xilinxmultiregimpl30 = 3'd0;
(* async_reg = "true", dont_touch = "true" *)
reg     [2:0] xilinxmultiregimpl31 = 3'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           xilinxmultiregimpl40 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           xilinxmultiregimpl41 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           xilinxmultiregimpl50 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           xilinxmultiregimpl51 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg           xilinxmultiregimpl60 = 1'd0;
(* async_reg = "true", dont_touch = "true" *)
reg           xilinxmultiregimpl61 = 1'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg     [4:0] xilinxmultiregimpl70 = 5'd0;
(* async_reg = "true", dont_touch = "true" *)
reg     [4:0] xilinxmultiregimpl71 = 5'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg     [4:0] xilinxmultiregimpl80 = 5'd0;
(* async_reg = "true", dont_touch = "true" *)
reg     [4:0] xilinxmultiregimpl81 = 5'd0;
(* async_reg = "true", mr_ff = "true", dont_touch = "true" *)
reg    [15:0] xilinxmultiregimpl90 = 16'd0;
(* async_reg = "true", dont_touch = "true" *)
reg    [15:0] xilinxmultiregimpl91 = 16'd0;


assign sys_clk = dbg_clk;
assign dq = dbg_probe;
assign bus_error = error;
assign shared_adr = rhs_self0;
assign shared_dat_w = rhs_self1;
assign shared_sel = rhs_self2;
assign shared_cyc = rhs_self3;
assign shared_stb = rhs_self4;
assign shared_we = rhs_self5;
assign shared_cti = rhs_self6;
assign shared_bte = rhs_self7;
assign jtagbone_wishbone_dat_r = shared_dat_r;
assign jtagbone_wishbone_ack = (shared_ack & (grant == 1'd0));
assign jtagbone_wishbone_err = (shared_err & (grant == 1'd0));
assign request = {jtagbone_wishbone_cyc};
assign grant = 1'd0;
assign slave_sel = (shared_adr[29:14] == 1'd0);
assign interface0_adr = shared_adr;
assign interface0_dat_w = shared_dat_w;
assign interface0_sel = shared_sel;
assign interface0_stb = shared_stb;
assign interface0_we = shared_we;
assign interface0_cti = shared_cti;
assign interface0_bte = shared_bte;
assign interface0_cyc = (shared_cyc & slave_sel);
assign shared_err = interface0_err;
assign wait_1 = ((shared_stb & shared_cyc) & (~shared_ack));
always @(*) begin
    error = 1'd0;
    shared_ack = 1'd0;
    shared_dat_r = 32'd0;
    shared_ack = interface0_ack;
    shared_dat_r = ({32{slave_sel_r}} & interface0_dat_r);
    if (done) begin
        shared_dat_r = 32'hffffffff;
        shared_ack = 1'd1;
        error = 1'd1;
    end
end
assign done = (count == 1'd0);
assign bus_errors_status = bus_errors;
assign jtagbone_wait = (~jtagbone_is_ongoing);
assign jtagbone_reset = jtagbone_done;
assign jtagbone_wishbone_adr = jtagbone_address;
assign jtagbone_wishbone_dat_w = jtagbone_data;
assign jtagbone_wishbone_sel = 4'd15;
always @(*) begin
    jtagbone_phy_sink_payload_data = 8'd0;
    case (jtagbone_data_bytes_count)
        1'd0: begin
            jtagbone_phy_sink_payload_data = jtagbone_data[31:24];
        end
        1'd1: begin
            jtagbone_phy_sink_payload_data = jtagbone_data[31:16];
        end
        2'd2: begin
            jtagbone_phy_sink_payload_data = jtagbone_data[31:8];
        end
        2'd3: begin
            jtagbone_phy_sink_payload_data = jtagbone_data;
        end
    endcase
end
assign jtagbone_phy_sink_last = ((jtagbone_data_bytes_count == 2'd3) & ($signed({1'd0, jtagbone_words_count}) == ($signed({1'd0, jtagbone_length}) - $signed({1'd0, 1'd1}))));
assign jtag_clk = jtagbone_phy_jtag_tck;
assign jtagbone_phy_tx_cdc_sink_sink_valid = jtagbone_phy_sink_valid;
assign jtagbone_phy_sink_ready = jtagbone_phy_tx_cdc_sink_sink_ready;
assign jtagbone_phy_tx_cdc_sink_sink_first = jtagbone_phy_sink_first;
assign jtagbone_phy_tx_cdc_sink_sink_last = jtagbone_phy_sink_last;
assign jtagbone_phy_tx_cdc_sink_sink_payload_data = jtagbone_phy_sink_payload_data;
assign jtagbone_phy_source_valid = jtagbone_phy_rx_cdc_source_source_valid;
assign jtagbone_phy_rx_cdc_source_source_ready = jtagbone_phy_source_ready;
assign jtagbone_phy_source_first = jtagbone_phy_rx_cdc_source_source_first;
assign jtagbone_phy_source_last = jtagbone_phy_rx_cdc_source_source_last;
assign jtagbone_phy_source_payload_data = jtagbone_phy_rx_cdc_source_source_payload_data;
assign jtagbone_phy_shift_falling = (jtagbone_phy_shift_d & (~(jtagbone_phy_jtag_shift & jtagbone_phy_jtag_sel)));
assign jtagbone_phy_fsm_reset = (jtagbone_phy_jtag_reset | (jtagbone_phy_jtag_capture & jtagbone_phy_jtag_sel));
assign jtagbone_phy_rx_cdc_sink_sink_valid = jtagbone_phy_rx_valid;
assign jtagbone_phy_rx_cdc_sink_sink_payload_data = jtagbone_phy_rx_data;
assign from91_clk = sys_clk;
assign to91_clk = jtag_clk;
assign jtagbone_phy_tx_cdc_cd_rst = (sys_rst | jtag_rst);
assign jtagbone_phy_tx_cdc_cdc_sink_valid = jtagbone_phy_tx_cdc_sink_sink_valid;
assign jtagbone_phy_tx_cdc_sink_sink_ready = jtagbone_phy_tx_cdc_cdc_sink_ready;
assign jtagbone_phy_tx_cdc_cdc_sink_first = jtagbone_phy_tx_cdc_sink_sink_first;
assign jtagbone_phy_tx_cdc_cdc_sink_last = jtagbone_phy_tx_cdc_sink_sink_last;
assign jtagbone_phy_tx_cdc_cdc_sink_payload_data = jtagbone_phy_tx_cdc_sink_sink_payload_data;
assign jtagbone_phy_tx_cdc_source_source_valid = jtagbone_phy_tx_cdc_cdc_source_valid;
assign jtagbone_phy_tx_cdc_cdc_source_ready = jtagbone_phy_tx_cdc_source_source_ready;
assign jtagbone_phy_tx_cdc_source_source_first = jtagbone_phy_tx_cdc_cdc_source_first;
assign jtagbone_phy_tx_cdc_source_source_last = jtagbone_phy_tx_cdc_cdc_source_last;
assign jtagbone_phy_tx_cdc_source_source_payload_data = jtagbone_phy_tx_cdc_cdc_source_payload_data;
assign jtagbone_phy_tx_cdc_cdc_asyncfifo_din = {jtagbone_phy_tx_cdc_cdc_fifo_in_last, jtagbone_phy_tx_cdc_cdc_fifo_in_first, jtagbone_phy_tx_cdc_cdc_fifo_in_payload_data};
assign {jtagbone_phy_tx_cdc_cdc_fifo_out_last, jtagbone_phy_tx_cdc_cdc_fifo_out_first, jtagbone_phy_tx_cdc_cdc_fifo_out_payload_data} = jtagbone_phy_tx_cdc_cdc_asyncfifo_dout;
assign jtagbone_phy_tx_cdc_cdc_sink_ready = jtagbone_phy_tx_cdc_cdc_asyncfifo_writable;
assign jtagbone_phy_tx_cdc_cdc_asyncfifo_we = jtagbone_phy_tx_cdc_cdc_sink_valid;
assign jtagbone_phy_tx_cdc_cdc_fifo_in_first = jtagbone_phy_tx_cdc_cdc_sink_first;
assign jtagbone_phy_tx_cdc_cdc_fifo_in_last = jtagbone_phy_tx_cdc_cdc_sink_last;
assign jtagbone_phy_tx_cdc_cdc_fifo_in_payload_data = jtagbone_phy_tx_cdc_cdc_sink_payload_data;
assign jtagbone_phy_tx_cdc_cdc_source_valid = jtagbone_phy_tx_cdc_cdc_asyncfifo_readable;
assign jtagbone_phy_tx_cdc_cdc_source_first = jtagbone_phy_tx_cdc_cdc_fifo_out_first;
assign jtagbone_phy_tx_cdc_cdc_source_last = jtagbone_phy_tx_cdc_cdc_fifo_out_last;
assign jtagbone_phy_tx_cdc_cdc_source_payload_data = jtagbone_phy_tx_cdc_cdc_fifo_out_payload_data;
assign jtagbone_phy_tx_cdc_cdc_asyncfifo_re = jtagbone_phy_tx_cdc_cdc_source_ready;
assign jtagbone_phy_tx_cdc_cdc_graycounter0_ce = (jtagbone_phy_tx_cdc_cdc_asyncfifo_writable & jtagbone_phy_tx_cdc_cdc_asyncfifo_we);
assign jtagbone_phy_tx_cdc_cdc_graycounter1_ce = (jtagbone_phy_tx_cdc_cdc_asyncfifo_readable & jtagbone_phy_tx_cdc_cdc_asyncfifo_re);
assign jtagbone_phy_tx_cdc_cdc_asyncfifo_writable = (((jtagbone_phy_tx_cdc_cdc_graycounter0_q[2] == jtagbone_phy_tx_cdc_cdc_consume_wdomain[2]) | (jtagbone_phy_tx_cdc_cdc_graycounter0_q[1] == jtagbone_phy_tx_cdc_cdc_consume_wdomain[1])) | (jtagbone_phy_tx_cdc_cdc_graycounter0_q[0] != jtagbone_phy_tx_cdc_cdc_consume_wdomain[0]));
assign jtagbone_phy_tx_cdc_cdc_asyncfifo_readable = (jtagbone_phy_tx_cdc_cdc_graycounter1_q != jtagbone_phy_tx_cdc_cdc_produce_rdomain);
assign jtagbone_phy_tx_cdc_cdc_wrport_adr = jtagbone_phy_tx_cdc_cdc_graycounter0_q_binary[1:0];
assign jtagbone_phy_tx_cdc_cdc_wrport_dat_w = jtagbone_phy_tx_cdc_cdc_asyncfifo_din;
assign jtagbone_phy_tx_cdc_cdc_wrport_we = jtagbone_phy_tx_cdc_cdc_graycounter0_ce;
assign jtagbone_phy_tx_cdc_cdc_rdport_adr = jtagbone_phy_tx_cdc_cdc_graycounter1_q_next_binary[1:0];
assign jtagbone_phy_tx_cdc_cdc_asyncfifo_dout = jtagbone_phy_tx_cdc_cdc_rdport_dat_r;
always @(*) begin
    jtagbone_phy_tx_cdc_cdc_graycounter0_q_next_binary = 3'd0;
    if (jtagbone_phy_tx_cdc_cdc_graycounter0_ce) begin
        jtagbone_phy_tx_cdc_cdc_graycounter0_q_next_binary = (jtagbone_phy_tx_cdc_cdc_graycounter0_q_binary + 1'd1);
    end else begin
        jtagbone_phy_tx_cdc_cdc_graycounter0_q_next_binary = jtagbone_phy_tx_cdc_cdc_graycounter0_q_binary;
    end
end
assign jtagbone_phy_tx_cdc_cdc_graycounter0_q_next = (jtagbone_phy_tx_cdc_cdc_graycounter0_q_next_binary ^ jtagbone_phy_tx_cdc_cdc_graycounter0_q_next_binary[2:1]);
always @(*) begin
    jtagbone_phy_tx_cdc_cdc_graycounter1_q_next_binary = 3'd0;
    if (jtagbone_phy_tx_cdc_cdc_graycounter1_ce) begin
        jtagbone_phy_tx_cdc_cdc_graycounter1_q_next_binary = (jtagbone_phy_tx_cdc_cdc_graycounter1_q_binary + 1'd1);
    end else begin
        jtagbone_phy_tx_cdc_cdc_graycounter1_q_next_binary = jtagbone_phy_tx_cdc_cdc_graycounter1_q_binary;
    end
end
assign jtagbone_phy_tx_cdc_cdc_graycounter1_q_next = (jtagbone_phy_tx_cdc_cdc_graycounter1_q_next_binary ^ jtagbone_phy_tx_cdc_cdc_graycounter1_q_next_binary[2:1]);
assign from242_clk = jtag_clk;
assign to242_clk = sys_clk;
assign jtagbone_phy_rx_cdc_cd_rst = (jtag_rst | sys_rst);
assign jtagbone_phy_rx_cdc_cdc_sink_valid = jtagbone_phy_rx_cdc_sink_sink_valid;
assign jtagbone_phy_rx_cdc_sink_sink_ready = jtagbone_phy_rx_cdc_cdc_sink_ready;
assign jtagbone_phy_rx_cdc_cdc_sink_first = jtagbone_phy_rx_cdc_sink_sink_first;
assign jtagbone_phy_rx_cdc_cdc_sink_last = jtagbone_phy_rx_cdc_sink_sink_last;
assign jtagbone_phy_rx_cdc_cdc_sink_payload_data = jtagbone_phy_rx_cdc_sink_sink_payload_data;
assign jtagbone_phy_rx_cdc_source_source_valid = jtagbone_phy_rx_cdc_cdc_source_valid;
assign jtagbone_phy_rx_cdc_cdc_source_ready = jtagbone_phy_rx_cdc_source_source_ready;
assign jtagbone_phy_rx_cdc_source_source_first = jtagbone_phy_rx_cdc_cdc_source_first;
assign jtagbone_phy_rx_cdc_source_source_last = jtagbone_phy_rx_cdc_cdc_source_last;
assign jtagbone_phy_rx_cdc_source_source_payload_data = jtagbone_phy_rx_cdc_cdc_source_payload_data;
assign jtagbone_phy_rx_cdc_cdc_asyncfifo_din = {jtagbone_phy_rx_cdc_cdc_fifo_in_last, jtagbone_phy_rx_cdc_cdc_fifo_in_first, jtagbone_phy_rx_cdc_cdc_fifo_in_payload_data};
assign {jtagbone_phy_rx_cdc_cdc_fifo_out_last, jtagbone_phy_rx_cdc_cdc_fifo_out_first, jtagbone_phy_rx_cdc_cdc_fifo_out_payload_data} = jtagbone_phy_rx_cdc_cdc_asyncfifo_dout;
assign jtagbone_phy_rx_cdc_cdc_sink_ready = jtagbone_phy_rx_cdc_cdc_asyncfifo_writable;
assign jtagbone_phy_rx_cdc_cdc_asyncfifo_we = jtagbone_phy_rx_cdc_cdc_sink_valid;
assign jtagbone_phy_rx_cdc_cdc_fifo_in_first = jtagbone_phy_rx_cdc_cdc_sink_first;
assign jtagbone_phy_rx_cdc_cdc_fifo_in_last = jtagbone_phy_rx_cdc_cdc_sink_last;
assign jtagbone_phy_rx_cdc_cdc_fifo_in_payload_data = jtagbone_phy_rx_cdc_cdc_sink_payload_data;
assign jtagbone_phy_rx_cdc_cdc_source_valid = jtagbone_phy_rx_cdc_cdc_asyncfifo_readable;
assign jtagbone_phy_rx_cdc_cdc_source_first = jtagbone_phy_rx_cdc_cdc_fifo_out_first;
assign jtagbone_phy_rx_cdc_cdc_source_last = jtagbone_phy_rx_cdc_cdc_fifo_out_last;
assign jtagbone_phy_rx_cdc_cdc_source_payload_data = jtagbone_phy_rx_cdc_cdc_fifo_out_payload_data;
assign jtagbone_phy_rx_cdc_cdc_asyncfifo_re = jtagbone_phy_rx_cdc_cdc_source_ready;
assign jtagbone_phy_rx_cdc_cdc_graycounter0_ce = (jtagbone_phy_rx_cdc_cdc_asyncfifo_writable & jtagbone_phy_rx_cdc_cdc_asyncfifo_we);
assign jtagbone_phy_rx_cdc_cdc_graycounter1_ce = (jtagbone_phy_rx_cdc_cdc_asyncfifo_readable & jtagbone_phy_rx_cdc_cdc_asyncfifo_re);
assign jtagbone_phy_rx_cdc_cdc_asyncfifo_writable = (((jtagbone_phy_rx_cdc_cdc_graycounter0_q[2] == jtagbone_phy_rx_cdc_cdc_consume_wdomain[2]) | (jtagbone_phy_rx_cdc_cdc_graycounter0_q[1] == jtagbone_phy_rx_cdc_cdc_consume_wdomain[1])) | (jtagbone_phy_rx_cdc_cdc_graycounter0_q[0] != jtagbone_phy_rx_cdc_cdc_consume_wdomain[0]));
assign jtagbone_phy_rx_cdc_cdc_asyncfifo_readable = (jtagbone_phy_rx_cdc_cdc_graycounter1_q != jtagbone_phy_rx_cdc_cdc_produce_rdomain);
assign jtagbone_phy_rx_cdc_cdc_wrport_adr = jtagbone_phy_rx_cdc_cdc_graycounter0_q_binary[1:0];
assign jtagbone_phy_rx_cdc_cdc_wrport_dat_w = jtagbone_phy_rx_cdc_cdc_asyncfifo_din;
assign jtagbone_phy_rx_cdc_cdc_wrport_we = jtagbone_phy_rx_cdc_cdc_graycounter0_ce;
assign jtagbone_phy_rx_cdc_cdc_rdport_adr = jtagbone_phy_rx_cdc_cdc_graycounter1_q_next_binary[1:0];
assign jtagbone_phy_rx_cdc_cdc_asyncfifo_dout = jtagbone_phy_rx_cdc_cdc_rdport_dat_r;
always @(*) begin
    jtagbone_phy_rx_cdc_cdc_graycounter0_q_next_binary = 3'd0;
    if (jtagbone_phy_rx_cdc_cdc_graycounter0_ce) begin
        jtagbone_phy_rx_cdc_cdc_graycounter0_q_next_binary = (jtagbone_phy_rx_cdc_cdc_graycounter0_q_binary + 1'd1);
    end else begin
        jtagbone_phy_rx_cdc_cdc_graycounter0_q_next_binary = jtagbone_phy_rx_cdc_cdc_graycounter0_q_binary;
    end
end
assign jtagbone_phy_rx_cdc_cdc_graycounter0_q_next = (jtagbone_phy_rx_cdc_cdc_graycounter0_q_next_binary ^ jtagbone_phy_rx_cdc_cdc_graycounter0_q_next_binary[2:1]);
always @(*) begin
    jtagbone_phy_rx_cdc_cdc_graycounter1_q_next_binary = 3'd0;
    if (jtagbone_phy_rx_cdc_cdc_graycounter1_ce) begin
        jtagbone_phy_rx_cdc_cdc_graycounter1_q_next_binary = (jtagbone_phy_rx_cdc_cdc_graycounter1_q_binary + 1'd1);
    end else begin
        jtagbone_phy_rx_cdc_cdc_graycounter1_q_next_binary = jtagbone_phy_rx_cdc_cdc_graycounter1_q_binary;
    end
end
assign jtagbone_phy_rx_cdc_cdc_graycounter1_q_next = (jtagbone_phy_rx_cdc_cdc_graycounter1_q_next_binary ^ jtagbone_phy_rx_cdc_cdc_graycounter1_q_next_binary[2:1]);
always @(*) begin
    jtagbone_phy_count_jtagphy_next_value2 = 3'd0;
    jtagbone_phy_count_jtagphy_next_value_ce2 = 1'd0;
    jtagbone_phy_data_jtagphy_next_value1 = 8'd0;
    jtagbone_phy_data_jtagphy_next_value_ce1 = 1'd0;
    jtagbone_phy_jtag_tdo = 1'd0;
    jtagbone_phy_rx_valid_in_jtagphy_next_value3 = 1'd0;
    jtagbone_phy_rx_valid_in_jtagphy_next_value_ce3 = 1'd0;
    jtagbone_phy_tx_cdc_source_source_ready = 1'd0;
    jtagbone_phy_update_ready = 1'd0;
    jtagbone_phy_update_rx = 1'd0;
    jtagbone_phy_valid_jtagphy_next_value0 = 1'd0;
    jtagbone_phy_valid_jtagphy_next_value_ce0 = 1'd0;
    jtagphy_next_state = 2'd0;
    jtagphy_next_state = jtagphy_state;
    case (jtagphy_state)
        1'd1: begin
            jtagbone_phy_jtag_tdo = jtagbone_phy_data[0];
            if ((jtagbone_phy_jtag_shift & jtagbone_phy_jtag_sel)) begin
                jtagbone_phy_count_jtagphy_next_value2 = (jtagbone_phy_count + 1'd1);
                jtagbone_phy_count_jtagphy_next_value_ce2 = 1'd1;
                jtagbone_phy_data_jtagphy_next_value1 = {jtagbone_phy_jtag_tdi, jtagbone_phy_data[7:1]};
                jtagbone_phy_data_jtagphy_next_value_ce1 = 1'd1;
                if ((jtagbone_phy_count == 3'd7)) begin
                    jtagphy_next_state = 2'd2;
                end
            end
        end
        2'd2: begin
            jtagbone_phy_jtag_tdo = jtagbone_phy_valid;
            if ((jtagbone_phy_jtag_shift & jtagbone_phy_jtag_sel)) begin
                jtagbone_phy_rx_valid_in_jtagphy_next_value3 = jtagbone_phy_jtag_tdi;
                jtagbone_phy_rx_valid_in_jtagphy_next_value_ce3 = 1'd1;
                jtagphy_next_state = 2'd3;
            end
        end
        2'd3: begin
            if ((jtagbone_phy_jtag_shift & jtagbone_phy_jtag_sel)) begin
                jtagbone_phy_update_rx = 1'd1;
                jtagbone_phy_update_ready = 1'd1;
                jtagphy_next_state = 1'd0;
            end
            if (jtagbone_phy_shift_falling) begin
                jtagbone_phy_update_rx = 1'd1;
                jtagbone_phy_update_ready = 1'd1;
                jtagphy_next_state = 1'd0;
            end
        end
        default: begin
            jtagbone_phy_jtag_tdo = jtagbone_phy_ready;
            if ((jtagbone_phy_jtag_shift & jtagbone_phy_jtag_sel)) begin
                jtagbone_phy_tx_cdc_source_source_ready = jtagbone_phy_jtag_tdi;
                jtagbone_phy_valid_jtagphy_next_value0 = jtagbone_phy_tx_cdc_source_source_valid;
                jtagbone_phy_valid_jtagphy_next_value_ce0 = 1'd1;
                jtagbone_phy_data_jtagphy_next_value1 = jtagbone_phy_tx_cdc_source_source_payload_data;
                jtagbone_phy_data_jtagphy_next_value_ce1 = 1'd1;
                jtagbone_phy_count_jtagphy_next_value2 = 1'd0;
                jtagbone_phy_count_jtagphy_next_value_ce2 = 1'd1;
                jtagphy_next_state = 1'd1;
            end
        end
    endcase
end
always @(*) begin
    jtagbone_addr_bytes_count_resetinserter_next_value1 = 2'd0;
    jtagbone_addr_bytes_count_resetinserter_next_value_ce1 = 1'd0;
    jtagbone_address_resetinserter_next_value5 = 32'd0;
    jtagbone_address_resetinserter_next_value_ce5 = 1'd0;
    jtagbone_cmd_resetinserter_next_value3 = 8'd0;
    jtagbone_cmd_resetinserter_next_value_ce3 = 1'd0;
    jtagbone_data_bytes_count_resetinserter_next_value0 = 2'd0;
    jtagbone_data_bytes_count_resetinserter_next_value_ce0 = 1'd0;
    jtagbone_data_resetinserter_next_value7 = 32'd0;
    jtagbone_data_resetinserter_next_value_ce7 = 1'd0;
    jtagbone_incr_resetinserter_next_value6 = 1'd0;
    jtagbone_incr_resetinserter_next_value_ce6 = 1'd0;
    jtagbone_is_ongoing = 1'd0;
    jtagbone_length_resetinserter_next_value4 = 8'd0;
    jtagbone_length_resetinserter_next_value_ce4 = 1'd0;
    jtagbone_phy_sink_valid = 1'd0;
    jtagbone_phy_source_ready = 1'd0;
    jtagbone_wishbone_cyc = 1'd0;
    jtagbone_wishbone_stb = 1'd0;
    jtagbone_wishbone_we = 1'd0;
    jtagbone_words_count_resetinserter_next_value2 = 8'd0;
    jtagbone_words_count_resetinserter_next_value_ce2 = 1'd0;
    resetinserter_next_state = 3'd0;
    resetinserter_next_state = resetinserter_state;
    case (resetinserter_state)
        1'd1: begin
            jtagbone_phy_source_ready = 1'd1;
            if (jtagbone_phy_source_valid) begin
                jtagbone_length_resetinserter_next_value4 = jtagbone_phy_source_payload_data;
                jtagbone_length_resetinserter_next_value_ce4 = 1'd1;
                resetinserter_next_state = 2'd2;
            end
        end
        2'd2: begin
            jtagbone_phy_source_ready = 1'd1;
            if (jtagbone_phy_source_valid) begin
                jtagbone_address_resetinserter_next_value5 = {jtagbone_address, jtagbone_phy_source_payload_data};
                jtagbone_address_resetinserter_next_value_ce5 = 1'd1;
                jtagbone_addr_bytes_count_resetinserter_next_value1 = (jtagbone_addr_bytes_count + 1'd1);
                jtagbone_addr_bytes_count_resetinserter_next_value_ce1 = 1'd1;
                if ((jtagbone_addr_bytes_count == 2'd3)) begin
                    if (((jtagbone_cmd == 1'd1) | (jtagbone_cmd == 2'd3))) begin
                        jtagbone_incr_resetinserter_next_value6 = (jtagbone_cmd == 1'd1);
                        jtagbone_incr_resetinserter_next_value_ce6 = 1'd1;
                        resetinserter_next_state = 2'd3;
                    end else begin
                        if (((jtagbone_cmd == 2'd2) | (jtagbone_cmd == 3'd4))) begin
                            jtagbone_incr_resetinserter_next_value6 = (jtagbone_cmd == 2'd2);
                            jtagbone_incr_resetinserter_next_value_ce6 = 1'd1;
                            resetinserter_next_state = 3'd5;
                        end else begin
                            resetinserter_next_state = 1'd0;
                        end
                    end
                end
            end
        end
        2'd3: begin
            jtagbone_phy_source_ready = 1'd1;
            if (jtagbone_phy_source_valid) begin
                jtagbone_data_resetinserter_next_value7 = {jtagbone_data, jtagbone_phy_source_payload_data};
                jtagbone_data_resetinserter_next_value_ce7 = 1'd1;
                jtagbone_data_bytes_count_resetinserter_next_value0 = (jtagbone_data_bytes_count + 1'd1);
                jtagbone_data_bytes_count_resetinserter_next_value_ce0 = 1'd1;
                if ((jtagbone_data_bytes_count == 2'd3)) begin
                    resetinserter_next_state = 3'd4;
                end
            end
        end
        3'd4: begin
            jtagbone_phy_source_ready = 1'd0;
            jtagbone_wishbone_stb = 1'd1;
            jtagbone_wishbone_we = 1'd1;
            jtagbone_wishbone_cyc = 1'd1;
            if (jtagbone_wishbone_ack) begin
                jtagbone_words_count_resetinserter_next_value2 = (jtagbone_words_count + 1'd1);
                jtagbone_words_count_resetinserter_next_value_ce2 = 1'd1;
                jtagbone_address_resetinserter_next_value5 = (jtagbone_address + jtagbone_incr);
                jtagbone_address_resetinserter_next_value_ce5 = 1'd1;
                if (($signed({1'd0, jtagbone_words_count}) == ($signed({1'd0, jtagbone_length}) - $signed({1'd0, 1'd1})))) begin
                    resetinserter_next_state = 1'd0;
                end else begin
                    resetinserter_next_state = 2'd3;
                end
            end
        end
        3'd5: begin
            jtagbone_phy_source_ready = 1'd0;
            jtagbone_wishbone_stb = 1'd1;
            jtagbone_wishbone_we = 1'd0;
            jtagbone_wishbone_cyc = 1'd1;
            if (jtagbone_wishbone_ack) begin
                jtagbone_data_resetinserter_next_value7 = jtagbone_wishbone_dat_r;
                jtagbone_data_resetinserter_next_value_ce7 = 1'd1;
                resetinserter_next_state = 3'd6;
            end
        end
        3'd6: begin
            jtagbone_phy_source_ready = 1'd0;
            jtagbone_phy_sink_valid = 1'd1;
            if (jtagbone_phy_sink_ready) begin
                jtagbone_data_bytes_count_resetinserter_next_value0 = (jtagbone_data_bytes_count + 1'd1);
                jtagbone_data_bytes_count_resetinserter_next_value_ce0 = 1'd1;
                if ((jtagbone_data_bytes_count == 2'd3)) begin
                    jtagbone_words_count_resetinserter_next_value2 = (jtagbone_words_count + 1'd1);
                    jtagbone_words_count_resetinserter_next_value_ce2 = 1'd1;
                    jtagbone_address_resetinserter_next_value5 = (jtagbone_address + jtagbone_incr);
                    jtagbone_address_resetinserter_next_value_ce5 = 1'd1;
                    if (($signed({1'd0, jtagbone_words_count}) == ($signed({1'd0, jtagbone_length}) - $signed({1'd0, 1'd1})))) begin
                        resetinserter_next_state = 1'd0;
                    end else begin
                        resetinserter_next_state = 3'd5;
                    end
                end
            end
        end
        default: begin
            jtagbone_is_ongoing = 1'd1;
            jtagbone_phy_source_ready = 1'd1;
            jtagbone_data_bytes_count_resetinserter_next_value0 = 1'd0;
            jtagbone_data_bytes_count_resetinserter_next_value_ce0 = 1'd1;
            jtagbone_addr_bytes_count_resetinserter_next_value1 = 1'd0;
            jtagbone_addr_bytes_count_resetinserter_next_value_ce1 = 1'd1;
            jtagbone_words_count_resetinserter_next_value2 = 1'd0;
            jtagbone_words_count_resetinserter_next_value_ce2 = 1'd1;
            if (jtagbone_phy_source_valid) begin
                jtagbone_cmd_resetinserter_next_value3 = jtagbone_phy_source_payload_data;
                jtagbone_cmd_resetinserter_next_value_ce3 = 1'd1;
                resetinserter_next_state = 1'd1;
            end
        end
    endcase
end
assign jtagbone_done = (jtagbone_count == 1'd0);
assign scope_clk = sys_clk;
assign analyzer_mux_valid = 1'd1;
assign analyzer_mux_payload_data = {dq};
always @(*) begin
    analyzer_mux_ready = 1'd0;
    analyzer_mux_source_first = 1'd0;
    analyzer_mux_source_last = 1'd0;
    analyzer_mux_source_payload_data = 16'd0;
    analyzer_mux_source_payload_hit = 1'd0;
    analyzer_mux_source_valid = 1'd0;
    case (analyzer_mux_value)
        1'd0: begin
            analyzer_mux_source_valid = analyzer_mux_valid;
            analyzer_mux_ready = analyzer_mux_source_ready;
            analyzer_mux_source_first = analyzer_mux_first;
            analyzer_mux_source_last = analyzer_mux_last;
            analyzer_mux_source_payload_data = analyzer_mux_payload_data;
            analyzer_mux_source_payload_hit = analyzer_mux_payload_hit;
        end
    endcase
end
assign analyzer_trigger_mem_sink_valid = analyzer_trigger_mem_write_re;
assign analyzer_trigger_mem_sink_payload_mask = analyzer_trigger_mem_mask_storage;
assign analyzer_trigger_mem_sink_payload_value = analyzer_trigger_mem_value_storage;
assign analyzer_trigger_mem_full_status = (~analyzer_trigger_mem_sink_ready);
assign analyzer_trigger_sink_sink_ready = 1'd1;
assign analyzer_trigger_hit = ((analyzer_trigger_sink_d_payload_data & analyzer_trigger_mem_source_payload_mask) == (analyzer_trigger_mem_source_payload_value & analyzer_trigger_mem_source_payload_mask));
assign analyzer_trigger_mem_source_ready = (((analyzer_trigger_enable & analyzer_trigger_sink_d_valid) & analyzer_trigger_hit) | analyzer_trigger_flushing);
assign analyzer_trigger_source_source_valid = analyzer_trigger_sink_d_valid;
assign analyzer_trigger_source_source_first = analyzer_trigger_sink_d_first;
assign analyzer_trigger_source_source_last = analyzer_trigger_sink_d_last;
assign analyzer_trigger_source_source_payload_data = analyzer_trigger_sink_d_payload_data;
assign analyzer_trigger_done = (~analyzer_trigger_mem_source_valid);
always @(*) begin
    analyzer_trigger_source_source_payload_hit = 1'd0;
    analyzer_trigger_source_source_payload_hit = analyzer_trigger_sink_d_payload_hit;
    analyzer_trigger_source_source_payload_hit = analyzer_trigger_done;
end
assign analyzer_trigger_mem_asyncfifo_din = {analyzer_trigger_mem_fifo_in_last, analyzer_trigger_mem_fifo_in_first, analyzer_trigger_mem_fifo_in_payload_value, analyzer_trigger_mem_fifo_in_payload_mask};
assign {analyzer_trigger_mem_fifo_out_last, analyzer_trigger_mem_fifo_out_first, analyzer_trigger_mem_fifo_out_payload_value, analyzer_trigger_mem_fifo_out_payload_mask} = analyzer_trigger_mem_dout;
assign analyzer_trigger_mem_sink_ready = analyzer_trigger_mem_asyncfifo_writable;
assign analyzer_trigger_mem_asyncfifo_we = analyzer_trigger_mem_sink_valid;
assign analyzer_trigger_mem_fifo_in_first = analyzer_trigger_mem_sink_first;
assign analyzer_trigger_mem_fifo_in_last = analyzer_trigger_mem_sink_last;
assign analyzer_trigger_mem_fifo_in_payload_mask = analyzer_trigger_mem_sink_payload_mask;
assign analyzer_trigger_mem_fifo_in_payload_value = analyzer_trigger_mem_sink_payload_value;
assign analyzer_trigger_mem_source_valid = analyzer_trigger_mem_readable;
assign analyzer_trigger_mem_source_first = analyzer_trigger_mem_fifo_out_first;
assign analyzer_trigger_mem_source_last = analyzer_trigger_mem_fifo_out_last;
assign analyzer_trigger_mem_source_payload_mask = analyzer_trigger_mem_fifo_out_payload_mask;
assign analyzer_trigger_mem_source_payload_value = analyzer_trigger_mem_fifo_out_payload_value;
assign analyzer_trigger_mem_re = analyzer_trigger_mem_source_ready;
assign analyzer_trigger_mem_asyncfifo_re = (analyzer_trigger_mem_re | (~analyzer_trigger_mem_readable));
assign analyzer_trigger_mem_graycounter0_ce = (analyzer_trigger_mem_asyncfifo_writable & analyzer_trigger_mem_asyncfifo_we);
assign analyzer_trigger_mem_graycounter1_ce = (analyzer_trigger_mem_asyncfifo_readable & analyzer_trigger_mem_asyncfifo_re);
assign analyzer_trigger_mem_asyncfifo_writable = (((analyzer_trigger_mem_graycounter0_q[4] == analyzer_trigger_mem_consume_wdomain[4]) | (analyzer_trigger_mem_graycounter0_q[3] == analyzer_trigger_mem_consume_wdomain[3])) | (analyzer_trigger_mem_graycounter0_q[2:0] != analyzer_trigger_mem_consume_wdomain[2:0]));
assign analyzer_trigger_mem_asyncfifo_readable = (analyzer_trigger_mem_graycounter1_q != analyzer_trigger_mem_produce_rdomain);
assign analyzer_trigger_mem_wrport_adr = analyzer_trigger_mem_graycounter0_q_binary[3:0];
assign analyzer_trigger_mem_wrport_dat_w = analyzer_trigger_mem_asyncfifo_din;
assign analyzer_trigger_mem_wrport_we = analyzer_trigger_mem_graycounter0_ce;
assign analyzer_trigger_mem_rdport_adr = analyzer_trigger_mem_graycounter1_q_next_binary[3:0];
assign analyzer_trigger_mem_asyncfifo_dout = analyzer_trigger_mem_rdport_dat_r;
always @(*) begin
    analyzer_trigger_mem_graycounter0_q_next_binary = 5'd0;
    if (analyzer_trigger_mem_graycounter0_ce) begin
        analyzer_trigger_mem_graycounter0_q_next_binary = (analyzer_trigger_mem_graycounter0_q_binary + 1'd1);
    end else begin
        analyzer_trigger_mem_graycounter0_q_next_binary = analyzer_trigger_mem_graycounter0_q_binary;
    end
end
assign analyzer_trigger_mem_graycounter0_q_next = (analyzer_trigger_mem_graycounter0_q_next_binary ^ analyzer_trigger_mem_graycounter0_q_next_binary[4:1]);
always @(*) begin
    analyzer_trigger_mem_graycounter1_q_next_binary = 5'd0;
    if (analyzer_trigger_mem_graycounter1_ce) begin
        analyzer_trigger_mem_graycounter1_q_next_binary = (analyzer_trigger_mem_graycounter1_q_binary + 1'd1);
    end else begin
        analyzer_trigger_mem_graycounter1_q_next_binary = analyzer_trigger_mem_graycounter1_q_binary;
    end
end
assign analyzer_trigger_mem_graycounter1_q_next = (analyzer_trigger_mem_graycounter1_q_next_binary ^ analyzer_trigger_mem_graycounter1_q_next_binary[4:1]);
assign analyzer_subsampler_done = (analyzer_subsampler_counter == analyzer_subsampler_value);
assign analyzer_subsampler_sink_ready = analyzer_subsampler_source_ready;
assign analyzer_subsampler_source_first = analyzer_subsampler_sink_first;
assign analyzer_subsampler_source_last = analyzer_subsampler_sink_last;
assign analyzer_subsampler_source_payload_data = analyzer_subsampler_sink_payload_data;
assign analyzer_subsampler_source_payload_hit = analyzer_subsampler_sink_payload_hit;
assign analyzer_subsampler_source_valid = (analyzer_subsampler_sink_valid & analyzer_subsampler_done);
assign analyzer_storage_level = analyzer_storage_mem_level1;
assign analyzer_storage_read_source_valid = analyzer_storage_cdc_source_valid;
assign analyzer_storage_cdc_source_ready = analyzer_storage_read_source_ready;
assign analyzer_storage_read_source_first = analyzer_storage_cdc_source_first;
assign analyzer_storage_read_source_last = analyzer_storage_cdc_source_last;
assign analyzer_storage_read_source_payload_data = analyzer_storage_cdc_source_payload_data;
assign analyzer_storage_read_source_ready = ((analyzer_storage_mem_data_rd_stb | (~analyzer_storage_enable_storage)) | analyzer_storage_flush_read_sys);
assign analyzer_storage_mem_data_status = analyzer_storage_read_source_payload_data;
assign analyzer_storage_mem_syncfifo_din = {analyzer_storage_mem_fifo_in_last, analyzer_storage_mem_fifo_in_first, analyzer_storage_mem_fifo_in_payload_data};
assign {analyzer_storage_mem_fifo_out_last, analyzer_storage_mem_fifo_out_first, analyzer_storage_mem_fifo_out_payload_data} = analyzer_storage_mem_syncfifo_dout;
assign analyzer_storage_mem_sink_ready = analyzer_storage_mem_syncfifo_writable;
assign analyzer_storage_mem_syncfifo_we = analyzer_storage_mem_sink_valid;
assign analyzer_storage_mem_fifo_in_first = analyzer_storage_mem_sink_first;
assign analyzer_storage_mem_fifo_in_last = analyzer_storage_mem_sink_last;
assign analyzer_storage_mem_fifo_in_payload_data = analyzer_storage_mem_sink_payload_data;
assign analyzer_storage_mem_source_valid = analyzer_storage_mem_readable;
assign analyzer_storage_mem_source_first = analyzer_storage_mem_fifo_out_first;
assign analyzer_storage_mem_source_last = analyzer_storage_mem_fifo_out_last;
assign analyzer_storage_mem_source_payload_data = analyzer_storage_mem_fifo_out_payload_data;
assign analyzer_storage_mem_re = analyzer_storage_mem_source_ready;
assign analyzer_storage_mem_syncfifo_re = (analyzer_storage_mem_syncfifo_readable & ((~analyzer_storage_mem_readable) | analyzer_storage_mem_re));
assign analyzer_storage_mem_level1 = (analyzer_storage_mem_level0 + analyzer_storage_mem_readable);
always @(*) begin
    analyzer_storage_mem_wrport_adr = 10'd0;
    if (analyzer_storage_mem_replace) begin
        analyzer_storage_mem_wrport_adr = (analyzer_storage_mem_produce - 1'd1);
    end else begin
        analyzer_storage_mem_wrport_adr = analyzer_storage_mem_produce;
    end
end
assign analyzer_storage_mem_wrport_dat_w = analyzer_storage_mem_syncfifo_din;
assign analyzer_storage_mem_wrport_we = (analyzer_storage_mem_syncfifo_we & (analyzer_storage_mem_syncfifo_writable | analyzer_storage_mem_replace));
assign analyzer_storage_mem_do_read = (analyzer_storage_mem_syncfifo_readable & analyzer_storage_mem_syncfifo_re);
assign analyzer_storage_mem_rdport_adr = analyzer_storage_mem_consume;
assign analyzer_storage_mem_syncfifo_dout = analyzer_storage_mem_rdport_dat_r;
assign analyzer_storage_mem_rdport_re = analyzer_storage_mem_do_read;
assign analyzer_storage_mem_syncfifo_writable = (analyzer_storage_mem_level0 != 11'h400);
assign analyzer_storage_mem_syncfifo_readable = (analyzer_storage_mem_level0 != 1'd0);
assign analyzer_storage_cdc_asyncfifo_din = {analyzer_storage_cdc_fifo_in_last, analyzer_storage_cdc_fifo_in_first, analyzer_storage_cdc_fifo_in_payload_data};
assign {analyzer_storage_cdc_fifo_out_last, analyzer_storage_cdc_fifo_out_first, analyzer_storage_cdc_fifo_out_payload_data} = analyzer_storage_cdc_asyncfifo_dout;
assign analyzer_storage_cdc_sink_ready = analyzer_storage_cdc_asyncfifo_writable;
assign analyzer_storage_cdc_asyncfifo_we = analyzer_storage_cdc_sink_valid;
assign analyzer_storage_cdc_fifo_in_first = analyzer_storage_cdc_sink_first;
assign analyzer_storage_cdc_fifo_in_last = analyzer_storage_cdc_sink_last;
assign analyzer_storage_cdc_fifo_in_payload_data = analyzer_storage_cdc_sink_payload_data;
assign analyzer_storage_cdc_source_valid = analyzer_storage_cdc_asyncfifo_readable;
assign analyzer_storage_cdc_source_first = analyzer_storage_cdc_fifo_out_first;
assign analyzer_storage_cdc_source_last = analyzer_storage_cdc_fifo_out_last;
assign analyzer_storage_cdc_source_payload_data = analyzer_storage_cdc_fifo_out_payload_data;
assign analyzer_storage_cdc_asyncfifo_re = analyzer_storage_cdc_source_ready;
assign analyzer_storage_cdc_graycounter0_ce = (analyzer_storage_cdc_asyncfifo_writable & analyzer_storage_cdc_asyncfifo_we);
assign analyzer_storage_cdc_graycounter1_ce = (analyzer_storage_cdc_asyncfifo_readable & analyzer_storage_cdc_asyncfifo_re);
assign analyzer_storage_cdc_asyncfifo_writable = (((analyzer_storage_cdc_graycounter0_q[2] == analyzer_storage_cdc_consume_wdomain[2]) | (analyzer_storage_cdc_graycounter0_q[1] == analyzer_storage_cdc_consume_wdomain[1])) | (analyzer_storage_cdc_graycounter0_q[0] != analyzer_storage_cdc_consume_wdomain[0]));
assign analyzer_storage_cdc_asyncfifo_readable = (analyzer_storage_cdc_graycounter1_q != analyzer_storage_cdc_produce_rdomain);
assign analyzer_storage_cdc_wrport_adr = analyzer_storage_cdc_graycounter0_q_binary[1:0];
assign analyzer_storage_cdc_wrport_dat_w = analyzer_storage_cdc_asyncfifo_din;
assign analyzer_storage_cdc_wrport_we = analyzer_storage_cdc_graycounter0_ce;
assign analyzer_storage_cdc_rdport_adr = analyzer_storage_cdc_graycounter1_q_next_binary[1:0];
assign analyzer_storage_cdc_asyncfifo_dout = analyzer_storage_cdc_rdport_dat_r;
always @(*) begin
    analyzer_storage_cdc_graycounter0_q_next_binary = 3'd0;
    if (analyzer_storage_cdc_graycounter0_ce) begin
        analyzer_storage_cdc_graycounter0_q_next_binary = (analyzer_storage_cdc_graycounter0_q_binary + 1'd1);
    end else begin
        analyzer_storage_cdc_graycounter0_q_next_binary = analyzer_storage_cdc_graycounter0_q_binary;
    end
end
assign analyzer_storage_cdc_graycounter0_q_next = (analyzer_storage_cdc_graycounter0_q_next_binary ^ analyzer_storage_cdc_graycounter0_q_next_binary[2:1]);
always @(*) begin
    analyzer_storage_cdc_graycounter1_q_next_binary = 3'd0;
    if (analyzer_storage_cdc_graycounter1_ce) begin
        analyzer_storage_cdc_graycounter1_q_next_binary = (analyzer_storage_cdc_graycounter1_q_binary + 1'd1);
    end else begin
        analyzer_storage_cdc_graycounter1_q_next_binary = analyzer_storage_cdc_graycounter1_q_binary;
    end
end
assign analyzer_storage_cdc_graycounter1_q_next = (analyzer_storage_cdc_graycounter1_q_next_binary ^ analyzer_storage_cdc_graycounter1_q_next_binary[2:1]);
assign analyzer_storage_done1 = (analyzer_storage_count == 1'd0);
always @(*) begin
    analyzer_storage_cdc_sink_first = 1'd0;
    analyzer_storage_cdc_sink_last = 1'd0;
    analyzer_storage_cdc_sink_payload_data = 16'd0;
    analyzer_storage_cdc_sink_valid = 1'd0;
    analyzer_storage_done0 = 1'd0;
    analyzer_storage_flush = 1'd0;
    analyzer_storage_flush_read = 1'd0;
    analyzer_storage_mem_sink_first = 1'd0;
    analyzer_storage_mem_sink_last = 1'd0;
    analyzer_storage_mem_sink_payload_data = 16'd0;
    analyzer_storage_mem_sink_valid = 1'd0;
    analyzer_storage_mem_source_ready = 1'd0;
    analyzer_storage_post_hit = 1'd0;
    analyzer_storage_sink_sink_ready = 1'd0;
    analyzer_storage_wait = 1'd0;
    litescopeanalyzer_next_state = 2'd0;
    litescopeanalyzer_next_state = litescopeanalyzer_state;
    case (litescopeanalyzer_state)
        1'd1: begin
            analyzer_storage_sink_sink_ready = 1'd1;
            analyzer_storage_wait = 1'd1;
            analyzer_storage_mem_source_ready = 1'd1;
            analyzer_storage_flush_read = 1'd1;
            if (analyzer_storage_done1) begin
                litescopeanalyzer_next_state = 2'd2;
            end
        end
        2'd2: begin
            analyzer_storage_mem_sink_valid = analyzer_storage_sink_sink_valid;
            analyzer_storage_sink_sink_ready = analyzer_storage_mem_sink_ready;
            analyzer_storage_mem_sink_first = analyzer_storage_sink_sink_first;
            analyzer_storage_mem_sink_last = analyzer_storage_sink_sink_last;
            analyzer_storage_mem_sink_payload_data = analyzer_storage_sink_sink_payload_data;
            if ((analyzer_storage_sink_sink_valid & analyzer_storage_sink_sink_payload_hit)) begin
                litescopeanalyzer_next_state = 2'd3;
            end
            analyzer_storage_mem_source_ready = (analyzer_storage_mem_level1 >= analyzer_storage_offset);
        end
        2'd3: begin
            analyzer_storage_post_hit = 1'd1;
            analyzer_storage_flush = ((analyzer_storage_length != 1'd0) & ($signed({1'd0, analyzer_storage_mem_level1}) >= ($signed({1'd0, analyzer_storage_length}) - $signed({1'd0, 1'd1}))));
            if ((analyzer_storage_mem_level1 < analyzer_storage_length)) begin
                analyzer_storage_mem_sink_valid = analyzer_storage_sink_sink_valid;
                analyzer_storage_sink_sink_ready = analyzer_storage_mem_sink_ready;
                analyzer_storage_mem_sink_first = analyzer_storage_sink_sink_first;
                analyzer_storage_mem_sink_last = analyzer_storage_sink_sink_last;
                analyzer_storage_mem_sink_payload_data = analyzer_storage_sink_sink_payload_data;
            end
            if ((analyzer_storage_mem_level1 >= analyzer_storage_length)) begin
                litescopeanalyzer_next_state = 1'd0;
            end
        end
        default: begin
            analyzer_storage_done0 = 1'd1;
            if ((analyzer_storage_enable & (~analyzer_storage_enable_d))) begin
                litescopeanalyzer_next_state = 1'd1;
            end
            analyzer_storage_sink_sink_ready = 1'd1;
            analyzer_storage_cdc_sink_valid = analyzer_storage_mem_source_valid;
            analyzer_storage_mem_source_ready = analyzer_storage_cdc_sink_ready;
            analyzer_storage_cdc_sink_first = analyzer_storage_mem_source_first;
            analyzer_storage_cdc_sink_last = analyzer_storage_mem_source_last;
            analyzer_storage_cdc_sink_payload_data = analyzer_storage_mem_source_payload_data;
        end
    endcase
end
assign analyzer_trigger_sink_sink_valid = analyzer_mux_source_valid;
assign analyzer_mux_source_ready = analyzer_trigger_sink_sink_ready;
assign analyzer_trigger_sink_sink_first = analyzer_mux_source_first;
assign analyzer_trigger_sink_sink_last = analyzer_mux_source_last;
assign analyzer_trigger_sink_sink_payload_data = analyzer_mux_source_payload_data;
assign analyzer_trigger_sink_sink_payload_hit = analyzer_mux_source_payload_hit;
assign analyzer_subsampler_sink_valid = analyzer_trigger_source_source_valid;
assign analyzer_trigger_source_source_ready = analyzer_subsampler_sink_ready;
assign analyzer_subsampler_sink_first = analyzer_trigger_source_source_first;
assign analyzer_subsampler_sink_last = analyzer_trigger_source_source_last;
assign analyzer_subsampler_sink_payload_data = analyzer_trigger_source_source_payload_data;
assign analyzer_subsampler_sink_payload_hit = analyzer_trigger_source_source_payload_hit;
assign analyzer_storage_sink_sink_valid = analyzer_subsampler_source_valid;
assign analyzer_subsampler_source_ready = analyzer_storage_sink_sink_ready;
assign analyzer_storage_sink_sink_first = analyzer_subsampler_source_first;
assign analyzer_storage_sink_sink_last = analyzer_subsampler_source_last;
assign analyzer_storage_sink_sink_payload_data = analyzer_subsampler_source_payload_data;
assign analyzer_storage_sink_sink_payload_hit = analyzer_subsampler_source_payload_hit;
always @(*) begin
    csr_data_width = 1'd0;
    csr_data_width = 1'd0;
    if ((interface0_sel != 1'd0)) begin
        csr_data_width = 1'd0;
    end
end
always @(*) begin
    interface0_ack = 1'd0;
    interface0_dat_r = 32'd0;
    interface1_adr = 14'd0;
    interface1_dat_w = 32'd0;
    interface1_re = 1'd0;
    interface1_we = 1'd0;
    wishbone2csr_next_state = 1'd0;
    wishbone2csr_next_state = wishbone2csr_state;
    case (wishbone2csr_state)
        1'd1: begin
            interface0_ack = 1'd1;
            interface0_dat_r = 1'd0;
            case (csr_data_width)
                1'd0: begin
                    interface0_dat_r = interface1_dat_r;
                end
            endcase
            wishbone2csr_next_state = 1'd0;
        end
        default: begin
            interface1_dat_w = basiclowerer_self;
            if ((interface0_cyc & interface0_stb)) begin
                interface1_adr = interface0_adr;
                interface1_re = ((~interface0_we) & (interface0_sel != 1'd0));
                interface1_we = (interface0_we & (interface0_sel != 1'd0));
                wishbone2csr_next_state = 1'd1;
            end
        end
    endcase
end
assign csr_bankarray_csrbank0_sel = (csr_bankarray_interface0_bank_bus_adr[13:9] == 1'd0);
assign csr_bankarray_csrbank0_mux_value_r = csr_bankarray_interface0_bank_bus_dat_w[0];
always @(*) begin
    csr_bankarray_csrbank0_mux_value_re = 1'd0;
    csr_bankarray_csrbank0_mux_value_we = 1'd0;
    if ((csr_bankarray_csrbank0_sel & (csr_bankarray_interface0_bank_bus_adr[8:0] == 1'd0))) begin
        csr_bankarray_csrbank0_mux_value_re = csr_bankarray_interface0_bank_bus_we;
        csr_bankarray_csrbank0_mux_value_we = csr_bankarray_interface0_bank_bus_re;
    end
end
assign csr_bankarray_csrbank0_trigger_enable_r = csr_bankarray_interface0_bank_bus_dat_w[0];
always @(*) begin
    csr_bankarray_csrbank0_trigger_enable_re = 1'd0;
    csr_bankarray_csrbank0_trigger_enable_we = 1'd0;
    if ((csr_bankarray_csrbank0_sel & (csr_bankarray_interface0_bank_bus_adr[8:0] == 1'd1))) begin
        csr_bankarray_csrbank0_trigger_enable_re = csr_bankarray_interface0_bank_bus_we;
        csr_bankarray_csrbank0_trigger_enable_we = csr_bankarray_interface0_bank_bus_re;
    end
end
assign csr_bankarray_csrbank0_trigger_done_r = csr_bankarray_interface0_bank_bus_dat_w[0];
always @(*) begin
    csr_bankarray_csrbank0_trigger_done_re = 1'd0;
    csr_bankarray_csrbank0_trigger_done_we = 1'd0;
    if ((csr_bankarray_csrbank0_sel & (csr_bankarray_interface0_bank_bus_adr[8:0] == 2'd2))) begin
        csr_bankarray_csrbank0_trigger_done_re = csr_bankarray_interface0_bank_bus_we;
        csr_bankarray_csrbank0_trigger_done_we = csr_bankarray_interface0_bank_bus_re;
    end
end
assign analyzer_trigger_mem_write_r = csr_bankarray_interface0_bank_bus_dat_w[0];
always @(*) begin
    analyzer_trigger_mem_write_re = 1'd0;
    analyzer_trigger_mem_write_we = 1'd0;
    if ((csr_bankarray_csrbank0_sel & (csr_bankarray_interface0_bank_bus_adr[8:0] == 2'd3))) begin
        analyzer_trigger_mem_write_re = csr_bankarray_interface0_bank_bus_we;
        analyzer_trigger_mem_write_we = csr_bankarray_interface0_bank_bus_re;
    end
end
assign csr_bankarray_csrbank0_trigger_mem_mask_r = csr_bankarray_interface0_bank_bus_dat_w[15:0];
always @(*) begin
    csr_bankarray_csrbank0_trigger_mem_mask_re = 1'd0;
    csr_bankarray_csrbank0_trigger_mem_mask_we = 1'd0;
    if ((csr_bankarray_csrbank0_sel & (csr_bankarray_interface0_bank_bus_adr[8:0] == 3'd4))) begin
        csr_bankarray_csrbank0_trigger_mem_mask_re = csr_bankarray_interface0_bank_bus_we;
        csr_bankarray_csrbank0_trigger_mem_mask_we = csr_bankarray_interface0_bank_bus_re;
    end
end
assign csr_bankarray_csrbank0_trigger_mem_value_r = csr_bankarray_interface0_bank_bus_dat_w[15:0];
always @(*) begin
    csr_bankarray_csrbank0_trigger_mem_value_re = 1'd0;
    csr_bankarray_csrbank0_trigger_mem_value_we = 1'd0;
    if ((csr_bankarray_csrbank0_sel & (csr_bankarray_interface0_bank_bus_adr[8:0] == 3'd5))) begin
        csr_bankarray_csrbank0_trigger_mem_value_re = csr_bankarray_interface0_bank_bus_we;
        csr_bankarray_csrbank0_trigger_mem_value_we = csr_bankarray_interface0_bank_bus_re;
    end
end
assign csr_bankarray_csrbank0_trigger_mem_full_r = csr_bankarray_interface0_bank_bus_dat_w[0];
always @(*) begin
    csr_bankarray_csrbank0_trigger_mem_full_re = 1'd0;
    csr_bankarray_csrbank0_trigger_mem_full_we = 1'd0;
    if ((csr_bankarray_csrbank0_sel & (csr_bankarray_interface0_bank_bus_adr[8:0] == 3'd6))) begin
        csr_bankarray_csrbank0_trigger_mem_full_re = csr_bankarray_interface0_bank_bus_we;
        csr_bankarray_csrbank0_trigger_mem_full_we = csr_bankarray_interface0_bank_bus_re;
    end
end
assign csr_bankarray_csrbank0_subsampler_value_r = csr_bankarray_interface0_bank_bus_dat_w[15:0];
always @(*) begin
    csr_bankarray_csrbank0_subsampler_value_re = 1'd0;
    csr_bankarray_csrbank0_subsampler_value_we = 1'd0;
    if ((csr_bankarray_csrbank0_sel & (csr_bankarray_interface0_bank_bus_adr[8:0] == 3'd7))) begin
        csr_bankarray_csrbank0_subsampler_value_re = csr_bankarray_interface0_bank_bus_we;
        csr_bankarray_csrbank0_subsampler_value_we = csr_bankarray_interface0_bank_bus_re;
    end
end
assign csr_bankarray_csrbank0_storage_enable_r = csr_bankarray_interface0_bank_bus_dat_w[0];
always @(*) begin
    csr_bankarray_csrbank0_storage_enable_re = 1'd0;
    csr_bankarray_csrbank0_storage_enable_we = 1'd0;
    if ((csr_bankarray_csrbank0_sel & (csr_bankarray_interface0_bank_bus_adr[8:0] == 4'd8))) begin
        csr_bankarray_csrbank0_storage_enable_re = csr_bankarray_interface0_bank_bus_we;
        csr_bankarray_csrbank0_storage_enable_we = csr_bankarray_interface0_bank_bus_re;
    end
end
assign csr_bankarray_csrbank0_storage_done_r = csr_bankarray_interface0_bank_bus_dat_w[0];
always @(*) begin
    csr_bankarray_csrbank0_storage_done_re = 1'd0;
    csr_bankarray_csrbank0_storage_done_we = 1'd0;
    if ((csr_bankarray_csrbank0_sel & (csr_bankarray_interface0_bank_bus_adr[8:0] == 4'd9))) begin
        csr_bankarray_csrbank0_storage_done_re = csr_bankarray_interface0_bank_bus_we;
        csr_bankarray_csrbank0_storage_done_we = csr_bankarray_interface0_bank_bus_re;
    end
end
assign csr_bankarray_csrbank0_storage_length_r = csr_bankarray_interface0_bank_bus_dat_w[10:0];
always @(*) begin
    csr_bankarray_csrbank0_storage_length_re = 1'd0;
    csr_bankarray_csrbank0_storage_length_we = 1'd0;
    if ((csr_bankarray_csrbank0_sel & (csr_bankarray_interface0_bank_bus_adr[8:0] == 4'd10))) begin
        csr_bankarray_csrbank0_storage_length_re = csr_bankarray_interface0_bank_bus_we;
        csr_bankarray_csrbank0_storage_length_we = csr_bankarray_interface0_bank_bus_re;
    end
end
assign csr_bankarray_csrbank0_storage_offset_r = csr_bankarray_interface0_bank_bus_dat_w[10:0];
always @(*) begin
    csr_bankarray_csrbank0_storage_offset_re = 1'd0;
    csr_bankarray_csrbank0_storage_offset_we = 1'd0;
    if ((csr_bankarray_csrbank0_sel & (csr_bankarray_interface0_bank_bus_adr[8:0] == 4'd11))) begin
        csr_bankarray_csrbank0_storage_offset_re = csr_bankarray_interface0_bank_bus_we;
        csr_bankarray_csrbank0_storage_offset_we = csr_bankarray_interface0_bank_bus_re;
    end
end
assign csr_bankarray_csrbank0_storage_mem_level_r = csr_bankarray_interface0_bank_bus_dat_w[10:0];
always @(*) begin
    csr_bankarray_csrbank0_storage_mem_level_re = 1'd0;
    csr_bankarray_csrbank0_storage_mem_level_we = 1'd0;
    if ((csr_bankarray_csrbank0_sel & (csr_bankarray_interface0_bank_bus_adr[8:0] == 4'd12))) begin
        csr_bankarray_csrbank0_storage_mem_level_re = csr_bankarray_interface0_bank_bus_we;
        csr_bankarray_csrbank0_storage_mem_level_we = csr_bankarray_interface0_bank_bus_re;
    end
end
assign csr_bankarray_csrbank0_storage_mem_data_r = csr_bankarray_interface0_bank_bus_dat_w[15:0];
always @(*) begin
    csr_bankarray_csrbank0_storage_mem_data_re = 1'd0;
    csr_bankarray_csrbank0_storage_mem_data_we = 1'd0;
    if ((csr_bankarray_csrbank0_sel & (csr_bankarray_interface0_bank_bus_adr[8:0] == 4'd13))) begin
        csr_bankarray_csrbank0_storage_mem_data_re = csr_bankarray_interface0_bank_bus_we;
        csr_bankarray_csrbank0_storage_mem_data_we = csr_bankarray_interface0_bank_bus_re;
    end
end
assign csr_bankarray_csrbank0_mux_value_w = analyzer_mux_value_storage;
assign csr_bankarray_csrbank0_trigger_enable_w = analyzer_trigger_enable_storage;
assign csr_bankarray_csrbank0_trigger_done_w = analyzer_trigger_done_status;
assign analyzer_trigger_done_rd_stb = csr_bankarray_csrbank0_trigger_done_we;
assign csr_bankarray_csrbank0_trigger_mem_mask_w = analyzer_trigger_mem_mask_storage;
assign csr_bankarray_csrbank0_trigger_mem_value_w = analyzer_trigger_mem_value_storage;
assign csr_bankarray_csrbank0_trigger_mem_full_w = analyzer_trigger_mem_full_status;
assign analyzer_trigger_mem_full_rd_stb = csr_bankarray_csrbank0_trigger_mem_full_we;
assign csr_bankarray_csrbank0_subsampler_value_w = analyzer_subsampler_value_storage;
assign csr_bankarray_csrbank0_storage_enable_w = analyzer_storage_enable_storage;
assign csr_bankarray_csrbank0_storage_done_w = analyzer_storage_done_status;
assign analyzer_storage_done_rd_stb = csr_bankarray_csrbank0_storage_done_we;
assign csr_bankarray_csrbank0_storage_length_w = analyzer_storage_length_storage;
assign csr_bankarray_csrbank0_storage_offset_w = analyzer_storage_offset_storage;
assign csr_bankarray_csrbank0_storage_mem_level_w = analyzer_storage_mem_level_status;
assign analyzer_storage_mem_level_rd_stb = csr_bankarray_csrbank0_storage_mem_level_we;
assign csr_bankarray_csrbank0_storage_mem_data_w = analyzer_storage_mem_data_status;
assign analyzer_storage_mem_data_rd_stb = csr_bankarray_csrbank0_storage_mem_data_we;
assign csr_bankarray_csrbank1_sel = (csr_bankarray_interface1_bank_bus_adr[13:9] == 1'd1);
assign csr_bankarray_csrbank1_reset_r = csr_bankarray_interface1_bank_bus_dat_w[1:0];
always @(*) begin
    csr_bankarray_csrbank1_reset_re = 1'd0;
    csr_bankarray_csrbank1_reset_we = 1'd0;
    if ((csr_bankarray_csrbank1_sel & (csr_bankarray_interface1_bank_bus_adr[8:0] == 1'd0))) begin
        csr_bankarray_csrbank1_reset_re = csr_bankarray_interface1_bank_bus_we;
        csr_bankarray_csrbank1_reset_we = csr_bankarray_interface1_bank_bus_re;
    end
end
assign csr_bankarray_csrbank1_scratch_r = csr_bankarray_interface1_bank_bus_dat_w;
always @(*) begin
    csr_bankarray_csrbank1_scratch_re = 1'd0;
    csr_bankarray_csrbank1_scratch_we = 1'd0;
    if ((csr_bankarray_csrbank1_sel & (csr_bankarray_interface1_bank_bus_adr[8:0] == 1'd1))) begin
        csr_bankarray_csrbank1_scratch_re = csr_bankarray_interface1_bank_bus_we;
        csr_bankarray_csrbank1_scratch_we = csr_bankarray_interface1_bank_bus_re;
    end
end
assign csr_bankarray_csrbank1_bus_errors_r = csr_bankarray_interface1_bank_bus_dat_w;
always @(*) begin
    csr_bankarray_csrbank1_bus_errors_re = 1'd0;
    csr_bankarray_csrbank1_bus_errors_we = 1'd0;
    if ((csr_bankarray_csrbank1_sel & (csr_bankarray_interface1_bank_bus_adr[8:0] == 2'd2))) begin
        csr_bankarray_csrbank1_bus_errors_re = csr_bankarray_interface1_bank_bus_we;
        csr_bankarray_csrbank1_bus_errors_we = csr_bankarray_interface1_bank_bus_re;
    end
end
always @(*) begin
    soc_rst = 1'd0;
    if (reset_wr_stb) begin
        soc_rst = reset_storage[0];
    end
end
assign cpu_rst = reset_storage[1];
assign csr_bankarray_csrbank1_reset_w = reset_storage;
assign csr_bankarray_csrbank1_scratch_w = scratch_storage;
assign csr_bankarray_csrbank1_bus_errors_w = bus_errors_status;
assign bus_errors_rd_stb = csr_bankarray_csrbank1_bus_errors_we;
assign csr_bankarray_sel = (csr_bankarray_sram_bus_adr[13:9] == 2'd2);
always @(*) begin
    csr_bankarray_sram_bus_dat_r = 32'd0;
    if (csr_bankarray_sel_r) begin
        csr_bankarray_sram_bus_dat_r = csr_bankarray_dat_r;
    end
end
assign csr_bankarray_adr = csr_bankarray_sram_bus_adr[4:0];
assign csr_interconnect_adr = interface1_adr;
assign csr_interconnect_re = interface1_re;
assign csr_interconnect_we = interface1_we;
assign csr_interconnect_dat_w = interface1_dat_w;
assign interface1_dat_r = csr_interconnect_dat_r;
assign csr_bankarray_interface0_bank_bus_adr = csr_interconnect_adr;
assign csr_bankarray_interface1_bank_bus_adr = csr_interconnect_adr;
assign csr_bankarray_sram_bus_adr = csr_interconnect_adr;
assign csr_bankarray_interface0_bank_bus_re = csr_interconnect_re;
assign csr_bankarray_interface1_bank_bus_re = csr_interconnect_re;
assign csr_bankarray_sram_bus_re = csr_interconnect_re;
assign csr_bankarray_interface0_bank_bus_we = csr_interconnect_we;
assign csr_bankarray_interface1_bank_bus_we = csr_interconnect_we;
assign csr_bankarray_sram_bus_we = csr_interconnect_we;
assign csr_bankarray_interface0_bank_bus_dat_w = csr_interconnect_dat_w;
assign csr_bankarray_interface1_bank_bus_dat_w = csr_interconnect_dat_w;
assign csr_bankarray_sram_bus_dat_w = csr_interconnect_dat_w;
assign csr_interconnect_dat_r = ((csr_bankarray_interface0_bank_bus_dat_r | csr_bankarray_interface1_bank_bus_dat_r) | csr_bankarray_sram_bus_dat_r);
always @(*) begin
    rhs_self0 = 30'd0;
    case (grant)
        default: begin
            rhs_self0 = jtagbone_wishbone_adr;
        end
    endcase
end
always @(*) begin
    rhs_self1 = 32'd0;
    case (grant)
        default: begin
            rhs_self1 = jtagbone_wishbone_dat_w;
        end
    endcase
end
always @(*) begin
    rhs_self2 = 4'd0;
    case (grant)
        default: begin
            rhs_self2 = jtagbone_wishbone_sel;
        end
    endcase
end
always @(*) begin
    rhs_self3 = 1'd0;
    case (grant)
        default: begin
            rhs_self3 = jtagbone_wishbone_cyc;
        end
    endcase
end
always @(*) begin
    rhs_self4 = 1'd0;
    case (grant)
        default: begin
            rhs_self4 = jtagbone_wishbone_stb;
        end
    endcase
end
always @(*) begin
    rhs_self5 = 1'd0;
    case (grant)
        default: begin
            rhs_self5 = jtagbone_wishbone_we;
        end
    endcase
end
always @(*) begin
    rhs_self6 = 3'd0;
    case (grant)
        default: begin
            rhs_self6 = jtagbone_wishbone_cti;
        end
    endcase
end
always @(*) begin
    rhs_self7 = 2'd0;
    case (grant)
        default: begin
            rhs_self7 = jtagbone_wishbone_bte;
        end
    endcase
end
always @(*) begin
    basiclowerer_self = 32'd0;
    case (csr_data_width)
        default: begin
            basiclowerer_self = interface0_dat_w;
        end
    endcase
end
assign jtagbone_phy_tx_cdc_cdc_produce_rdomain = xilinxmultiregimpl01;
assign jtagbone_phy_tx_cdc_cdc_consume_wdomain = xilinxmultiregimpl11;
assign jtagbone_phy_rx_cdc_cdc_produce_rdomain = xilinxmultiregimpl21;
assign jtagbone_phy_rx_cdc_cdc_consume_wdomain = xilinxmultiregimpl31;
assign analyzer_mux_value = xilinxmultiregimpl41;
assign analyzer_trigger_enable = xilinxmultiregimpl51;
assign analyzer_trigger_done_status = xilinxmultiregimpl61;
assign analyzer_trigger_mem_produce_rdomain = xilinxmultiregimpl71;
assign analyzer_trigger_mem_consume_wdomain = xilinxmultiregimpl81;
assign analyzer_subsampler_value = xilinxmultiregimpl91;
assign analyzer_storage_enable = xilinxmultiregimpl101;
assign analyzer_storage_length = xilinxmultiregimpl111;
assign analyzer_storage_offset = xilinxmultiregimpl121;
assign analyzer_storage_done_status = xilinxmultiregimpl131;
assign analyzer_storage_mem_level_status = xilinxmultiregimpl141;
assign analyzer_storage_cdc_produce_rdomain = xilinxmultiregimpl151;
assign analyzer_storage_cdc_consume_wdomain = xilinxmultiregimpl161;
assign analyzer_storage_flush_read_sys = xilinxmultiregimpl171;



always @(posedge from242_clk) begin
    jtagbone_phy_rx_cdc_cdc_graycounter0_q_binary <= jtagbone_phy_rx_cdc_cdc_graycounter0_q_next_binary;
    jtagbone_phy_rx_cdc_cdc_graycounter0_q <= jtagbone_phy_rx_cdc_cdc_graycounter0_q_next;
    if (from242_rst) begin
        jtagbone_phy_rx_cdc_cdc_graycounter0_q <= 3'd0;
        jtagbone_phy_rx_cdc_cdc_graycounter0_q_binary <= 3'd0;
    end
    xilinxmultiregimpl30 <= jtagbone_phy_rx_cdc_cdc_graycounter1_q;
    xilinxmultiregimpl31 <= xilinxmultiregimpl30;
end

always @(posedge from91_clk) begin
    jtagbone_phy_tx_cdc_cdc_graycounter0_q_binary <= jtagbone_phy_tx_cdc_cdc_graycounter0_q_next_binary;
    jtagbone_phy_tx_cdc_cdc_graycounter0_q <= jtagbone_phy_tx_cdc_cdc_graycounter0_q_next;
    if (from91_rst) begin
        jtagbone_phy_tx_cdc_cdc_graycounter0_q <= 3'd0;
        jtagbone_phy_tx_cdc_cdc_graycounter0_q_binary <= 3'd0;
    end
    xilinxmultiregimpl10 <= jtagbone_phy_tx_cdc_cdc_graycounter1_q;
    xilinxmultiregimpl11 <= xilinxmultiregimpl10;
end

always @(posedge jtag_clk) begin
    jtagbone_phy_shift_d <= (jtagbone_phy_jtag_shift & jtagbone_phy_jtag_sel);
    if (jtagbone_phy_update_ready) begin
        jtagbone_phy_ready <= jtagbone_phy_rx_cdc_sink_sink_ready;
    end
    if (jtagbone_phy_update_rx) begin
        jtagbone_phy_rx_valid <= jtagbone_phy_rx_valid_in;
        jtagbone_phy_rx_data <= jtagbone_phy_data;
    end else begin
        if ((jtagbone_phy_rx_cdc_sink_sink_valid & jtagbone_phy_rx_cdc_sink_sink_ready)) begin
            jtagbone_phy_rx_valid <= 1'd0;
        end
    end
    jtagphy_state <= jtagphy_next_state;
    if (jtagbone_phy_valid_jtagphy_next_value_ce0) begin
        jtagbone_phy_valid <= jtagbone_phy_valid_jtagphy_next_value0;
    end
    if (jtagbone_phy_data_jtagphy_next_value_ce1) begin
        jtagbone_phy_data <= jtagbone_phy_data_jtagphy_next_value1;
    end
    if (jtagbone_phy_count_jtagphy_next_value_ce2) begin
        jtagbone_phy_count <= jtagbone_phy_count_jtagphy_next_value2;
    end
    if (jtagbone_phy_rx_valid_in_jtagphy_next_value_ce3) begin
        jtagbone_phy_rx_valid_in <= jtagbone_phy_rx_valid_in_jtagphy_next_value3;
    end
    if (jtagbone_phy_fsm_reset) begin
        jtagbone_phy_valid <= 1'd0;
        jtagbone_phy_data <= 8'd0;
        jtagbone_phy_count <= 3'd0;
        jtagbone_phy_rx_valid_in <= 1'd0;
        jtagphy_state <= 2'd0;
    end
    if (jtag_rst) begin
        jtagbone_phy_valid <= 1'd0;
        jtagbone_phy_data <= 8'd0;
        jtagbone_phy_count <= 3'd0;
        jtagbone_phy_rx_valid <= 1'd0;
        jtagbone_phy_rx_data <= 8'd0;
        jtagbone_phy_rx_valid_in <= 1'd0;
        jtagbone_phy_ready <= 1'd0;
        jtagbone_phy_shift_d <= 1'd0;
        jtagphy_state <= 2'd0;
    end
end

always @(posedge scope_clk) begin
    analyzer_trigger_enable_d <= analyzer_trigger_enable;
    analyzer_trigger_sink_d_valid <= analyzer_trigger_sink_sink_valid;
    analyzer_trigger_sink_d_payload_data <= analyzer_trigger_sink_sink_payload_data;
    if (((~analyzer_trigger_enable) & analyzer_trigger_enable_d)) begin
        analyzer_trigger_flushing <= 1'd1;
    end else begin
        if ((~analyzer_trigger_mem_source_valid)) begin
            analyzer_trigger_flushing <= 1'd0;
        end
    end
    if ((analyzer_trigger_mem_re | (~analyzer_trigger_mem_readable))) begin
        analyzer_trigger_mem_dout <= analyzer_trigger_mem_asyncfifo_dout;
        analyzer_trigger_mem_readable <= analyzer_trigger_mem_asyncfifo_readable;
    end
    analyzer_trigger_mem_graycounter1_q_binary <= analyzer_trigger_mem_graycounter1_q_next_binary;
    analyzer_trigger_mem_graycounter1_q <= analyzer_trigger_mem_graycounter1_q_next;
    if (analyzer_subsampler_source_ready) begin
        if (analyzer_subsampler_done) begin
            analyzer_subsampler_counter <= 1'd0;
        end else begin
            if (analyzer_subsampler_sink_valid) begin
                analyzer_subsampler_counter <= (analyzer_subsampler_counter + 1'd1);
            end
        end
    end
    analyzer_storage_enable_d <= analyzer_storage_enable;
    if (analyzer_storage_mem_syncfifo_re) begin
        analyzer_storage_mem_readable <= 1'd1;
    end else begin
        if (analyzer_storage_mem_re) begin
            analyzer_storage_mem_readable <= 1'd0;
        end
    end
    if (((analyzer_storage_mem_syncfifo_we & analyzer_storage_mem_syncfifo_writable) & (~analyzer_storage_mem_replace))) begin
        analyzer_storage_mem_produce <= (analyzer_storage_mem_produce + 1'd1);
    end
    if (analyzer_storage_mem_do_read) begin
        analyzer_storage_mem_consume <= (analyzer_storage_mem_consume + 1'd1);
    end
    if (((analyzer_storage_mem_syncfifo_we & analyzer_storage_mem_syncfifo_writable) & (~analyzer_storage_mem_replace))) begin
        if ((~analyzer_storage_mem_do_read)) begin
            analyzer_storage_mem_level0 <= (analyzer_storage_mem_level0 + 1'd1);
        end
    end else begin
        if (analyzer_storage_mem_do_read) begin
            analyzer_storage_mem_level0 <= (analyzer_storage_mem_level0 - 1'd1);
        end
    end
    analyzer_storage_cdc_graycounter0_q_binary <= analyzer_storage_cdc_graycounter0_q_next_binary;
    analyzer_storage_cdc_graycounter0_q <= analyzer_storage_cdc_graycounter0_q_next;
    if (analyzer_storage_wait) begin
        if ((~analyzer_storage_done1)) begin
            analyzer_storage_count <= (analyzer_storage_count - 1'd1);
        end
    end else begin
        analyzer_storage_count <= 11'h400;
    end
    litescopeanalyzer_state <= litescopeanalyzer_next_state;
    if (scope_rst) begin
        analyzer_trigger_enable_d <= 1'd0;
        analyzer_trigger_mem_readable <= 1'd0;
        analyzer_trigger_mem_graycounter1_q <= 5'd0;
        analyzer_trigger_mem_graycounter1_q_binary <= 5'd0;
        analyzer_trigger_sink_d_valid <= 1'd0;
        analyzer_trigger_flushing <= 1'd0;
        analyzer_subsampler_counter <= 16'd0;
        analyzer_storage_enable_d <= 1'd0;
        analyzer_storage_mem_readable <= 1'd0;
        analyzer_storage_mem_level0 <= 11'd0;
        analyzer_storage_mem_produce <= 10'd0;
        analyzer_storage_mem_consume <= 10'd0;
        analyzer_storage_cdc_graycounter0_q <= 3'd0;
        analyzer_storage_cdc_graycounter0_q_binary <= 3'd0;
        analyzer_storage_count <= 11'h400;
        litescopeanalyzer_state <= 2'd0;
    end
    xilinxmultiregimpl40 <= analyzer_mux_value_storage;
    xilinxmultiregimpl41 <= xilinxmultiregimpl40;
    xilinxmultiregimpl50 <= analyzer_trigger_enable_storage;
    xilinxmultiregimpl51 <= xilinxmultiregimpl50;
    xilinxmultiregimpl70 <= analyzer_trigger_mem_graycounter0_q;
    xilinxmultiregimpl71 <= xilinxmultiregimpl70;
    xilinxmultiregimpl90 <= analyzer_subsampler_value_storage;
    xilinxmultiregimpl91 <= xilinxmultiregimpl90;
    xilinxmultiregimpl100 <= analyzer_storage_enable_storage;
    xilinxmultiregimpl101 <= xilinxmultiregimpl100;
    xilinxmultiregimpl110 <= analyzer_storage_length_storage;
    xilinxmultiregimpl111 <= xilinxmultiregimpl110;
    xilinxmultiregimpl120 <= analyzer_storage_offset_storage;
    xilinxmultiregimpl121 <= xilinxmultiregimpl120;
    xilinxmultiregimpl160 <= analyzer_storage_cdc_graycounter1_q;
    xilinxmultiregimpl161 <= xilinxmultiregimpl160;
end

always @(posedge sys_clk) begin
    slave_sel_r <= slave_sel;
    if (wait_1) begin
        if ((~done)) begin
            count <= (count - 1'd1);
        end
    end else begin
        count <= 20'd1000000;
    end
    if ((bus_errors != 32'hffffffff)) begin
        if (bus_error) begin
            bus_errors <= (bus_errors + 1'd1);
        end
    end
    resetinserter_state <= resetinserter_next_state;
    if (jtagbone_data_bytes_count_resetinserter_next_value_ce0) begin
        jtagbone_data_bytes_count <= jtagbone_data_bytes_count_resetinserter_next_value0;
    end
    if (jtagbone_addr_bytes_count_resetinserter_next_value_ce1) begin
        jtagbone_addr_bytes_count <= jtagbone_addr_bytes_count_resetinserter_next_value1;
    end
    if (jtagbone_words_count_resetinserter_next_value_ce2) begin
        jtagbone_words_count <= jtagbone_words_count_resetinserter_next_value2;
    end
    if (jtagbone_cmd_resetinserter_next_value_ce3) begin
        jtagbone_cmd <= jtagbone_cmd_resetinserter_next_value3;
    end
    if (jtagbone_length_resetinserter_next_value_ce4) begin
        jtagbone_length <= jtagbone_length_resetinserter_next_value4;
    end
    if (jtagbone_address_resetinserter_next_value_ce5) begin
        jtagbone_address <= jtagbone_address_resetinserter_next_value5;
    end
    if (jtagbone_incr_resetinserter_next_value_ce6) begin
        jtagbone_incr <= jtagbone_incr_resetinserter_next_value6;
    end
    if (jtagbone_data_resetinserter_next_value_ce7) begin
        jtagbone_data <= jtagbone_data_resetinserter_next_value7;
    end
    if (jtagbone_reset) begin
        jtagbone_incr <= 1'd0;
        resetinserter_state <= 3'd0;
    end
    if (jtagbone_wait) begin
        if ((~jtagbone_done)) begin
            jtagbone_count <= (jtagbone_count - 1'd1);
        end
    end else begin
        jtagbone_count <= 24'd10000000;
    end
    analyzer_trigger_mem_graycounter0_q_binary <= analyzer_trigger_mem_graycounter0_q_next_binary;
    analyzer_trigger_mem_graycounter0_q <= analyzer_trigger_mem_graycounter0_q_next;
    analyzer_storage_cdc_graycounter1_q_binary <= analyzer_storage_cdc_graycounter1_q_next_binary;
    analyzer_storage_cdc_graycounter1_q <= analyzer_storage_cdc_graycounter1_q_next;
    wishbone2csr_state <= wishbone2csr_next_state;
    csr_bankarray_interface0_bank_bus_dat_r <= 1'd0;
    if (csr_bankarray_csrbank0_sel) begin
        case (csr_bankarray_interface0_bank_bus_adr[8:0])
            1'd0: begin
                csr_bankarray_interface0_bank_bus_dat_r <= csr_bankarray_csrbank0_mux_value_w;
            end
            1'd1: begin
                csr_bankarray_interface0_bank_bus_dat_r <= csr_bankarray_csrbank0_trigger_enable_w;
            end
            2'd2: begin
                csr_bankarray_interface0_bank_bus_dat_r <= csr_bankarray_csrbank0_trigger_done_w;
            end
            2'd3: begin
                csr_bankarray_interface0_bank_bus_dat_r <= analyzer_trigger_mem_write_w;
            end
            3'd4: begin
                csr_bankarray_interface0_bank_bus_dat_r <= csr_bankarray_csrbank0_trigger_mem_mask_w;
            end
            3'd5: begin
                csr_bankarray_interface0_bank_bus_dat_r <= csr_bankarray_csrbank0_trigger_mem_value_w;
            end
            3'd6: begin
                csr_bankarray_interface0_bank_bus_dat_r <= csr_bankarray_csrbank0_trigger_mem_full_w;
            end
            3'd7: begin
                csr_bankarray_interface0_bank_bus_dat_r <= csr_bankarray_csrbank0_subsampler_value_w;
            end
            4'd8: begin
                csr_bankarray_interface0_bank_bus_dat_r <= csr_bankarray_csrbank0_storage_enable_w;
            end
            4'd9: begin
                csr_bankarray_interface0_bank_bus_dat_r <= csr_bankarray_csrbank0_storage_done_w;
            end
            4'd10: begin
                csr_bankarray_interface0_bank_bus_dat_r <= csr_bankarray_csrbank0_storage_length_w;
            end
            4'd11: begin
                csr_bankarray_interface0_bank_bus_dat_r <= csr_bankarray_csrbank0_storage_offset_w;
            end
            4'd12: begin
                csr_bankarray_interface0_bank_bus_dat_r <= csr_bankarray_csrbank0_storage_mem_level_w;
            end
            4'd13: begin
                csr_bankarray_interface0_bank_bus_dat_r <= csr_bankarray_csrbank0_storage_mem_data_w;
            end
        endcase
    end
    if (csr_bankarray_csrbank0_mux_value_re) begin
        analyzer_mux_value_storage <= csr_bankarray_csrbank0_mux_value_r;
    end
    analyzer_mux_value_wr_stb <= csr_bankarray_csrbank0_mux_value_re;
    if (csr_bankarray_csrbank0_trigger_enable_re) begin
        analyzer_trigger_enable_storage <= csr_bankarray_csrbank0_trigger_enable_r;
    end
    analyzer_trigger_enable_wr_stb <= csr_bankarray_csrbank0_trigger_enable_re;
    analyzer_trigger_done_wr_stb <= csr_bankarray_csrbank0_trigger_done_re;
    if (csr_bankarray_csrbank0_trigger_mem_mask_re) begin
        analyzer_trigger_mem_mask_storage <= csr_bankarray_csrbank0_trigger_mem_mask_r;
    end
    analyzer_trigger_mem_mask_wr_stb <= csr_bankarray_csrbank0_trigger_mem_mask_re;
    if (csr_bankarray_csrbank0_trigger_mem_value_re) begin
        analyzer_trigger_mem_value_storage <= csr_bankarray_csrbank0_trigger_mem_value_r;
    end
    analyzer_trigger_mem_value_wr_stb <= csr_bankarray_csrbank0_trigger_mem_value_re;
    analyzer_trigger_mem_full_wr_stb <= csr_bankarray_csrbank0_trigger_mem_full_re;
    if (csr_bankarray_csrbank0_subsampler_value_re) begin
        analyzer_subsampler_value_storage <= csr_bankarray_csrbank0_subsampler_value_r;
    end
    analyzer_subsampler_value_wr_stb <= csr_bankarray_csrbank0_subsampler_value_re;
    if (csr_bankarray_csrbank0_storage_enable_re) begin
        analyzer_storage_enable_storage <= csr_bankarray_csrbank0_storage_enable_r;
    end
    analyzer_storage_enable_wr_stb <= csr_bankarray_csrbank0_storage_enable_re;
    analyzer_storage_done_wr_stb <= csr_bankarray_csrbank0_storage_done_re;
    if (csr_bankarray_csrbank0_storage_length_re) begin
        analyzer_storage_length_storage <= csr_bankarray_csrbank0_storage_length_r;
    end
    analyzer_storage_length_wr_stb <= csr_bankarray_csrbank0_storage_length_re;
    if (csr_bankarray_csrbank0_storage_offset_re) begin
        analyzer_storage_offset_storage <= csr_bankarray_csrbank0_storage_offset_r;
    end
    analyzer_storage_offset_wr_stb <= csr_bankarray_csrbank0_storage_offset_re;
    analyzer_storage_mem_level_wr_stb <= csr_bankarray_csrbank0_storage_mem_level_re;
    analyzer_storage_mem_data_wr_stb <= csr_bankarray_csrbank0_storage_mem_data_re;
    csr_bankarray_interface1_bank_bus_dat_r <= 1'd0;
    if (csr_bankarray_csrbank1_sel) begin
        case (csr_bankarray_interface1_bank_bus_adr[8:0])
            1'd0: begin
                csr_bankarray_interface1_bank_bus_dat_r <= csr_bankarray_csrbank1_reset_w;
            end
            1'd1: begin
                csr_bankarray_interface1_bank_bus_dat_r <= csr_bankarray_csrbank1_scratch_w;
            end
            2'd2: begin
                csr_bankarray_interface1_bank_bus_dat_r <= csr_bankarray_csrbank1_bus_errors_w;
            end
        endcase
    end
    if (csr_bankarray_csrbank1_reset_re) begin
        reset_storage <= csr_bankarray_csrbank1_reset_r;
    end
    reset_wr_stb <= csr_bankarray_csrbank1_reset_re;
    if (csr_bankarray_csrbank1_scratch_re) begin
        scratch_storage <= csr_bankarray_csrbank1_scratch_r;
    end
    scratch_wr_stb <= csr_bankarray_csrbank1_scratch_re;
    bus_errors_wr_stb <= csr_bankarray_csrbank1_bus_errors_re;
    csr_bankarray_sel_r <= csr_bankarray_sel;
    if (sys_rst) begin
        reset_storage <= 2'd0;
        reset_wr_stb <= 1'd0;
        scratch_storage <= 32'd305419896;
        scratch_wr_stb <= 1'd0;
        bus_errors_wr_stb <= 1'd0;
        bus_errors <= 32'd0;
        jtagbone_incr <= 1'd0;
        jtagbone_count <= 24'd10000000;
        analyzer_mux_value_storage <= 1'd0;
        analyzer_mux_value_wr_stb <= 1'd0;
        analyzer_trigger_enable_storage <= 1'd0;
        analyzer_trigger_enable_wr_stb <= 1'd0;
        analyzer_trigger_done_wr_stb <= 1'd0;
        analyzer_trigger_mem_mask_storage <= 16'd0;
        analyzer_trigger_mem_mask_wr_stb <= 1'd0;
        analyzer_trigger_mem_value_storage <= 16'd0;
        analyzer_trigger_mem_value_wr_stb <= 1'd0;
        analyzer_trigger_mem_full_wr_stb <= 1'd0;
        analyzer_trigger_mem_graycounter0_q <= 5'd0;
        analyzer_trigger_mem_graycounter0_q_binary <= 5'd0;
        analyzer_subsampler_value_storage <= 16'd0;
        analyzer_subsampler_value_wr_stb <= 1'd0;
        analyzer_storage_enable_storage <= 1'd0;
        analyzer_storage_enable_wr_stb <= 1'd0;
        analyzer_storage_done_wr_stb <= 1'd0;
        analyzer_storage_length_storage <= 11'd0;
        analyzer_storage_length_wr_stb <= 1'd0;
        analyzer_storage_offset_storage <= 11'd0;
        analyzer_storage_offset_wr_stb <= 1'd0;
        analyzer_storage_mem_level_wr_stb <= 1'd0;
        analyzer_storage_mem_data_wr_stb <= 1'd0;
        analyzer_storage_cdc_graycounter1_q <= 3'd0;
        analyzer_storage_cdc_graycounter1_q_binary <= 3'd0;
        slave_sel_r <= 1'd0;
        count <= 20'd1000000;
        csr_bankarray_sel_r <= 1'd0;
        resetinserter_state <= 3'd0;
        wishbone2csr_state <= 1'd0;
    end
    xilinxmultiregimpl60 <= analyzer_trigger_done;
    xilinxmultiregimpl61 <= xilinxmultiregimpl60;
    xilinxmultiregimpl80 <= analyzer_trigger_mem_graycounter1_q;
    xilinxmultiregimpl81 <= xilinxmultiregimpl80;
    xilinxmultiregimpl130 <= analyzer_storage_done0;
    xilinxmultiregimpl131 <= xilinxmultiregimpl130;
    xilinxmultiregimpl140 <= analyzer_storage_level;
    xilinxmultiregimpl141 <= xilinxmultiregimpl140;
    xilinxmultiregimpl150 <= analyzer_storage_cdc_graycounter0_q;
    xilinxmultiregimpl151 <= xilinxmultiregimpl150;
    xilinxmultiregimpl170 <= analyzer_storage_flush_read;
    xilinxmultiregimpl171 <= xilinxmultiregimpl170;
end

always @(posedge to242_clk) begin
    jtagbone_phy_rx_cdc_cdc_graycounter1_q_binary <= jtagbone_phy_rx_cdc_cdc_graycounter1_q_next_binary;
    jtagbone_phy_rx_cdc_cdc_graycounter1_q <= jtagbone_phy_rx_cdc_cdc_graycounter1_q_next;
    if (to242_rst) begin
        jtagbone_phy_rx_cdc_cdc_graycounter1_q <= 3'd0;
        jtagbone_phy_rx_cdc_cdc_graycounter1_q_binary <= 3'd0;
    end
    xilinxmultiregimpl20 <= jtagbone_phy_rx_cdc_cdc_graycounter0_q;
    xilinxmultiregimpl21 <= xilinxmultiregimpl20;
end

always @(posedge to91_clk) begin
    jtagbone_phy_tx_cdc_cdc_graycounter1_q_binary <= jtagbone_phy_tx_cdc_cdc_graycounter1_q_next_binary;
    jtagbone_phy_tx_cdc_cdc_graycounter1_q <= jtagbone_phy_tx_cdc_cdc_graycounter1_q_next;
    if (to91_rst) begin
        jtagbone_phy_tx_cdc_cdc_graycounter1_q <= 3'd0;
        jtagbone_phy_tx_cdc_cdc_graycounter1_q_binary <= 3'd0;
    end
    xilinxmultiregimpl00 <= jtagbone_phy_tx_cdc_cdc_graycounter0_q;
    xilinxmultiregimpl01 <= xilinxmultiregimpl00;
end



reg [7:0] mem[0:29];
initial begin
	$readmemh("scope_core_mem.init", mem);
end
reg [7:0] mem_dat0;
always @(posedge sys_clk) begin
	mem_dat0 <= mem[csr_bankarray_adr];
end
assign csr_bankarray_dat_r = mem_dat0;


BSCANE2 #(
	.JTAG_CHAIN (1'd1)
) BSCANE2 (
	.TDO     (jtagbone_phy_jtag_tdo),

	.CAPTURE (jtagbone_phy_jtag_capture),
	.RESET   (jtagbone_phy_jtag_reset),
	.SEL     (jtagbone_phy_jtag_sel),
	.SHIFT   (jtagbone_phy_jtag_shift),
	.TCK     (jtagbone_phy_jtag_tck),
	.TDI     (jtagbone_phy_jtag_tdi),
	.TMS     (jtagbone_phy_jtag_tms),
	.UPDATE  (jtagbone_phy_jtag_update)
);

reg [9:0] storage[0:3];
reg [9:0] storage_dat0;
reg [9:0] storage_dat1;
always @(posedge from91_clk) begin
	if (jtagbone_phy_tx_cdc_cdc_wrport_we)
		storage[jtagbone_phy_tx_cdc_cdc_wrport_adr] <= jtagbone_phy_tx_cdc_cdc_wrport_dat_w;
	storage_dat0 <= storage[jtagbone_phy_tx_cdc_cdc_wrport_adr];
end
always @(posedge to91_clk) begin
	storage_dat1 <= storage[jtagbone_phy_tx_cdc_cdc_rdport_adr];
end
assign jtagbone_phy_tx_cdc_cdc_wrport_dat_r = storage_dat0;
assign jtagbone_phy_tx_cdc_cdc_rdport_dat_r = storage_dat1;


reg [9:0] storage_1[0:3];
reg [9:0] storage_1_dat0;
reg [9:0] storage_1_dat1;
always @(posedge from242_clk) begin
	if (jtagbone_phy_rx_cdc_cdc_wrport_we)
		storage_1[jtagbone_phy_rx_cdc_cdc_wrport_adr] <= jtagbone_phy_rx_cdc_cdc_wrport_dat_w;
	storage_1_dat0 <= storage_1[jtagbone_phy_rx_cdc_cdc_wrport_adr];
end
always @(posedge to242_clk) begin
	storage_1_dat1 <= storage_1[jtagbone_phy_rx_cdc_cdc_rdport_adr];
end
assign jtagbone_phy_rx_cdc_cdc_wrport_dat_r = storage_1_dat0;
assign jtagbone_phy_rx_cdc_cdc_rdport_dat_r = storage_1_dat1;


reg [33:0] storage_2[0:15];
reg [33:0] storage_2_dat0;
reg [33:0] storage_2_dat1;
always @(posedge sys_clk) begin
	if (analyzer_trigger_mem_wrport_we)
		storage_2[analyzer_trigger_mem_wrport_adr] <= analyzer_trigger_mem_wrport_dat_w;
	storage_2_dat0 <= storage_2[analyzer_trigger_mem_wrport_adr];
end
always @(posedge scope_clk) begin
	storage_2_dat1 <= storage_2[analyzer_trigger_mem_rdport_adr];
end
assign analyzer_trigger_mem_wrport_dat_r = storage_2_dat0;
assign analyzer_trigger_mem_rdport_dat_r = storage_2_dat1;


reg [17:0] storage_3[0:1023];
reg [17:0] storage_3_dat0;
reg [17:0] storage_3_dat1;
always @(posedge scope_clk) begin
	if (analyzer_storage_mem_wrport_we)
		storage_3[analyzer_storage_mem_wrport_adr] <= analyzer_storage_mem_wrport_dat_w;
	storage_3_dat0 <= storage_3[analyzer_storage_mem_wrport_adr];
end
always @(posedge scope_clk) begin
	if (analyzer_storage_mem_rdport_re) begin
		storage_3_dat1 <= storage_3[analyzer_storage_mem_rdport_adr];
	end
end
assign analyzer_storage_mem_wrport_dat_r = storage_3_dat0;
assign analyzer_storage_mem_rdport_dat_r = storage_3_dat1;


reg [17:0] storage_4[0:3];
reg [17:0] storage_4_dat0;
reg [17:0] storage_4_dat1;
always @(posedge scope_clk) begin
	if (analyzer_storage_cdc_wrport_we)
		storage_4[analyzer_storage_cdc_wrport_adr] <= analyzer_storage_cdc_wrport_dat_w;
	storage_4_dat0 <= storage_4[analyzer_storage_cdc_wrport_adr];
end
always @(posedge sys_clk) begin
	storage_4_dat1 <= storage_4[analyzer_storage_cdc_rdport_adr];
end
assign analyzer_storage_cdc_wrport_dat_r = storage_4_dat0;
assign analyzer_storage_cdc_rdport_dat_r = storage_4_dat1;


(* ars_ff1 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE (
	.C   (jtag_clk),
	.CE  (1'd1),
	.D   (1'd0),
	.PRE (sys_rst),

	.Q   (rst_meta0)
);

(* ars_ff2 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_1 (
	.C   (jtag_clk),
	.CE  (1'd1),
	.D   (rst_meta0),
	.PRE (sys_rst),

	.Q   (jtag_rst)
);

(* ars_ff1 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_2 (
	.C   (from91_clk),
	.CE  (1'd1),
	.D   (1'd0),
	.PRE (jtagbone_phy_tx_cdc_cd_rst),

	.Q   (rst_meta1)
);

(* ars_ff2 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_3 (
	.C   (from91_clk),
	.CE  (1'd1),
	.D   (rst_meta1),
	.PRE (jtagbone_phy_tx_cdc_cd_rst),

	.Q   (from91_rst)
);

(* ars_ff1 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_4 (
	.C   (to91_clk),
	.CE  (1'd1),
	.D   (1'd0),
	.PRE (jtagbone_phy_tx_cdc_cd_rst),

	.Q   (rst_meta2)
);

(* ars_ff2 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_5 (
	.C   (to91_clk),
	.CE  (1'd1),
	.D   (rst_meta2),
	.PRE (jtagbone_phy_tx_cdc_cd_rst),

	.Q   (to91_rst)
);

(* ars_ff1 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_6 (
	.C   (from242_clk),
	.CE  (1'd1),
	.D   (1'd0),
	.PRE (jtagbone_phy_rx_cdc_cd_rst),

	.Q   (rst_meta3)
);

(* ars_ff2 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_7 (
	.C   (from242_clk),
	.CE  (1'd1),
	.D   (rst_meta3),
	.PRE (jtagbone_phy_rx_cdc_cd_rst),

	.Q   (from242_rst)
);

(* ars_ff1 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_8 (
	.C   (to242_clk),
	.CE  (1'd1),
	.D   (1'd0),
	.PRE (jtagbone_phy_rx_cdc_cd_rst),

	.Q   (rst_meta4)
);

(* ars_ff2 = "true", async_reg = "true" *)
FDPE #(
	.INIT (1'd1)
) FDPE_9 (
	.C   (to242_clk),
	.CE  (1'd1),
	.D   (rst_meta4),
	.PRE (jtagbone_phy_rx_cdc_cd_rst),

	.Q   (to242_rst)
);

endmodule

