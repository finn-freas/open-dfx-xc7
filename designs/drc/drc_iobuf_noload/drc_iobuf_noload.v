module drc_iobuf_noload (input wire clk, input wire [1:0] sw, output wire [3:0] led, inout wire pad);
    reg [23:0] c = 24'd0;
    always @(posedge clk) c <= c + 24'd1 + sw;
    wire io_o;
    (* DONT_TOUCH = "yes" *) IOBUF u_io (.IO(pad), .I(c[5]), .T(c[6]), .O(io_o));
    assign led = c[23:20];
endmodule
