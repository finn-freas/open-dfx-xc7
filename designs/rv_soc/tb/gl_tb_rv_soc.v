`timescale 1ns/1ps
module gl_tb_rv_soc;
    localparam CPB = 100;
    localparam [9:0] FUNCT = 10'd0;
    localparam MAXV = 256;

    reg clk = 0;
    always #5 clk = ~clk;
    reg rx = 1'b1;
    wire tx;
    wire [3:0] led;
    rv_soc dut (.clk(clk), .uart_txd_in(rx), .uart_rxd_out(tx), .led(led));

    function [31:0] popc32(input [31:0] x);
        integer i;
        begin
            popc32 = 0;
            for (i = 0; i < 32; i = i + 1) popc32 = popc32 + x[i];
        end
    endfunction

    function [31:0] clz32(input [31:0] x);
        integer i;
        reg done;
        begin
            clz32 = 0;
            done = 1'b0;
            for (i = 31; i >= 0; i = i - 1) begin
                if (x[i]) done = 1'b1;
                if (!done) clz32 = clz32 + 1;
            end
        end
    endfunction

    function [31:0] rotl32(input [31:0] x, input integer n);
        reg [63:0] d;
        begin
            d = {x, x} << (n & 31);
            rotl32 = d[63:32];
        end
    endfunction

    reg [31:0] a = 0, b = 0;
    wire [9:0] f = FUNCT;
    wire [31:0] e_tab = `REF_EXPR;
`ifdef RTL_REF
    wire [31:0] e_rtl;
    rm_core rtl_ref (.valid(1'b1), .funct(f), .rs1(a), .rs2(b), .rd(e_rtl), .ready());
`endif

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

    reg [31:0] va [0:MAXV-1];
    reg [31:0] vb [0:MAXV-1];
    reg [8*32-1:0] rm;
    integer nv, k, base, fails;
    reg [31:0] r;
    reg ok;
    initial begin
        if (!$value$plusargs("RM=%s", rm)) rm = "?";
        if (!$value$plusargs("NVEC=%d", nv)) nv = 0;
        if (nv > MAXV) begin
            $display("FAIL %0s: %0d vectors, testbench holds %0d", rm, nv, MAXV);
            nv = MAXV;
        end
        if (nv > 0) begin
            $readmemh(`VEC_A, va, 0, nv - 1);
            $readmemh(`VEC_B, vb, 0, nv - 1);
        end
        fails = 0;
        repeat (200) @(posedge clk);
        if (tx !== 1'b1) begin
            $display("FAIL %0s boot: uart tx idle level is %b after 200 cycles", rm, tx);
            fails = fails + 1;
        end
        armed = 1'b1;
        for (k = 0; k < nv; k = k + 1) begin
            a = va[k];
            b = vb[k];
            base = ngot;
            send_byte("C"); send_word(a); send_word(b);
            wait_bytes(base + 4);
            repeat (CPB * 12) @(posedge clk);
            r = {got[base], got[base + 1], got[base + 2], got[base + 3]};
            ok = (ngot == base + 4) && (r === e_tab) && (led === e_tab[3:0]);
`ifdef RTL_REF
            ok = ok && (e_rtl === e_tab);
            $display("%0s %0s %08x %08x -> %08x expect %08x rtl %08x led %x replies %0d",
                     ok ? "PASS" : "FAIL", rm, a, b, r, e_tab, e_rtl, led, ngot - base);
`else
            $display("%0s %0s %08x %08x -> %08x expect %08x rtl n/a led %x replies %0d",
                     ok ? "PASS" : "FAIL", rm, a, b, r, e_tab, led, ngot - base);
`endif
            if (!ok) fails = fails + 1;
        end
        $display("DONE %0s vectors=%0d fails=%0d time=%0t", rm, nv, fails, $time);
        $finish;
    end
endmodule
