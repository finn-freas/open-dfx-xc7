module rm_slot (input wire clk, input wire [15:0] din, output reg [15:0] dout);
    always @(posedge clk) dout <= {din[6:0], din[15:7]} ^ (din + 16'h1234);
endmodule
