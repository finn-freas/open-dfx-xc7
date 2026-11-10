module latch_ldce_ginv (input [3:0] sw, input [3:0] btn, output [3:0] led);
    wire g = btn[0] ^ btn[1];
    genvar i;
    generate for (i = 0; i < 4; i = i + 1) begin : l
        LDCE #(.INIT(1'b1), .IS_G_INVERTED(1'b1)) u (.Q(led[i]), .D(sw[i] ^ sw[(i + 1) % 4]), .G(g),
            .GE(btn[2]), .CLR(btn[3]));
    end endgenerate
endmodule
