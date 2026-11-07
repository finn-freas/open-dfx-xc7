module x_iodly_fall (input wire clk, input wire [3:0] sw, output wire [7:0] ja, output wire [3:0] led);
    reg [7:0] r = 8'd0;
    always @(posedge clk) r <= {sw, sw};
    wire [7:0] u0 = (r ^ {r[0:0], r[7:1]}) + r + 8'd0;
    wire [7:0] u1 = (u0 ^ {u0[3:0], u0[7:4]}) + u0 + 8'd177;
    reg [7:0] o = 8'd0;
    always @(posedge clk) o <= u1;
    assign ja = o;
    assign led = r[3:0];
endmodule
