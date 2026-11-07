module b01_top (input wire clk, input wire sw, output wire led);
    reg [9:0] a = 0;
    always @(posedge clk) a <= a + 1'b1;
    wire [39:0] wd = {4{a}};
    wire [31:0] qa;
    b01_mem u_mem (.clka(clk), .wea(sw), .addra(a), .dina(wd[31:0]), .douta(qa));
    wire x = ^qa;
    reg r = 1'b0;
    always @(posedge clk) r <= x;
    assign led = r;
endmodule
