module x_interm (input wire clk, input wire din, output wire [3:0] led);
    reg [3:0] q = 4'd0;
    always @(posedge clk) q <= {q[2:0], din};
    assign led = q;
endmodule
