module muxf7f8 (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [2:0] y;

    wire [3:0] lo;
    LUT6 #(.INIT(64'h0123_4567_89ab_cdef)) u_l0 (.I0(s[0]), .I1(s[1]), .I2(s[2]), .I3(s[3]), .I4(s[4]), .I5(s[5]), .O(lo[0]));
    LUT6 #(.INIT(64'hfedc_ba98_7654_3210)) u_l1 (.I0(s[0]), .I1(s[1]), .I2(s[2]), .I3(s[3]), .I4(s[4]), .I5(s[5]), .O(lo[1]));
    LUT6 #(.INIT(64'h0f0f_3c3c_5a5a_9696)) u_l2 (.I0(s[0]), .I1(s[1]), .I2(s[2]), .I3(s[3]), .I4(s[4]), .I5(s[5]), .O(lo[2]));
    LUT6 #(.INIT(64'hf0f0_c3c3_a5a5_6969)) u_l3 (.I0(s[0]), .I1(s[1]), .I2(s[2]), .I3(s[3]), .I4(s[4]), .I5(s[5]), .O(lo[3]));
    wire m7a, m7b, m8;
    MUXF7 u_m7a (.I0(lo[0]), .I1(lo[1]), .S(s[6]), .O(m7a));
    MUXF7 u_m7b (.I0(lo[2]), .I1(lo[3]), .S(s[6]), .O(m7b));
    MUXF8 u_m8 (.I0(m7a), .I1(m7b), .S(s[7]), .O(m8));
    assign y = {m8, m7b, m7a};
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
