module drc_lutlp (input wire clk, input wire [1:0] sw, output wire [3:0] led);
    reg [23:0] c = 24'd0;
    always @(posedge clk) c <= c + 24'd1 + sw;
    wire x, y;
    (* DONT_TOUCH = "yes" *) LUT2 #(.INIT(4'h6)) u_l1 (.O(x), .I0(y), .I1(sw[0]));
    (* DONT_TOUCH = "yes" *) LUT2 #(.INIT(4'h6)) u_l2 (.O(y), .I0(x), .I1(sw[1]));
    assign led = {c[23:21], x};
endmodule
