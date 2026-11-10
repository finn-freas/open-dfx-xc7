module x_pad_b (input wire clk, input wire [3:0] i, output wire [4:0] o, input wire [0:0] dip, input wire [0:0] din, output wire [0:0] dop, output wire [0:0] don);
    wire [0:0] di;
    IBUFDS u_ibd0 (.I(dip[0]), .IB(din[0]), .O(di[0]));
    reg [4:0] r = 0;
    always @(posedge clk) r <= {di, i};
    reg [5:0] q = 0;
    always @(posedge clk) q <= q + {{5{1'b0}}, ^r} + 1'b1;
    assign o = q[4:0];
    OBUFDS u_obd0 (.I(q[5]), .O(dop[0]), .OB(don[0]));
endmodule
