module drc_ffclk (input wire clk, input wire [1:0] sw, output wire [3:0] led);
    reg [23:0] c = 24'd0;
    always @(posedge clk) c <= c + 24'd1 + sw;
    reg div = 1'b0;
    always @(posedge clk) div <= ~div;
    reg [31:0] r = 32'd0;
    always @(posedge div) r <= {r[30:0], sw[0] ^ r[31]};
    assign led = r[31:28] ^ c[23:20];
endmodule
