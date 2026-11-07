module dt_a_none (input wire clk, input wire rx0_p, input wire rx0_n, input wire rx1_p, input wire rx1_n, input wire rx2_p, input wire rx2_n, input wire rx3_p, input wire rx3_n, input wire rx4_p, input wire rx4_n, input wire rx5_p, input wire rx5_n, input wire rx6_p, input wire rx6_n, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [6:0] y;
    wire [6:0] di;
    IBUFDS #(.IOSTANDARD("LVDS_25"), .DIFF_TERM("FALSE")) u_ibufds0 (.I(rx0_p), .IB(rx0_n), .O(di[0]));
    IBUFDS #(.IOSTANDARD("LVDS_25"), .DIFF_TERM("FALSE")) u_ibufds1 (.I(rx1_p), .IB(rx1_n), .O(di[1]));
    IBUFDS #(.IOSTANDARD("LVDS_25"), .DIFF_TERM("FALSE")) u_ibufds2 (.I(rx2_p), .IB(rx2_n), .O(di[2]));
    IBUFDS #(.IOSTANDARD("LVDS_25"), .DIFF_TERM("FALSE")) u_ibufds3 (.I(rx3_p), .IB(rx3_n), .O(di[3]));
    IBUFDS #(.IOSTANDARD("LVDS_25"), .DIFF_TERM("FALSE")) u_ibufds4 (.I(rx4_p), .IB(rx4_n), .O(di[4]));
    IBUFDS #(.IOSTANDARD("LVDS_25"), .DIFF_TERM("FALSE")) u_ibufds5 (.I(rx5_p), .IB(rx5_n), .O(di[5]));
    IBUFDS #(.IOSTANDARD("LVDS_25"), .DIFF_TERM("FALSE")) u_ibufds6 (.I(rx6_p), .IB(rx6_n), .O(di[6]));
    reg [6:0] q = 0;
    always @(posedge clk) q <= di ^ s[6:0];
    assign y = q;
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 7; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
