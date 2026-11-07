module pw_dsp8 (input wire clk, output wire [3:0] led);
    reg [31:0] s [0:4];
    integer k;
    initial for (k = 0; k <= 4; k = k + 1) s[k] = 32'h1234567 + k * 32'h9e3779b9;
    genvar i;
    generate for (i = 0; i <= 4; i = i + 1) begin : xs
        wire [31:0] a = s[i] ^ (s[i] << 13);
        wire [31:0] b = a ^ (a >> 17);
        always @(posedge clk) s[i] <= b ^ (b << 5);
    end endgenerate
    reg [47:0] p [0:7];
    reg [24:0] a [0:7];
    reg [17:0] b [0:7];
    reg [42:0] m [0:7];
    integer j;
    initial for (j = 0; j < 8; j = j + 1) p[j] = 48'd0;
    generate for (i = 0; i < 8; i = i + 1) begin : mac
        always @(posedge clk) begin
            a[i] <= s[i / 2][24:0];
            b[i] <= s[i / 2 + 1][31:14];
            m[i] <= $signed(a[i]) * $signed(b[i]);
            p[i] <= p[i] + {{5{m[i][42]}}, m[i]};
        end
    end endgenerate
    wire [47:0] r = p[0] ^ p[1] ^ p[2] ^ p[3] ^ p[4] ^ p[5] ^ p[6] ^ p[7];
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= r[3:0] ^ r[47:44];
    assign led = l;
endmodule
