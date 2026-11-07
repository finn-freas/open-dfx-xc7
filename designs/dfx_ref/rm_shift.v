module rm_slot (input wire clk, input wire [7:0] din, output reg [3:0] dout);
    always @(posedge clk) dout <= 4'b0001 << din[7:6];
endmodule
