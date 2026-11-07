module pw_io24_p5 (input wire clk, output wire [3:0] led, output wire [23:0] io);
    reg [31:0] s [0:0];
    integer k;
    initial for (k = 0; k <= 0; k = k + 1) s[k] = 32'h1234567 + k * 32'h9e3779b9;
    genvar i;
    generate for (i = 0; i <= 0; i = i + 1) begin : xs
        wire [31:0] a = s[i] ^ (s[i] << 13);
        wire [31:0] b = a ^ (a >> 17);
        always @(posedge clk) s[i] <= b ^ (b << 5);
    end endgenerate
    reg [23:0] o = 24'd0;
    always @(posedge clk) o <= s[0][23:0];
    assign io = o;
    assign led = s[0][31:28];
endmodule
