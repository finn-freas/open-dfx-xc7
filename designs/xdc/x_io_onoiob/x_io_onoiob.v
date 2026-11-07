module x_io_onoiob (input wire clk, input wire [3:0] btn, output wire [3:0] led);
    reg [3:0] c = 4'd0;
    always @(posedge clk) c <= c + btn;
    reg [3:0] q = 4'd0;
    always @(posedge clk) q <= c;
    assign led = q;
endmodule
