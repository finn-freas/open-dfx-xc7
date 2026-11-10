module x_pad_a (input wire clk, input wire [9:0] i, output wire [46:0] o, input wire [1:0] dip, input wire [1:0] din, output wire [1:0] dop, output wire [1:0] don);
    wire [1:0] di;
    IBUFDS u_ibd0 (.I(dip[0]), .IB(din[0]), .O(di[0]));
    IBUFDS u_ibd1 (.I(dip[1]), .IB(din[1]), .O(di[1]));
    reg [11:0] r = 0;
    always @(posedge clk) r <= {di, i};
    reg [48:0] q = 0;
    always @(posedge clk) q <= q + {{48{1'b0}}, ^r} + 1'b1;
    assign o = q[46:0];
    OBUFDS u_obd0 (.I(q[47]), .O(dop[0]), .OB(don[0]));
    OBUFDS u_obd1 (.I(q[48]), .O(dop[1]), .OB(don[1]));
endmodule
