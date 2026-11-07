module b05_top (input wire clk, input wire sw, output wire led);
    reg [9:0] a = 0;
    always @(posedge clk) a <= a + 1'b1;
    wire [19:0] wd = {2{a}};
    wire [17:0] qa;
    b05_mem u_mem (.clka(clk), .addra(a), .douta(qa));
    wire x = ^qa;
    reg r = 1'b0;
    always @(posedge clk) r <= x;
    assign led = r;
endmodule
