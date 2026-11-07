module rm_rp2 (input wire clk, input wire [7:0] din, output reg [3:0] dout);
    always @(posedge clk) dout <= 4'b1000 >> din[7:6];
endmodule
