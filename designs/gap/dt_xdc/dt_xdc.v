module dt_xdc (input wire clk, input wire rx0_p, input wire rx0_n, input wire rx1_p, input wire rx1_n, inout wire io_p, inout wire io_n, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [2:0] y;

    wire [1:0] di;
    IBUFDS #(.IOSTANDARD("LVDS_25")) u_ibufds0 (.I(rx0_p), .IB(rx0_n), .O(di[0]));
    IBUFDS #(.IOSTANDARD("LVDS_25")) u_ibufds1 (.I(rx1_p), .IB(rx1_n), .O(di[1]));
    wire bo;
    IOBUFDS #(.IOSTANDARD("LVDS_25"), .DIFF_TERM("TRUE")) u_iobufds (.I(s[4]), .T(s[5]), .O(bo), .IO(io_p), .IOB(io_n));
    reg [2:0] q = 0;
    always @(posedge clk) q <= {bo, di} ^ s[2:0];
    assign y = q;
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 3; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
