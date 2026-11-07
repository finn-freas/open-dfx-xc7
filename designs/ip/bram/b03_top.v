module b03_top (input wire clk, input wire sw, output wire led);
    reg [10:0] a = 0;
    always @(posedge clk) a <= a + 1'b1;
    wire [21:0] wd = {2{a}};
    wire [15:0] qa, qb;
    b03_mem u_mem (.clka(clk), .wea(sw), .addra(a), .dina(wd[15:0]), .douta(qa),
                      .clkb(clk), .web(~sw), .addrb(~a), .dinb(~wd[15:0]), .doutb(qb));
    wire x = ^qa ^ ^qb;
    reg r = 1'b0;
    always @(posedge clk) r <= x;
    assign led = r;
endmodule
