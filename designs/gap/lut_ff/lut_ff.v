module lut_ff (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [4:0] y;

    wire lo;
    LUT6 #(.INIT(64'h6996_9669_9669_6996)) u_lut (.I0(s[0]), .I1(s[1]), .I2(s[2]), .I3(s[3]), .I4(s[4]), .I5(s[5]), .O(lo));
    wire [3:0] fq;
    FDRE #(.INIT(1'b0)) u_fdre (.C(clk), .CE(s[6]), .R(s[7]), .D(lo), .Q(fq[0]));
    FDSE #(.INIT(1'b1)) u_fdse (.C(clk), .CE(s[8]), .S(s[9]), .D(lo), .Q(fq[1]));
    FDCE #(.INIT(1'b0)) u_fdce (.C(clk), .CE(s[10]), .CLR(s[11]), .D(lo), .Q(fq[2]));
    FDPE #(.INIT(1'b1)) u_fdpe (.C(clk), .CE(s[12]), .PRE(s[13]), .D(lo), .Q(fq[3]));
    assign y = {fq, lo};
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 5; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
