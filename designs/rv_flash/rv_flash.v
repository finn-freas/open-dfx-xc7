module rv_flash #(
    parameter MEM_INIT = "designs/rv_flash/fw/main.hex",
    parameter MEM_WORDS = 2048,
    parameter CLKS_PER_BIT = 100,
    parameter TIMEOUT = 64,
    parameter FENCE = 64,
    parameter SPI_DIV = 2,
    parameter SCK_STARTUPE2 = 0
) (
    input wire clk, input wire uart_txd_in, output wire uart_rxd_out, output wire [3:0] led,
    output wire qspi_cs, output wire qspi_sck, output wire qspi_dq0, input wire qspi_dq1,
    output wire qspi_dq2, output wire qspi_dq3
);
    reg [5:0] por = 6'd0;
    wire resetn = &por;
    always @(posedge clk) if (!resetn) por <= por + 6'd1;

    wire mem_valid, mem_instr, trap;
    wire [31:0] mem_addr, mem_wdata;
    wire [3:0] mem_wstrb;
    wire [31:0] mem_rdata;
    reg ram_ready = 1'b0, io_ready = 1'b0;
    wire mem_ready = ram_ready | io_ready;

    wire pcpi_valid, pcpi_wr, pcpi_wait, pcpi_ready;
    wire [31:0] pcpi_insn, pcpi_rs1, pcpi_rs2, pcpi_rd;

    picorv32 #(
        .ENABLE_COUNTERS(0), .ENABLE_COUNTERS64(0), .ENABLE_REGS_16_31(1), .ENABLE_REGS_DUALPORT(1),
        .LATCHED_MEM_RDATA(0), .TWO_STAGE_SHIFT(0), .BARREL_SHIFTER(0), .TWO_CYCLE_COMPARE(0), .TWO_CYCLE_ALU(0),
        .COMPRESSED_ISA(0), .CATCH_MISALIGN(0), .CATCH_ILLINSN(1),
        .ENABLE_PCPI(1), .ENABLE_MUL(0), .ENABLE_FAST_MUL(0), .ENABLE_DIV(0), .ENABLE_IRQ(0), .ENABLE_TRACE(0),
        .PROGADDR_RESET(32'h0000_0000)
    ) u_cpu (
        .clk(clk), .resetn(resetn), .trap(trap),
        .mem_valid(mem_valid), .mem_instr(mem_instr), .mem_ready(mem_ready),
        .mem_addr(mem_addr), .mem_wdata(mem_wdata), .mem_wstrb(mem_wstrb), .mem_rdata(mem_rdata),
        .mem_la_read(), .mem_la_write(), .mem_la_addr(), .mem_la_wdata(), .mem_la_wstrb(),
        .pcpi_valid(pcpi_valid), .pcpi_insn(pcpi_insn), .pcpi_rs1(pcpi_rs1), .pcpi_rs2(pcpi_rs2),
        .pcpi_wr(pcpi_wr), .pcpi_rd(pcpi_rd), .pcpi_wait(pcpi_wait), .pcpi_ready(pcpi_ready),
        .irq(32'd0), .eoi(), .trace_valid(), .trace_data()
    );

    wire slot_valid, slot_ready;
    wire [9:0] slot_funct;
    wire [31:0] slot_rs1, slot_rs2, slot_rd;
    wire [15:0] slot_timeouts, slot_late;
    rm_bridge_fenced #(.TIMEOUT(TIMEOUT), .FENCE(FENCE)) u_bridge (
        .clk(clk), .resetn(resetn),
        .pcpi_valid(pcpi_valid), .pcpi_insn(pcpi_insn), .pcpi_rs1(pcpi_rs1), .pcpi_rs2(pcpi_rs2),
        .pcpi_wr(pcpi_wr), .pcpi_rd(pcpi_rd), .pcpi_wait(pcpi_wait), .pcpi_ready(pcpi_ready),
        .slot_valid(slot_valid), .slot_funct(slot_funct), .slot_rs1(slot_rs1), .slot_rs2(slot_rs2),
        .slot_rd(slot_rd), .slot_ready(slot_ready), .timeouts(slot_timeouts), .late_answers(slot_late)
    );
    reg decouple_r = 1'b0;
    wire decouple_status;
    wire rp_valid, rp_ready;
    wire [9:0] rp_funct;
    wire [31:0] rp_rs1, rp_rs2, rp_rd;
    dfx_decoupler #(.W_TO_RP(75), .W_FROM_RP(33)) u_decouple (
        .decouple(decouple_r),
        .s_to_rp({slot_valid, slot_funct, slot_rs1, slot_rs2}), .rp_in({rp_valid, rp_funct, rp_rs1, rp_rs2}),
        .rp_out({rp_ready, rp_rd}), .s_from_rp({slot_ready, slot_rd}),
        .decouple_status(decouple_status)
    );
    rm_slot u_rm (.clk(clk), .valid(rp_valid), .funct(rp_funct), .rs1(rp_rs1), .rs2(rp_rs2),
                  .rd(rp_rd), .ready(rp_ready));

    wire sel_ram = mem_addr[31:28] == 4'h0;
    wire sel_io = mem_addr[31:28] == 4'h1;
    wire ram_en = mem_valid && !mem_ready && sel_ram;
    wire io_en = mem_valid && !mem_ready && sel_io;
    wire io_wr = |mem_wstrb;

    reg [31:0] ram [0:MEM_WORDS-1];
    reg [31:0] ram_q = 32'd0;
    initial $readmemh(MEM_INIT, ram);
    wire [10:0] ram_a = mem_addr[12:2];
    always @(posedge clk) begin
        if (ram_en) begin
            if (mem_wstrb[0]) ram[ram_a][7:0] <= mem_wdata[7:0];
            if (mem_wstrb[1]) ram[ram_a][15:8] <= mem_wdata[15:8];
            if (mem_wstrb[2]) ram[ram_a][23:16] <= mem_wdata[23:16];
            if (mem_wstrb[3]) ram[ram_a][31:24] <= mem_wdata[31:24];
            ram_q <= ram[ram_a];
        end
    end

    wire rx_valid;
    wire [7:0] rx_data;
    uart_rx #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_rx (.clk(clk), .rx(uart_txd_in), .valid(rx_valid), .data(rx_data));
    reg tx_start = 1'b0;
    reg [7:0] tx_data = 8'd0;
    wire tx_busy;
    uart_tx #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_tx (.clk(clk), .start(tx_start), .data(tx_data), .tx(uart_rxd_out), .busy(tx_busy));
    wire tx_full = tx_busy | tx_start;

    reg [7:0] rxf [0:15];
    reg [4:0] rxf_wp = 5'd0, rxf_rp = 5'd0;
    wire rxf_empty = rxf_wp == rxf_rp;
    wire rxf_full = (rxf_wp - rxf_rp) == 5'd16;
    reg rx_pop = 1'b0;
    reg [7:0] rx_overruns = 8'd0;
    always @(posedge clk) begin
        if (rx_valid) begin
            if (!rxf_full) begin
                rxf[rxf_wp[3:0]] <= rx_data;
                rxf_wp <= rxf_wp + 5'd1;
            end else begin
                rx_overruns <= rx_overruns + 8'd1;
            end
        end
        if (rx_pop) rxf_rp <= rxf_rp + 5'd1;
    end

    function [31:0] bswap(input [31:0] w);
        integer i;
        begin
            for (i = 0; i < 32; i = i + 1)
                bswap[i] = w[(i & ~7) + (7 - (i & 7))];
        end
    endfunction

    reg icap_csib = 1'b1, icap_rdwrb = 1'b0;
    reg [31:0] icap_i = 32'd0;
    wire [31:0] icap_o;
    ICAPE2 #(.ICAP_WIDTH("X32")) u_icap (.CLK(clk), .CSIB(icap_csib), .RDWRB(icap_rdwrb), .I(icap_i), .O(icap_o));

    reg spi_cs_on = 1'b0;
    reg spi_start = 1'b0;
    reg [31:0] spi_wdata = 32'd0;
    reg [1:0] spi_st = 2'd0;
    wire spi_busy, spi_sck, spi_mosi;
    wire [31:0] spi_rdata;
    spi_master #(.DIV(SPI_DIV)) u_spi (.clk(clk), .start(spi_start), .wdata(spi_wdata), .busy(spi_busy),
                                      .rdata(spi_rdata), .sck(spi_sck), .mosi(spi_mosi), .miso(qspi_dq1));
    assign qspi_cs = !spi_cs_on;
    assign qspi_dq0 = spi_mosi;
    assign qspi_dq2 = 1'b1;
    assign qspi_dq3 = 1'b1;
    generate
        if (SCK_STARTUPE2) begin : g_startup
            assign qspi_sck = 1'bz;
            STARTUPE2 #(.PROG_USR("FALSE"), .SIM_CCLK_FREQ(10.0)) u_startup (
                .CFGCLK(), .CFGMCLK(), .EOS(), .PREQ(),
                .CLK(1'b0), .GSR(1'b0), .GTS(1'b0), .KEYCLEARB(1'b1), .PACK(1'b0),
                .USRCCLKO(spi_sck), .USRCCLKTS(1'b0), .USRDONEO(1'b1), .USRDONETS(1'b1)
            );
        end else begin : g_pin
            assign qspi_sck = spi_sck;
        end
    endgenerate

    reg [3:0] led_r = 4'd0;
    assign led = led_r;
    reg [31:0] io_q = 32'd0;
    reg [2:0] rd_phase = 3'd0;
    always @(posedge clk) begin
        ram_ready <= ram_en;
        io_ready <= 1'b0;
        tx_start <= 1'b0;
        rx_pop <= 1'b0;
        icap_csib <= 1'b1;
        spi_start <= 1'b0;
        if (io_en) begin
            case (mem_addr[5:2])
                4'd0: begin
                    if (io_wr) led_r <= mem_wdata[3:0];
                    io_q <= {28'd0, led_r};
                    io_ready <= 1'b1;
                end
                4'd1: if (!io_wr) begin
                    io_q <= 32'd0;
                    io_ready <= 1'b1;
                end else if (!tx_full) begin
                    tx_data <= mem_wdata[7:0];
                    tx_start <= 1'b1;
                    io_ready <= 1'b1;
                end
                4'd2: begin
                    io_q <= {31'd0, tx_full};
                    io_ready <= 1'b1;
                end
                4'd3: begin
                    io_q <= {23'd0, !rxf_empty, rxf_empty ? 8'd0 : rxf[rxf_rp[3:0]]};
                    if (!io_wr && !rxf_empty) rx_pop <= 1'b1;
                    io_ready <= 1'b1;
                end
                4'd4: begin
                    if (io_wr) begin
                        icap_i <= bswap(mem_wdata);
                        icap_csib <= 1'b0;
                    end
                    io_q <= 32'd0;
                    io_ready <= 1'b1;
                end
                4'd5: if (io_wr) begin
                    io_q <= 32'd0;
                    io_ready <= 1'b1;
                end else begin
                    rd_phase <= rd_phase + 3'd1;
                    case (rd_phase)
                        3'd0: icap_rdwrb <= 1'b1;
                        3'd1: icap_csib <= 1'b0;
                        3'd5: begin
                            io_q <= bswap(icap_o);
                            icap_rdwrb <= 1'b0;
                            rd_phase <= 3'd0;
                            io_ready <= 1'b1;
                        end
                        default: ;
                    endcase
                end
                4'd6: begin
                    io_q <= {8'd0, rx_overruns, slot_timeouts};
                    io_ready <= 1'b1;
                end
                4'd7: begin
                    io_q <= {16'd0, slot_late};
                    io_ready <= 1'b1;
                end
                4'd8: begin
                    if (io_wr) spi_cs_on <= mem_wdata[0];
                    io_q <= {31'd0, spi_cs_on};
                    io_ready <= 1'b1;
                end
                4'd9: case (spi_st)
                    2'd0: begin
                        spi_wdata <= io_wr ? mem_wdata : 32'd0;
                        spi_start <= 1'b1;
                        spi_st <= 2'd1;
                    end
                    2'd1: spi_st <= 2'd2;
                    default: if (!spi_busy) begin
                        io_q <= spi_rdata;
                        io_ready <= 1'b1;
                        spi_st <= 2'd0;
                    end
                endcase
                4'd10: begin
                    io_q <= spi_rdata;
                    io_ready <= 1'b1;
                end
                4'd11: begin
                    if (io_wr) decouple_r <= mem_wdata[0];
                    io_q <= {31'd0, decouple_status};
                    io_ready <= 1'b1;
                end
                default: begin
                    io_q <= 32'd0;
                    io_ready <= 1'b1;
                end
            endcase
        end
    end

    reg rdata_from_io = 1'b0;
    always @(posedge clk) if (mem_valid && !mem_ready) rdata_from_io <= sel_io;
    assign mem_rdata = rdata_from_io ? io_q : ram_q;
endmodule
