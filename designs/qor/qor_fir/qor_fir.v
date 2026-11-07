module qor_fir #(
    parameter TAPS = 32,
    parameter W = 16
) (
    input wire clk, input wire uart_txd_in, output wire uart_rxd_out, output wire [3:0] led
);
    reg [63:0] lfsr = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) lfsr <= {lfsr[62:0], lfsr[63] ^ lfsr[62] ^ lfsr[60] ^ lfsr[59]};

    reg [1:0] load_s = 2'b11;
    always @(posedge clk) load_s <= {load_s[0], uart_txd_in};
    wire load = !load_s[1];

    reg signed [W-1:0] coef [0:TAPS-1];
    integer i;
    initial for (i = 0; i < TAPS; i = i + 1) coef[i] = (i * 1237 + 91) & 16'h7fff;
    always @(posedge clk) if (load) begin
        coef[0] <= lfsr[W-1:0];
        for (i = 1; i < TAPS; i = i + 1) coef[i] <= coef[i-1];
    end

    reg signed [W-1:0] x0 = 0;
    always @(posedge clk) x0 <= lfsr[W+7:8];

    reg signed [W-1:0] xd [0:TAPS-1];
    reg signed [W-1:0] xr [0:TAPS-1];
    reg signed [2*W-1:0] m [0:TAPS-1];
    reg signed [2*W+7:0] acc [0:TAPS-1];
    initial for (i = 0; i < TAPS; i = i + 1) begin
        xd[i] = 0; xr[i] = 0; m[i] = 0; acc[i] = 0;
    end
    always @(posedge clk) begin
        xd[0] <= x0;
        for (i = 1; i < TAPS; i = i + 1) xd[i] <= xr[i-1];
        for (i = 0; i < TAPS; i = i + 1) begin
            xr[i] <= xd[i];
            m[i] <= xr[i] * coef[i];
        end
        acc[0] <= m[0];
        for (i = 1; i < TAPS; i = i + 1) acc[i] <= acc[i-1] + m[i];
    end

    reg [2*W+7:0] y = 0;
    reg [3:0] led_r = 4'd0;
    reg tx_r = 1'b1;
    always @(posedge clk) begin
        y <= acc[TAPS-1];
        led_r <= y[3:0] ^ y[7:4] ^ y[11:8] ^ y[15:12] ^ y[19:16] ^ y[23:20] ^ y[27:24] ^ y[31:28] ^ y[35:32] ^ y[39:36];
        tx_r <= ^y;
    end
    assign led = led_r;
    assign uart_rxd_out = tx_r;
endmodule
