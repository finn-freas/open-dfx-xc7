module rm_slot (input wire clk, input wire [15:0] din, output reg [15:0] dout);
    reg [31:0] a = 32'd0, b = 32'd0;
    reg c = 1'b0;
    reg [31:0] s1 = 32'd0, s2 = 32'd0;
    reg [16:0] s3 = 17'd0;
    reg lt = 1'b0;
    always @(posedge clk) begin
        a <= {din, ~din};
        b <= {din ^ 16'h5A5A, din[7:0], din[15:8]};
        c <= din[3];
        s1 <= a + b;
        s2 <= a - b;
        s3 <= a[15:0] + b[31:16] + c;
        lt <= a < b;
        dout <= s1[31:16] ^ s1[15:0] ^ s2[31:16] ^ s2[15:0] ^ s3[15:0] ^ {s3[16], 14'd0, lt};
    end
endmodule
