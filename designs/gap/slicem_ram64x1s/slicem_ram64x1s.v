module slicem_ram64x1s (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire o;
    RAM64X1S #(.INIT(64'h0123_4567_89ab_cdef)) u_ram (.WCLK(clk), .WE(s[0]), .D(s[1]),
        .A0(s[2]), .A1(s[3]), .A2(s[4]), .A3(s[5]), .A4(s[6]), .A5(s[7]), .O(o));
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= {l[2:0], o};
    assign led = l;
endmodule
