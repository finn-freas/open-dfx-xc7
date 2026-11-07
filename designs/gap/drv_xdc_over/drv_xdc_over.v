module drv_xdc_over (input wire clk, output wire o, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [0:0] y;

    OBUF #(.IOSTANDARD("LVCMOS33"), .DRIVE(4), .SLEW("SLOW")) u_o (.I(s[0]), .O(o));
    assign y = s[1];
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 1; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
