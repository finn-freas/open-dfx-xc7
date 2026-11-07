module bufh (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [15:0] y;

    wire g0, g1;
    BUFH u_bufh (.I(clk), .O(g0));
    BUFHCE u_bufhce (.I(clk), .CE(s[0]), .O(g1));

    reg [7:0] c0 = 8'd0, c1 = 8'd0;
    always @(posedge g0) c0 <= c0 + 8'd1;
    always @(posedge g1) c1 <= c1 + 8'd1;

    assign y = {c0, c1};
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 16; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
