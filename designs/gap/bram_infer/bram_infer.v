module bram_infer (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [31:0] y;

    reg [31:0] mem [0:1023];
    reg [31:0] q = 32'd0;
    always @(posedge clk) begin
        if (s[0]) mem[s[10:1]] <= s[63:32];
        q <= mem[s[20:11]];
    end
    assign y = q;
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 32; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
