module x_srl (input wire clk, input wire [3:0] sw, output wire [3:0] led);
    reg [3:0] a;
    reg [3:0] sh [0:7];
    reg [3:0] b;
    integer i;
    always @(posedge clk) begin
        a <= sw ^ b;
        sh[0] <= a;
        for (i = 1; i < 8; i = i + 1)
            sh[i] <= sh[i - 1];
        b <= sh[7] + a;
    end
    assign led = b;
endmodule
