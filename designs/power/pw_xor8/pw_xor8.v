module pw_xor8 (input wire clk, output wire [3:0] led);
    reg [31:0] s [0:7];
    integer k;
    initial for (k = 0; k <= 7; k = k + 1) s[k] = 32'h1234567 + k * 32'h9e3779b9;
    genvar i;
    generate for (i = 0; i <= 7; i = i + 1) begin : xs
        wire [31:0] a = s[i] ^ (s[i] << 13);
        wire [31:0] b = a ^ (a >> 17);
        always @(posedge clk) s[i] <= b ^ (b << 5);
    end endgenerate
    wire [31:0] r = s[0] ^ s[1] ^ s[2] ^ s[3] ^ s[4] ^ s[5] ^ s[6] ^ s[7];
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= r[3:0] ^ r[31:28];
    assign led = l;
endmodule
