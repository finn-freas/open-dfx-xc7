module dsp_infer (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [47:0] y;

    reg signed [24:0] a = 0;
    reg signed [17:0] b = 0;
    reg signed [47:0] c = 0, m = 0, p = 0;
    always @(posedge clk) begin
        a <= s[24:0];
        b <= s[42:25];
        c <= {s[63:43], s[26:0]};
        m <= a * b;
        p <= m + c;
    end
    assign y = p;
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 48; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
