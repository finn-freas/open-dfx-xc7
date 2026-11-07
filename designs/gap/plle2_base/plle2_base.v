module plle2_base (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [16:0] y;

    wire fb, o0, o1, locked, g0, g1;
    PLLE2_BASE #(.CLKIN1_PERIOD(10.0), .CLKFBOUT_MULT(12), .CLKOUT0_DIVIDE(6), .CLKOUT1_DIVIDE(24)) u_pll (
        .CLKIN1(clk), .CLKFBIN(fb), .CLKFBOUT(fb), .RST(1'b0), .PWRDWN(1'b0),
        .CLKOUT0(o0), .CLKOUT1(o1), .LOCKED(locked));
    BUFG u_b0 (.I(o0), .O(g0));
    BUFG u_b1 (.I(o1), .O(g1));

    reg [7:0] c0 = 8'd0, c1 = 8'd0;
    always @(posedge g0) c0 <= c0 + 8'd1;
    always @(posedge g1) c1 <= c1 + 8'd1;

    assign y = {c0, c1, locked};
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 17; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
