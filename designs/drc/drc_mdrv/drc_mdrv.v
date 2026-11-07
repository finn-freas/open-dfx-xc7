module drc_mdrv (input wire clk, input wire [1:0] sw, output wire [3:0] led);
    reg [23:0] c = 24'd0;
    always @(posedge clk) c <= c + 24'd1 + sw;
    wire m;
    (* DONT_TOUCH = "yes" *) LUT1 #(.INIT(2'b10)) u_d1 (.O(m), .I0(sw[0]));
    (* DONT_TOUCH = "yes" *) LUT1 #(.INIT(2'b10)) u_d2 (.O(m), .I0(sw[1]));
    assign led = {c[23:21], m};
endmodule
