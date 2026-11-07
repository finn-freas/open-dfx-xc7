`timescale 1ns/1ps
module ICAPE2 #(parameter ICAP_WIDTH = "X32") (
    input wire CLK, input wire CSIB, input wire RDWRB, input wire [31:0] I, output reg [31:0] O
);
    reg [31:0] wmem [0:63];
    integer nw = 0;
    integer nr = 0;
    always @(posedge CLK) begin
        if (!CSIB && !RDWRB) begin
            wmem[nw] <= I;
            nw <= nw + 1;
        end
        if (!CSIB && RDWRB) begin
            O <= 32'hC0DE0000 + nr;
            nr <= nr + 1;
        end
    end
endmodule

module tb;
    localparam CPB = 8;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rx = 1'b1;
    wire tx;
    uart_icap #(.CLKS_PER_BIT(CPB), .SWAP(1)) dut (.clk(clk), .rx(rx), .tx(tx), .status());

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
            repeat (CPB * 2) @(posedge clk);
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

    function [31:0] bswap(input [31:0] w);
        integer i;
        begin
            for (i = 0; i < 32; i = i + 1) bswap[i] = w[(i & ~7) + (7 - (i & 7))];
        end
    endfunction

    reg [31:0] words [0:3];
    integer k, errors;
    initial begin
        errors = 0;
        words[0] = 32'hFFFFFFFF; words[1] = 32'hAA995566; words[2] = 32'h20000000; words[3] = 32'h30008001;
        repeat (20) @(posedge clk);
        send_byte("W"); send_word(32'd4);
        for (k = 0; k < 4; k = k + 1) send_word(words[k]);
        repeat (CPB * 60) @(posedge clk);
        if (tb.dut.u_icap.nw != 4) begin $display("FAIL: icap got %0d writes", tb.dut.u_icap.nw); errors = errors + 1; end
        for (k = 0; k < 4; k = k + 1)
            if (tb.dut.u_icap.wmem[k] !== bswap(words[k])) begin
                $display("FAIL: icap word %0d = %08x, want %08x", k, tb.dut.u_icap.wmem[k], bswap(words[k]));
                errors = errors + 1;
            end
        if (ngot != 5 || got[0] != "K" || {got[1], got[2], got[3], got[4]} != 32'd4) begin
            $display("FAIL: ack bytes ngot=%0d", ngot); errors = errors + 1;
        end
        ngot = 0;
        send_byte("R"); send_word(32'd3);
        repeat (CPB * 200) @(posedge clk);
        if (ngot != 12) begin $display("FAIL: read reply %0d bytes", ngot); errors = errors + 1; end
        for (k = 0; k < 3; k = k + 1)
            $display("read word %0d = %02x%02x%02x%02x (icap O before swap-back: %08x)", k,
                     got[4*k], got[4*k+1], got[4*k+2], got[4*k+3], bswap({got[4*k], got[4*k+1], got[4*k+2], got[4*k+3]}));
        if (errors == 0) $display("PASS");
        $finish;
    end

endmodule
