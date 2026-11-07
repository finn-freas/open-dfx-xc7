module top (input wire clk, input wire uart_txd_in, output wire uart_rxd_out, output reg [3:0] led);
    reg [27:0] count = 28'd0;
    wire [3:0] rm_out;
    always @(posedge clk) begin
        count <= count + 28'd1;
        led <= rm_out;
    end
    rm_slot u_rm (.clk(clk), .din(count[27:20]), .dout(rm_out));
    uart_icap u_bridge (.clk(clk), .rx(uart_txd_in), .tx(uart_rxd_out), .status());
endmodule
