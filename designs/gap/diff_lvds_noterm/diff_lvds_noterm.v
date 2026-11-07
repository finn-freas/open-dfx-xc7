module diff_lvds_noterm (input wire clk, input wire rx_p, input wire rx_n, output wire tx_p, output wire tx_n, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [0:0] y;

    wire di;
    IBUFDS #(.IOSTANDARD("LVDS_25"), .DIFF_TERM("FALSE")) u_ibufds (.I(rx_p), .IB(rx_n), .O(di));
    reg q = 1'b0;
    always @(posedge clk) q <= di ^ s[0];
    OBUFDS #(.IOSTANDARD("LVDS_25")) u_obufds (.I(q), .O(tx_p), .OB(tx_n));
    assign y = q;
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
