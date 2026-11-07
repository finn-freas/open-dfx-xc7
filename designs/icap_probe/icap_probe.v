module icap_probe (input wire clk, output reg [3:0] led);
    reg [31:0] count = 32'd0;
    wire [31:0] o;
    always @(posedge clk) begin
        count <= count + 32'd1;
        led <= o[3:0] ^ o[31:28];
    end
    ICAPE2 #(.ICAP_WIDTH("X32")) icap (.CLK(clk), .CSIB(count[31]), .RDWRB(count[30]), .I(count), .O(o));
endmodule
