`timescale 1ns/1ps
module ICAPE2 #(parameter ICAP_WIDTH = "X32") (
    input wire CLK, input wire CSIB, input wire RDWRB, input wire [31:0] I, output reg [31:0] O = 32'd0
);
    reg [31:0] wmem [0:255];
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
