module ram64x1d (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [1:0] y;

    wire spo, dpo;
    RAM64X1D #(.INIT(64'h0123_4567_89ab_cdef)) u_ram (.WCLK(clk), .WE(s[0]), .D(s[1]),
        .A0(s[2]), .A1(s[3]), .A2(s[4]), .A3(s[5]), .A4(s[6]), .A5(s[7]),
        .DPRA0(s[8]), .DPRA1(s[9]), .DPRA2(s[10]), .DPRA3(s[11]), .DPRA4(s[12]), .DPRA5(s[13]),
        .SPO(spo), .DPO(dpo));
    assign y = {spo, dpo};
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
