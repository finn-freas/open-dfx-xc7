module qor_bram #(
    parameter BIG_AW = 14,
    parameter NBANK = 8,
    parameter BANK_AW = 10
) (
    input wire clk, input wire uart_txd_in, output wire uart_rxd_out, output wire [3:0] led
);
    reg [63:0] lfsr = 64'hfedc_ba98_7654_3210;
    always @(posedge clk) lfsr <= {lfsr[62:0], lfsr[63] ^ lfsr[62] ^ lfsr[60] ^ lfsr[59]};

    reg [1:0] we_s = 2'b11;
    always @(posedge clk) we_s <= {we_s[0], uart_txd_in};
    wire we = !we_s[1];

    reg [31:0] big [0:(1<<BIG_AW)-1];
    reg [BIG_AW-1:0] big_ra = 0;
    reg [31:0] big_q = 32'd0;
    always @(posedge clk) begin
        if (we) big[lfsr[BIG_AW+19:20]] <= lfsr[31:0];
        big_ra <= big_ra + 1'b1;
        big_q <= big[big_ra];
    end

    wire [36*NBANK-1:0] bq_all;
    wire [36*(NBANK+1)-1:0] bsum_all;
    assign bsum_all[35:0] = 36'd0;
    genvar g;
    generate for (g = 0; g < NBANK; g = g + 1) begin : bank
        reg [35:0] mem [0:(1<<BANK_AW)-1];
        reg [BANK_AW-1:0] ra = g * 37;
        reg [35:0] q = 36'd0;
        reg [35:0] bq = 36'd0;
        reg [35:0] bsum = 36'd0;
        wire [35:0] prev = bsum_all[36*g+35:36*g];
        wire [35:0] wd = (g == 0) ? {4'd0, big_q} : prev;
        always @(posedge clk) begin
            mem[lfsr[BANK_AW-1+g:g]] <= wd ^ lfsr[35:0];
            ra <= ra + (g + 1);
            q <= mem[ra];
        end
        always @(posedge clk) begin
            bq <= q;
            bsum <= prev + q + {q[17:0], q[35:18]};
        end
        assign bq_all[36*g+35:36*g] = bq;
        assign bsum_all[36*(g+1)+35:36*(g+1)] = bsum;
    end endgenerate

    reg [35:0] y = 36'd0;
    reg [3:0] led_r = 4'd0;
    reg tx_r = 1'b1;
    always @(posedge clk) begin
        y <= bsum_all[36*NBANK+35:36*NBANK] ^ bq_all[35:0];
        led_r <= y[3:0] ^ y[7:4] ^ y[11:8] ^ y[15:12] ^ y[19:16] ^ y[23:20] ^ y[27:24] ^ y[31:28] ^ y[35:32];
        tx_r <= ^y;
    end
    assign led = led_r;
    assign uart_rxd_out = tx_r;
endmodule
