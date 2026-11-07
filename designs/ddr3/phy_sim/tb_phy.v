`timescale 1ps / 1ps

module tb_phy;
    localparam TSYS   = 10000;
    localparam TCK    = 2500;
    localparam LANES  = 2;
    localparam DELAYS = 32;
    localparam SLIPS  = 8;
    localparam NCHECK = 24;
    parameter  DEBUG_ONLY = 0;

    reg sys_clk = 0, sys4x_clk = 0, sys4x_dqs_clk = 0, idelay_clk = 0;
    reg sys_rst = 1, idelay_rst = 1;
    always #(TSYS / 2) sys_clk = ~sys_clk;
    always #(TCK / 2) sys4x_clk = ~sys4x_clk;
    initial begin #(TCK / 4); forever #(TCK / 2) sys4x_dqs_clk = ~sys4x_dqs_clk; end
    always #2500 idelay_clk = ~idelay_clk;

    wire [13:0] a;
    wire  [2:0] ba;
    wire        ras_n, cas_n, we_n, cs_n, clk_p, clk_n, cke, odt, reset_n;
    wire  [1:0] dm;
    wire [15:0] dq;
    wire  [1:0] dqs_p, dqs_n;

    reg   [1:0] dly_sel = 0;
    reg         rdly_dq_rst = 0, rdly_dq_inc = 0, rdly_dq_bitslip_rst = 0, rdly_dq_bitslip = 0;

    reg  [13:0] address [0:3];
    reg   [2:0] bank    [0:3];
    reg   [3:0] cas_n_r, cs_n_r, ras_n_r, we_n_r, wrdata_en, rddata_en;
    reg  [31:0] wrdata  [0:3];
    reg         cke_r = 0, reset_n_r = 0;
    wire [31:0] rddata  [0:3];
    wire  [3:0] rddata_valid;

    phy_top dut (
        .sys_clk(sys_clk), .sys_rst(sys_rst), .sys4x_clk(sys4x_clk), .sys4x_dqs_clk(sys4x_dqs_clk),
        .idelay_clk(idelay_clk), .idelay_rst(idelay_rst),
        .ddram_a(a), .ddram_ba(ba), .ddram_ras_n(ras_n), .ddram_cas_n(cas_n), .ddram_we_n(we_n),
        .ddram_cs_n(cs_n), .ddram_dm(dm), .ddram_dq(dq), .ddram_dqs_p(dqs_p), .ddram_dqs_n(dqs_n),
        .ddram_clk_p(clk_p), .ddram_clk_n(clk_n), .ddram_cke(cke), .ddram_odt(odt), .ddram_reset_n(reset_n),
        .dly_sel(dly_sel), .rdly_dq_rst(rdly_dq_rst), .rdly_dq_inc(rdly_dq_inc),
        .rdly_dq_bitslip_rst(rdly_dq_bitslip_rst), .rdly_dq_bitslip(rdly_dq_bitslip),
        .wlevel_strobe(1'b0), .wdly_dq_bitslip_rst(1'b0), .wdly_dq_bitslip(1'b0),
        .dfi_p0_address(address[0]), .dfi_p0_bank(bank[0]), .dfi_p0_cas_n(cas_n_r[0]), .dfi_p0_cs_n(cs_n_r[0]),
        .dfi_p0_ras_n(ras_n_r[0]), .dfi_p0_we_n(we_n_r[0]), .dfi_p0_cke(cke_r), .dfi_p0_odt(1'b0),
        .dfi_p0_reset_n(reset_n_r), .dfi_p0_act_n(1'b1), .dfi_p0_wrdata(wrdata[0]), .dfi_p0_wrdata_en(wrdata_en[0]),
        .dfi_p0_wrdata_mask(4'b0), .dfi_p0_rddata_en(rddata_en[0]), .dfi_p0_rddata(rddata[0]),
        .dfi_p0_rddata_valid(rddata_valid[0]),
        .dfi_p1_address(address[1]), .dfi_p1_bank(bank[1]), .dfi_p1_cas_n(cas_n_r[1]), .dfi_p1_cs_n(cs_n_r[1]),
        .dfi_p1_ras_n(ras_n_r[1]), .dfi_p1_we_n(we_n_r[1]), .dfi_p1_cke(cke_r), .dfi_p1_odt(1'b0),
        .dfi_p1_reset_n(reset_n_r), .dfi_p1_act_n(1'b1), .dfi_p1_wrdata(wrdata[1]), .dfi_p1_wrdata_en(wrdata_en[1]),
        .dfi_p1_wrdata_mask(4'b0), .dfi_p1_rddata_en(rddata_en[1]), .dfi_p1_rddata(rddata[1]),
        .dfi_p1_rddata_valid(rddata_valid[1]),
        .dfi_p2_address(address[2]), .dfi_p2_bank(bank[2]), .dfi_p2_cas_n(cas_n_r[2]), .dfi_p2_cs_n(cs_n_r[2]),
        .dfi_p2_ras_n(ras_n_r[2]), .dfi_p2_we_n(we_n_r[2]), .dfi_p2_cke(cke_r), .dfi_p2_odt(1'b0),
        .dfi_p2_reset_n(reset_n_r), .dfi_p2_act_n(1'b1), .dfi_p2_wrdata(wrdata[2]), .dfi_p2_wrdata_en(wrdata_en[2]),
        .dfi_p2_wrdata_mask(4'b0), .dfi_p2_rddata_en(rddata_en[2]), .dfi_p2_rddata(rddata[2]),
        .dfi_p2_rddata_valid(rddata_valid[2]),
        .dfi_p3_address(address[3]), .dfi_p3_bank(bank[3]), .dfi_p3_cas_n(cas_n_r[3]), .dfi_p3_cs_n(cs_n_r[3]),
        .dfi_p3_ras_n(ras_n_r[3]), .dfi_p3_we_n(we_n_r[3]), .dfi_p3_cke(cke_r), .dfi_p3_odt(1'b0),
        .dfi_p3_reset_n(reset_n_r), .dfi_p3_act_n(1'b1), .dfi_p3_wrdata(wrdata[3]), .dfi_p3_wrdata_en(wrdata_en[3]),
        .dfi_p3_wrdata_mask(4'b0), .dfi_p3_rddata_en(rddata_en[3]), .dfi_p3_rddata(rddata[3]),
        .dfi_p3_rddata_valid(rddata_valid[3])
    );

    ddr3_model #(.CL(6), .CWL(5), .TCK(TCK), .LANES(LANES)) mem (
        .ck_p(clk_p), .ck_n(clk_n), .cke(cke), .cs_n(cs_n), .ras_n(ras_n), .cas_n(cas_n), .we_n(we_n),
        .ba(ba), .a(a), .dm(dm), .dq(dq), .dqs_p(dqs_p), .dqs_n(dqs_n), .odt(odt), .reset_n(reset_n)
    );

    integer p, l, b, d, s, k, t, bb, rr, cc, sd, errors, best_s, best_d, run, best_run, start;
    reg   [7:0] rx [0:7][0:LANES-1];
    reg         pass [0:LANES-1][0:SLIPS-1][0:DELAYS-1];
    reg  [15:0] beat;
    integer     wr_first0;
    reg         debug = 0;
    integer     nvalid = 0;
    integer     ncmd = 0;

    function [7:0] pat(input integer seed, input integer bt, input integer ln);
        pat = (seed * 8'h3B + bt * 8'h1D + ln * 8'h6B + 8'h35) & 8'hFF;
    endfunction

    task nop;
        begin
            for (p = 0; p < 4; p = p + 1) begin
                cs_n_r[p] <= 1; ras_n_r[p] <= 1; cas_n_r[p] <= 1; we_n_r[p] <= 1;
                wrdata_en[p] <= 0; rddata_en[p] <= 0;
            end
        end
    endtask

    task cmd(input integer ph, input r, input c, input w, input [2:0] bk, input [13:0] ad, input wr, input rd);
        begin
            @(posedge sys_clk);
            nop;
            cs_n_r[ph] <= 0; ras_n_r[ph] <= r; cas_n_r[ph] <= c; we_n_r[ph] <= w;
            bank[ph] <= bk; address[ph] <= ad; wrdata_en[ph] <= wr; rddata_en[ph] <= rd;
            @(posedge sys_clk);
            if (debug || ncmd < 4)
                $display("[dbg] DFI command (phase %0d, ras %0d cas %0d we %0d) sampled by the PHY at %0t ps", ph, r, c, w, $time);
            ncmd = ncmd + 1;
            nop;
        end
    endtask

    task idle(input integer n);
        begin
            repeat (n) @(posedge sys_clk);
        end
    endtask

    task pulse_rst;  begin @(posedge sys_clk); rdly_dq_rst <= 1; @(posedge sys_clk); rdly_dq_rst <= 0; end endtask
    task pulse_inc;  begin @(posedge sys_clk); rdly_dq_inc <= 1; @(posedge sys_clk); rdly_dq_inc <= 0; end endtask
    task pulse_srst; begin @(posedge sys_clk); rdly_dq_bitslip_rst <= 1; @(posedge sys_clk); rdly_dq_bitslip_rst <= 0; end endtask
    task pulse_slip; begin @(posedge sys_clk); rdly_dq_bitslip <= 1; @(posedge sys_clk); rdly_dq_bitslip <= 0; end endtask

    task write_burst(input [2:0] bk, input [13:0] row, input [9:0] col, input integer seed);
        begin
            for (p = 0; p < 4; p = p + 1)
                for (k = 0; k < 2; k = k + 1)
                    for (l = 0; l < LANES; l = l + 1)
                        wrdata[p][16 * k + 8 * l +: 8] <= pat(seed, 2 * p + k, l);
            cmd(0, 0, 1, 1, bk, row, 0, 0);
            idle(4);
            cmd(3, 1, 0, 0, bk, {4'b0, col}, 1, 0);
            idle(12);
        end
    endtask

    task read_burst(input [2:0] bk, input [13:0] row, input [9:0] col);
        integer cyc, rp, rk, rl;
        begin
            for (rp = 0; rp < 8; rp = rp + 1)
                for (rl = 0; rl < LANES; rl = rl + 1)
                    rx[rp][rl] = 8'hxx;
            cmd(0, 0, 1, 1, bk, row, 0, 0);
            idle(4);
            fork
                cmd(3, 1, 0, 1, bk, {4'b0, col}, 0, 1);
                for (cyc = 0; cyc < 24; cyc = cyc + 1) begin
                    @(posedge sys_clk);
                    for (rp = 0; rp < 4; rp = rp + 1)
                        if (rddata_valid[rp]) begin
                            nvalid = nvalid + 1;
                            for (rk = 0; rk < 2; rk = rk + 1)
                                for (rl = 0; rl < LANES; rl = rl + 1)
                                    rx[2 * rp + rk][rl] = rddata[rp][16 * rk + 8 * rl +: 8];
                        end
                    if (debug)
                        $display("[dbg] cyc %0d t %0t valid %b p0 %h p1 %h p2 %h p3 %h", cyc, $time, rddata_valid,
                                 rddata[0], rddata[1], rddata[2], rddata[3]);
                end
            join
        end
    endtask

    function lane_ok(input integer ln, input integer seed);
        integer q;
        begin
            lane_ok = 1;
            for (q = 0; q < 8; q = q + 1)
                if (rx[q][ln] !== pat(seed, q, ln))
                    lane_ok = 0;
        end
    endfunction

    task set_delay(input [1:0] sel, input integer slip, input integer taps);
        begin
            dly_sel <= sel;
            pulse_srst;
            for (k = 0; k < slip; k = k + 1) pulse_slip;
            pulse_rst;
            for (k = 0; k < taps; k = k + 1) pulse_inc;
            dly_sel <= 0;
            idle(2);
        end
    endtask

    initial begin
        errors = 0;
        nop;
        for (p = 0; p < 4; p = p + 1) begin bank[p] = 0; address[p] = 0; wrdata[p] = 0; end
        #(200000);
        idelay_rst = 0;
        #(100000);
        sys_rst = 0;
        idle(20);
        reset_n_r <= 1;
        idle(20);
        cke_r <= 1;
        idle(20);
        $display("[tb] write path: 2 bursts");
        write_burst(0, 0, 0, 1);
        for (l = 0; l < LANES; l = l + 1)
            $display("[tb] lane %0d: first write DQS edge %0d ps after the WRITE command at CK (CWL*tCK = %0d ps)",
                     l, mem.wr_first[l], 5 * TCK);
        write_burst(0, 0, 8, 2);
        for (b = 0; b < 8; b = b + 1) begin
            beat = mem.mem[mem.index(0, 0, 0) + b];
            for (l = 0; l < LANES; l = l + 1)
                if (beat[8 * l +: 8] !== pat(1, b, l)) begin
                    errors = errors + 1;
                    $display("[tb] WRITE PATH ERROR: model beat %0d lane %0d = %h, expected %h", b, l, beat[8 * l +: 8], pat(1, b, l));
                end
        end
        $display("[tb] write path beat order on the pins: %0s", errors ? "WRONG" : "as DFI phases/halves (16 beats checked)");
        if (DEBUG_ONLY) begin
            for (s = 2; s < 7; s = s + 4) begin
                d = 8;
                set_delay(2'b11, s, d);
                debug = 1;
                $display("[dbg] bitslip %0d delay %0d, expected beats lane0: %h %h %h %h %h %h %h %h", s, d, pat(1,0,0), pat(1,1,0),
                         pat(1,2,0), pat(1,3,0), pat(1,4,0), pat(1,5,0), pat(1,6,0), pat(1,7,0));
                read_burst(0, 0, 0);
                debug = 0;
            end
            $finish;
        end
        $display("[tb] read leveling scan (like the BIOS: per module, per bitslip, %0d delay taps)", DELAYS);
        for (s = 0; s < SLIPS; s = s + 1)
            for (d = 0; d < DELAYS; d = d + 1) begin
                set_delay(2'b11, s, d);
                read_burst(0, 0, 0);
                for (l = 0; l < LANES; l = l + 1) pass[l][s][d] = lane_ok(l, 1);
                read_burst(0, 0, 8);
                for (l = 0; l < LANES; l = l + 1) pass[l][s][d] = pass[l][s][d] & lane_ok(l, 2);
            end
        for (l = 0; l < LANES; l = l + 1) begin
            best_run = 0; best_s = -1; best_d = -1;
            for (s = 0; s < SLIPS; s = s + 1) begin
                $write("[tb] m%0d, b%0d: |", l, s);
                run = 0; start = 0;
                for (d = 0; d < DELAYS; d = d + 1) begin
                    $write("%0d", pass[l][s][d]);
                    if (pass[l][s][d]) begin
                        if (run == 0) start = d;
                        run = run + 1;
                        if (run > best_run) begin best_run = run; best_s = s; best_d = start + (run - 1) / 2; end
                    end else run = 0;
                end
                $write("|\n");
            end
            $display("[tb] best: m%0d, b%0d, delay %0d (window %0d taps)", l, best_s, best_d, best_run);
            if (best_run == 0) errors = errors + 1;
            set_delay(l == 0 ? 2'b01 : 2'b10, best_s, best_d);
        end
        $display("[tb] memtest: %0d bursts over banks/rows/columns at the chosen delays", NCHECK);
        for (t = 0; t < NCHECK; t = t + 1) begin
            bb = t % 8; rr = (t * 5) % 128; cc = ((t * 24) % 1024) & 10'h3f8; sd = 100 + t;
            write_burst(bb, rr, cc, sd);
            read_burst(bb, rr, cc);
            for (l = 0; l < LANES; l = l + 1)
                if (!lane_ok(l, sd)) begin
                    errors = errors + 1;
                    $display("[tb] MEMTEST ERROR burst %0d lane %0d bank %0d row %0d col %0d", t, l, bb, rr, cc);
                end
        end
        $display("[tb] model saw ACT %0d, WRITE %0d, READ %0d, MRS %0d, other %0d", mem.n_act, mem.n_wr, mem.n_rd, mem.n_mrs, mem.n_other);
        if (errors == 0) $display("[tb] PASS");
        else $display("[tb] FAIL: %0d errors", errors);
        $finish;
    end
endmodule
