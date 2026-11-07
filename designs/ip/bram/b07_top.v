module b07_top (input wire clk, input wire sw, output wire led);
    reg [8:0] a = 0;
    always @(posedge clk) a <= a + 1'b1;
    wire [71:0] wd = {8{a}};
    wire [71:0] qa;
    b07_mem u_mem (.clka(clk), .wea(sw), .addra(a), .dina(wd[71:0]), .douta(qa));
    wire x = ^qa;
    reg r = 1'b0;
    always @(posedge clk) r <= x;
    assign led = r;
endmodule
