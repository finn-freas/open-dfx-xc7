module pw_bram40 (input wire clk, output wire [3:0] led);
    reg [31:0] s [0:40];
    integer k;
    initial for (k = 0; k <= 40; k = k + 1) s[k] = 32'h1234567 + k * 32'h9e3779b9;
    genvar i;
    generate for (i = 0; i <= 40; i = i + 1) begin : xs
        wire [31:0] a = s[i] ^ (s[i] << 13);
        wire [31:0] b = a ^ (a >> 17);
        always @(posedge clk) s[i] <= b ^ (b << 5);
    end endgenerate
    wire [31:0] q [0:39];
    generate for (i = 0; i < 40; i = i + 1) begin : ram
        (* ram_style = "block" *) reg [31:0] mem [0:1023];
        reg [31:0] rd = 32'd0;
        always @(posedge clk) begin
            if (s[i][0]) mem[s[i][10:1]] <= s[i + 1];
            rd <= mem[s[i][20:11]];
        end
        assign q[i] = rd;
    end endgenerate
    wire [31:0] r = q[0] ^ q[1] ^ q[2] ^ q[3] ^ q[4] ^ q[5] ^ q[6] ^ q[7] ^ q[8] ^ q[9] ^ q[10] ^ q[11] ^ q[12] ^ q[13] ^ q[14] ^ q[15] ^ q[16] ^ q[17] ^ q[18] ^ q[19] ^ q[20] ^ q[21] ^ q[22] ^ q[23] ^ q[24] ^ q[25] ^ q[26] ^ q[27] ^ q[28] ^ q[29] ^ q[30] ^ q[31] ^ q[32] ^ q[33] ^ q[34] ^ q[35] ^ q[36] ^ q[37] ^ q[38] ^ q[39];
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= r[3:0] ^ r[31:28];
    assign led = l;
endmodule
