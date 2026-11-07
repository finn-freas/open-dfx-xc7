module b04_top (input wire clk, input wire sw, output wire led);
    reg [8:0] a = 0;
    always @(posedge clk) a <= a + 1'b1;
    wire [35:0] wd = {4{a}};
    wire [35:0] qb;
    b04_mem u_mem (.clka(clk), .wea(sw), .addra(a), .dina(wd[35:0]),
                      .clkb(clk), .addrb(~a), .doutb(qb));
    wire x = ^qb;
    reg r = 1'b0;
    always @(posedge clk) r <= x;
    assign led = r;
endmodule
