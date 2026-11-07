module x_io_pull (input wire clk, input wire [3:0] btn, output wire [3:0] led);
    reg [3:0] q = 4'd0;
    always @(posedge clk) q <= btn;
    assign led = q;
endmodule
