module top (input wire clk, output reg [3:0] led, output reg [3:0] rgb);
    reg [27:0] count = 28'd0;
    wire [3:0] rp1_out;
    wire [3:0] rp2_out;
    always @(posedge clk) begin
        count <= count + 28'd1;
        led <= rp1_out;
        rgb <= rp2_out;
    end
    rm_rp1 u_rp1 (.clk(clk), .din(count[27:20]), .dout(rp1_out));
    rm_rp2 u_rp2 (.clk(clk), .din(count[19:12]), .dout(rp2_out));
endmodule
