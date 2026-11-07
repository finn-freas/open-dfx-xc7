module blinky_s100 (
    input  wire       clk,
    output wire [3:0] led
);
    reg [27:0] count = 28'd0;
    always @(posedge clk) count <= count + 28'd1;
    assign led = count[27:24];
endmodule
