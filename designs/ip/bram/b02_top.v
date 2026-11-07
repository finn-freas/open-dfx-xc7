module b02_top (input wire clk, input wire sw, output wire led);
    reg [11:0] a = 0;
    always @(posedge clk) a <= a + 1'b1;
    wire [11:0] wd = {1{a}};
    wire [7:0] qa;
    b02_mem u_mem (.clka(clk), .addra(a), .douta(qa));
    wire x = ^qa;
    reg r = 1'b0;
    always @(posedge clk) r <= x;
    assign led = r;
endmodule
