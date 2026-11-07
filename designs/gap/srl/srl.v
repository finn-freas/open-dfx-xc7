module srl (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [2:0] y;

    wire q16, q32a, q31a, q32b;
    SRL16E #(.INIT(16'h1234)) u_srl16 (.CLK(clk), .CE(s[0]), .D(s[1]), .A0(s[2]), .A1(s[3]), .A2(s[4]), .A3(s[5]), .Q(q16));
    SRLC32E #(.INIT(32'h1234_5678)) u_srl32a (.CLK(clk), .CE(s[6]), .D(s[7]), .A(s[12:8]), .Q(q32a), .Q31(q31a));
    SRLC32E #(.INIT(32'h9abc_def0)) u_srl32b (.CLK(clk), .CE(s[6]), .D(q31a), .A(s[17:13]), .Q(q32b), .Q31());
    assign y = {q16, q32a, q32b};
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
