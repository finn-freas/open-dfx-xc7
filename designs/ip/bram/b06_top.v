module b06_top (input wire clk, input wire sw, output wire led);
    reg [10:0] a = 0;
    always @(posedge clk) a <= a + 1'b1;
    wire [65:0] wd = {6{a}};
    wire [63:0] qa;
    b06_mem u_mem (.clka(clk), .addra(a), .douta(qa));
    wire x = ^qa;
    reg r = 1'b0;
    always @(posedge clk) r <= x;
    assign led = r;
endmodule
