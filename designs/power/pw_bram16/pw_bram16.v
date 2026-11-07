module pw_bram16 (input wire clk, output wire [3:0] led);
    reg [31:0] s [0:16];
    integer k;
    initial for (k = 0; k <= 16; k = k + 1) s[k] = 32'h1234567 + k * 32'h9e3779b9;
    genvar i;
    generate for (i = 0; i <= 16; i = i + 1) begin : xs
        wire [31:0] a = s[i] ^ (s[i] << 13);
        wire [31:0] b = a ^ (a >> 17);
        always @(posedge clk) s[i] <= b ^ (b << 5);
    end endgenerate
    wire [31:0] q [0:15];
    generate for (i = 0; i < 16; i = i + 1) begin : ram
        (* ram_style = "block" *) reg [31:0] mem [0:1023];
        reg [31:0] rd = 32'd0;
        always @(posedge clk) begin
            if (s[i][0]) mem[s[i][10:1]] <= s[i + 1];
            rd <= mem[s[i][20:11]];
        end
        assign q[i] = rd;
    end endgenerate
    wire [31:0] r = q[0] ^ q[1] ^ q[2] ^ q[3] ^ q[4] ^ q[5] ^ q[6] ^ q[7] ^ q[8] ^ q[9] ^ q[10] ^ q[11] ^ q[12] ^ q[13] ^ q[14] ^ q[15];
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= r[3:0] ^ r[31:28];
    assign led = l;
endmodule
