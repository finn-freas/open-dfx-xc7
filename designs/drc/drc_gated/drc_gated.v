module drc_gated (input wire clk, input wire [1:0] sw, output wire [3:0] led);
    reg [23:0] c = 24'd0;
    always @(posedge clk) c <= c + 24'd1 + sw;
    wire gclk = clk & sw[0];
    reg [3:0] g = 4'd0;
    always @(posedge gclk) g <= g + 4'd1;
    assign led = {c[23:22], g[3:2]};
endmodule
