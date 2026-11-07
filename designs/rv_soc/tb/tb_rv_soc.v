`timescale 1ns/1ps
module tb_rv_soc;
    localparam CPB = 100;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rx = 1'b1;
    wire tx;
    wire [3:0] led;
    rv_soc #(.MEM_INIT("designs/rv_soc/fw/main.hex"), .CLKS_PER_BIT(CPB)) dut (
        .clk(clk), .uart_txd_in(rx), .uart_rxd_out(tx), .led(led));

`ifdef RM_XOR
    localparam NAME = "rm_xor";
`else
    localparam NAME = "rm_add";
`endif

    function [31:0] model(input [31:0] a, input [31:0] b);
`ifdef RM_XOR
        model = a ^ b;
`else
        model = a + b;
`endif
    endfunction

    function [31:0] bswap(input [31:0] w);
        integer i;
        begin
            for (i = 0; i < 32; i = i + 1) bswap[i] = w[(i & ~7) + (7 - (i & 7))];
        end
    endfunction

    task send_byte(input [7:0] b);
        integer i;
        begin
            rx = 1'b0;
            repeat (CPB) @(posedge clk);
            for (i = 0; i < 8; i = i + 1) begin
                rx = b[i];
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

    reg [7:0] got [0:255];
    integer ngot = 0;
    always @(negedge tx) begin : rxmon
        integer i;
        reg [7:0] b;
        repeat (CPB + CPB / 2) @(posedge clk);
        for (i = 0; i < 8; i = i + 1) begin
            b[i] = tx;
            repeat (CPB) @(posedge clk);
        end
        got[ngot] = b;
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

    integer errors = 0;
    task do_cmd_c(input [31:0] a, input [31:0] b);
        integer base;
        reg [31:0] r, e;
        begin
            base = ngot;
            send_byte("C"); send_word(a); send_word(b);
            wait_bytes(base + 4);
            repeat (CPB * 12) @(posedge clk);
            r = {got[base], got[base + 1], got[base + 2], got[base + 3]};
            e = model(a, b);
            if (ngot != base + 4) begin
                $display("FAIL: C %08x %08x: got %0d reply bytes, expected 4", a, b, ngot - base);
                errors = errors + 1;
            end else if (r !== e) begin
                $display("FAIL: C %08x %08x: reply %08x expected %08x", a, b, r, e);
                errors = errors + 1;
            end else begin
                $display("ok:   C %08x %08x -> %08x (%0s)", a, b, r, NAME);
            end
            if (led !== e[3:0]) begin
                $display("FAIL: led=%x expected %x", led, e[3:0]);
                errors = errors + 1;
            end else begin
                $display("ok:   led=%x", led);
            end
        end
    endtask

    reg [31:0] words [0:7];
    integer k, base, nw0;
    initial begin
        words[0] = 32'hFFFFFFFF; words[1] = 32'hAA995566; words[2] = 32'h20000000; words[3] = 32'h30008001;
        words[4] = 32'h00000007; words[5] = 32'h12345678; words[6] = 32'h80000001; words[7] = 32'h0F1E2D3C;
        repeat (200) @(posedge clk);
        do_cmd_c(32'h12345678, 32'h11111111);
        do_cmd_c(32'hFFFFFFFF, 32'h00000003);

        base = ngot;
        nw0 = dut.u_icap.nw;
        send_byte("W"); send_word(32'd8);
        for (k = 0; k < 8; k = k + 1) send_word(words[k]);
        wait_bytes(base + 1);
        repeat (CPB * 12) @(posedge clk);
        if (ngot != base + 1 || got[base] !== "K") begin
            $display("FAIL: W: reply count %0d byte %02x, expected one 'K'", ngot - base, got[base]);
            errors = errors + 1;
        end else begin
            $display("ok:   W 8 words -> 'K'");
        end
        if (dut.u_icap.nw - nw0 != 8) begin
            $display("FAIL: ICAP got %0d writes, expected 8", dut.u_icap.nw - nw0);
            errors = errors + 1;
        end
        for (k = 0; k < 8; k = k + 1)
            if (dut.u_icap.wmem[nw0 + k] !== bswap(words[k])) begin
                $display("FAIL: ICAP word %0d = %08x expected %08x (bswap of %08x)", k, dut.u_icap.wmem[nw0 + k], bswap(words[k]), words[k]);
                errors = errors + 1;
            end else begin
                $display("ok:   ICAP word %0d sent %08x captured %08x", k, words[k], dut.u_icap.wmem[nw0 + k]);
            end

        do_cmd_c(32'hA5A5A5A5, 32'h0F0F0F0F);
        if (dut.trap) begin
            $display("FAIL: cpu trapped");
            errors = errors + 1;
        end
        if (dut.slot_timeouts != 0) begin
            $display("FAIL: %0d slot timeouts", dut.slot_timeouts);
            errors = errors + 1;
        end
        if (errors == 0) $display("PASS: tb_rv_soc %0s", NAME);
        else $display("FAIL: tb_rv_soc %0s (%0d errors)", NAME, errors);
        $finish;
    end
endmodule
