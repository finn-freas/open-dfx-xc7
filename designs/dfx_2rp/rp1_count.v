module rm_rp1 (input wire clk, input wire [7:0] din, output reg [3:0] dout);
    always @(posedge clk) dout <= din[7:4];
endmodule
