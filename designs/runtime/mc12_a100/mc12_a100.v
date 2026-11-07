module mc12_a100 #(parameter N = 12) (
    input wire clk, input wire uart_txd_in, output wire uart_rxd_out, output wire [3:0] led
);
    reg [N-1:0] rx_d = {N{1'b1}};
    always @(posedge clk) rx_d <= {rx_d[N-2:0], uart_txd_in};
    wire [N-1:0] tx;
    wire [4*N-1:0] leds;
    genvar i;
    generate for (i = 0; i < N; i = i + 1) begin : g_core
        qor_rv_big #(.MEM_INIT("main.hex"), .MEM_WORDS(4096)) u_core (
            .clk(clk), .uart_txd_in(rx_d[i]), .uart_rxd_out(tx[i]), .led(leds[4*i +: 4]));
    end endgenerate
    reg tx_q = 1'b1;
    reg [3:0] led_q = 4'd0;
    reg [3:0] led_x;
    integer k;
    always @(*) begin
        led_x = 4'd0;
        for (k = 0; k < N; k = k + 1) led_x = led_x ^ leds[4*k +: 4];
    end
    always @(posedge clk) begin
        tx_q <= ^tx;
        led_q <= led_x;
    end
    assign uart_rxd_out = tx_q;
    assign led = led_q;
endmodule
