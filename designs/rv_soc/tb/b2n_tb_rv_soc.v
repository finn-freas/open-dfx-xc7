`timescale 1ns/1ps
module b2n_tb_rv_soc;
    localparam CPB = 100;
    localparam [9:0] FUNCT = 10'd0;
    localparam NV = 11;
    localparam BOOT_CYCLES = 200;

    reg clk = 0;
    always #5 clk = ~clk;
    reg rx = 1'b1;
    wire tx;
    wire [3:0] led;
    `B2N_DUT dut (.clk(clk), .uart_txd_in(rx), .uart_rxd_out(tx), .led(led));

    reg [31:0] va [0:NV-1];
    reg [31:0] vb [0:NV-1];
    initial begin
        va[0] = 32'h12345678; vb[0] = 32'h0F0F0F0F;
        va[1] = 32'h00000000; vb[1] = 32'h00000000;
        va[2] = 32'hFFFFFFFF; vb[2] = 32'hFFFFFFFF;
        va[3] = 32'hFFFFFFFF; vb[3] = 32'h00000000;
        va[4] = 32'h00000000; vb[4] = 32'hFFFFFFFF;
        va[5] = 32'h80000000; vb[5] = 32'h80000000;
        va[6] = 32'h80000000; vb[6] = 32'hFFFFFFFF;
        va[7] = 32'h7FFFFFFF; vb[7] = 32'h80000000;
        va[8] = 32'hFFFFFFFF; vb[8] = 32'h00000001;
        va[9] = 32'hA5A5A5A5; vb[9] = 32'h0000001F;
        va[10] = 32'h00000001; vb[10] = 32'h00000021;
    end

    reg [8*16-1:0] rm;
    function [31:0] expect_rm(input [31:0] a, input [31:0] b);
        begin
            if (rm == "xor") expect_rm = a ^ b;
            else if (rm == "andn") expect_rm = FUNCT[0] ? (a | ~b) : (a & ~b);
            else if (rm == "add") expect_rm = a + b;
            else expect_rm = 32'hxxxxxxxx;
        end
    endfunction

    task send_byte(input [7:0] v);
        integer i;
        begin
            rx = 1'b0;
            repeat (CPB) @(posedge clk);
            for (i = 0; i < 8; i = i + 1) begin
                rx = v[i];
                repeat (CPB) @(posedge clk);
            end
            rx = 1'b1;
            repeat (CPB) @(posedge clk);
        end
    endtask

    task send_word(input [31:0] w);
        begin
            send_byte(w[31:24]); send_byte(w[23:16]); send_byte(w[15:8]); send_byte(w[7:0]);
        end
    endtask

    reg armed = 1'b0;
    reg [7:0] got [0:1023];
    integer ngot = 0;
    always @(negedge tx) if (armed) begin : rxmon
        integer i;
        reg [7:0] v;
        repeat (CPB + CPB / 2) @(posedge clk);
        for (i = 0; i < 8; i = i + 1) begin
            v[i] = tx;
            repeat (CPB) @(posedge clk);
        end
        got[ngot] = v;
        ngot = ngot + 1;
    end

    task wait_bytes(input integer n);
        integer t;
        begin
            t = 0;
            while (ngot < n && t < CPB * 200) begin
                @(posedge clk);
                t = t + 1;
            end
        end
    endtask

    reg [8*64-1:0] tag;
    integer nv, k, base, fails;
    reg [31:0] a, b, r, e;
    reg ok;
    initial begin
        if (!$value$plusargs("RM=%s", rm)) rm = "?";
        if (!$value$plusargs("TAG=%s", tag)) tag = "?";
        if (!$value$plusargs("NVEC=%d", nv)) nv = NV;
        if (nv > NV) nv = NV;
        fails = 0;
        repeat (BOOT_CYCLES) @(posedge clk);
        if (tx !== 1'b1) begin
            $display("FAIL %0s %0s boot: uart tx idle level is %b after %0d cycles", tag, rm, tx, BOOT_CYCLES);
            fails = fails + 1;
        end
        armed = 1'b1;
        for (k = 0; k < nv; k = k + 1) begin
            a = va[k];
            b = vb[k];
            e = expect_rm(a, b);
            base = ngot;
            send_byte("C"); send_word(a); send_word(b);
            wait_bytes(base + 4);
            repeat (CPB * 12) @(posedge clk);
            r = {got[base], got[base + 1], got[base + 2], got[base + 3]};
            ok = (ngot == base + 4) && (r === e) && (led === e[3:0]);
            $display("%0s %0s %0s %08x %08x -> %08x expect %08x led %x replies %0d",
                     ok ? "PASS" : "FAIL", tag, rm, a, b, r, e, led, ngot - base);
            if (!ok) fails = fails + 1;
        end
        $display("DONE %0s %0s vectors=%0d fails=%0d time=%0t", tag, rm, nv, fails, $time);
        $finish;
    end
endmodule
