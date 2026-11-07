module bufio_iddr (input wire clk, input wire din, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [1:0] y;

    wire cio, q1, q2;
    BUFIO u_bufio (.I(clk), .O(cio));
    IDDR #(.DDR_CLK_EDGE("SAME_EDGE_PIPELINED")) u_iddr (.C(cio), .CE(1'b1), .D(din), .R(1'b0), .S(1'b0), .Q1(q1), .Q2(q2));
    assign y = {q1, q2};
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 2; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
