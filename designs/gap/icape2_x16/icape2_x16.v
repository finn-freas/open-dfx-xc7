module icape2_x16 (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [31:0] y;

    wire [31:0] o;
    ICAPE2 #(.ICAP_WIDTH("X16")) u_icap (.CLK(clk), .CSIB(s[31]), .RDWRB(s[30]), .I(s[63:32]), .O(o));
    assign y = o;
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
