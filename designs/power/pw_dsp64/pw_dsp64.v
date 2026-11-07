module pw_dsp64 (input wire clk, output wire [3:0] led);
    reg [31:0] s [0:32];
    integer k;
    initial for (k = 0; k <= 32; k = k + 1) s[k] = 32'h1234567 + k * 32'h9e3779b9;
    genvar i;
    generate for (i = 0; i <= 32; i = i + 1) begin : xs
        wire [31:0] a = s[i] ^ (s[i] << 13);
        wire [31:0] b = a ^ (a >> 17);
        always @(posedge clk) s[i] <= b ^ (b << 5);
    end endgenerate
    reg [47:0] p [0:63];
    reg [24:0] a [0:63];
    reg [17:0] b [0:63];
    reg [42:0] m [0:63];
    integer j;
    initial for (j = 0; j < 64; j = j + 1) p[j] = 48'd0;
    generate for (i = 0; i < 64; i = i + 1) begin : mac
        always @(posedge clk) begin
            a[i] <= s[i / 2][24:0];
            b[i] <= s[i / 2 + 1][31:14];
            m[i] <= $signed(a[i]) * $signed(b[i]);
            p[i] <= p[i] + {{5{m[i][42]}}, m[i]};
        end
    end endgenerate
    wire [47:0] r = p[0] ^ p[1] ^ p[2] ^ p[3] ^ p[4] ^ p[5] ^ p[6] ^ p[7] ^ p[8] ^ p[9] ^ p[10] ^ p[11] ^ p[12] ^ p[13] ^ p[14] ^ p[15] ^ p[16] ^ p[17] ^ p[18] ^ p[19] ^ p[20] ^ p[21] ^ p[22] ^ p[23] ^ p[24] ^ p[25] ^ p[26] ^ p[27] ^ p[28] ^ p[29] ^ p[30] ^ p[31] ^ p[32] ^ p[33] ^ p[34] ^ p[35] ^ p[36] ^ p[37] ^ p[38] ^ p[39] ^ p[40] ^ p[41] ^ p[42] ^ p[43] ^ p[44] ^ p[45] ^ p[46] ^ p[47] ^ p[48] ^ p[49] ^ p[50] ^ p[51] ^ p[52] ^ p[53] ^ p[54] ^ p[55] ^ p[56] ^ p[57] ^ p[58] ^ p[59] ^ p[60] ^ p[61] ^ p[62] ^ p[63];
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= r[3:0] ^ r[47:44];
    assign led = l;
endmodule
