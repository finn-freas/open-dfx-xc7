module dna_port2 (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [1:0] y;

    reg div = 1'b0;
    always @(posedge clk) div <= ~div;
    wire gd, d;
    BUFG u_bufg (.I(div), .O(gd));
    reg rd = 1'b1, sh = 1'b0;
    always @(posedge gd) begin rd <= 1'b0; sh <= ~sh; end
    DNA_PORT u_dna (.CLK(gd), .READ(rd), .SHIFT(sh), .DIN(d), .DOUT(d));
    assign y = {d, sh};
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
