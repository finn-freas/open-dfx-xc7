module drc_vref (input wire clk, input wire [1:0] sw, output wire [3:0] led, input wire d, output wire q);
    reg [23:0] c = 24'd0;
    always @(posedge clk) c <= c + 24'd1 + sw;
    reg r = 1'b0;
    always @(posedge clk) r <= d ^ c[3];
    assign q = r;
    assign led = c[23:20];
endmodule
