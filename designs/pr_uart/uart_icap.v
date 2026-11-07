module uart_rx #(parameter CLKS_PER_BIT = 100) (
    input wire clk, input wire rx, output reg valid = 1'b0, output reg [7:0] data = 8'd0
);
    reg [1:0] sync = 2'b11;
    reg [15:0] cnt = 16'd0;
    reg [3:0] bitn = 4'd0;
    reg busy = 1'b0;
    always @(posedge clk) begin
        sync <= {sync[0], rx};
        valid <= 1'b0;
        if (!busy) begin
            if (!sync[1]) begin
                busy <= 1'b1;
                cnt <= CLKS_PER_BIT / 2;
                bitn <= 4'd0;
            end
        end else if (cnt != 0) begin
            cnt <= cnt - 16'd1;
        end else begin
            cnt <= CLKS_PER_BIT - 1;
            bitn <= bitn + 4'd1;
            if (bitn == 4'd0) begin
                if (sync[1]) busy <= 1'b0;
            end else if (bitn <= 4'd8) begin
                data <= {sync[1], data[7:1]};
            end else begin
                busy <= 1'b0;
                valid <= sync[1];
            end
        end
    end
endmodule

module uart_tx #(parameter CLKS_PER_BIT = 100) (
    input wire clk, input wire start, input wire [7:0] data, output reg tx = 1'b1, output wire busy
);
    reg [9:0] sh = 10'h3ff;
    reg [15:0] cnt = 16'd0;
    reg [3:0] left = 4'd0;
    assign busy = left != 4'd0;
    always @(posedge clk) begin
        if (!busy) begin
            if (start) begin
                sh <= {1'b1, data, 1'b0};
                left <= 4'd11;
                cnt <= 16'd0;
            end
        end else if (cnt != 0) begin
            cnt <= cnt - 16'd1;
        end else begin
            tx <= sh[0];
            sh <= {1'b1, sh[9:1]};
            left <= left - 4'd1;
            cnt <= CLKS_PER_BIT - 1;
        end
    end
endmodule

module uart_icap #(parameter CLKS_PER_BIT = 100, parameter SWAP = 1, parameter RBUF = 16) (
    input wire clk, input wire rx, output wire tx, output reg [7:0] status = 8'd0
);
    wire rx_valid;
    wire [7:0] rx_data;
    uart_rx #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_rx (.clk(clk), .rx(rx), .valid(rx_valid), .data(rx_data));
    reg tx_start = 1'b0;
    reg [7:0] tx_data = 8'd0;
    wire tx_busy;
    uart_tx #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_tx (.clk(clk), .start(tx_start), .data(tx_data), .tx(tx), .busy(tx_busy));

    function [31:0] bswap(input [31:0] w);
        integer i;
        begin
            for (i = 0; i < 32; i = i + 1)
                bswap[i] = SWAP ? w[(i & ~7) + (7 - (i & 7))] : w[i];
        end
    endfunction

    localparam S_CMD = 0, S_LEN = 1, S_WDATA = 2, S_RSETUP = 3, S_READ = 4, S_SEND = 5, S_ACK = 6;
    reg [2:0] state = S_CMD;
    reg [7:0] cmd = 8'd0;
    reg [31:0] len = 32'd0;
    reg [31:0] word = 32'd0;
    reg [1:0] nbyte = 2'd0;
    reg [31:0] done = 32'd0;
    reg icap_csib = 1'b1;
    reg icap_rdwrb = 1'b0;
    reg [31:0] icap_i = 32'd0;
    wire [31:0] icap_o;
    reg [31:0] rbuf [0:RBUF-1];
    reg [4:0] ridx = 5'd0;
    reg [4:0] rcnt = 5'd0;
    reg [2:0] sbyte = 3'd0;
    reg [31:0] sword = 32'd0;

    ICAPE2 #(.ICAP_WIDTH("X32")) u_icap (.CLK(clk), .CSIB(icap_csib), .RDWRB(icap_rdwrb), .I(icap_i), .O(icap_o));

    always @(posedge clk) begin
        tx_start <= 1'b0;
        icap_csib <= 1'b1;
        case (state)
            S_CMD: if (rx_valid) begin
                cmd <= rx_data;
                nbyte <= 2'd0;
                if (rx_data == "W" || rx_data == "R") state <= S_LEN;
            end
            S_LEN: if (rx_valid) begin
                len <= {len[23:0], rx_data};
                nbyte <= nbyte + 2'd1;
                if (nbyte == 2'd3) begin
                    done <= 32'd0;
                    if (cmd == "W") state <= S_WDATA;
                    else state <= S_RSETUP;
                end
            end
            S_WDATA: begin
                icap_rdwrb <= 1'b0;
                if (done == len) begin
                    state <= S_ACK;
                    sword <= done;
                    sbyte <= 3'd0;
                end else if (rx_valid) begin
                    word <= {word[23:0], rx_data};
                    nbyte <= nbyte + 2'd1;
                    if (nbyte == 2'd3) begin
                        icap_i <= bswap({word[23:0], rx_data});
                        icap_csib <= 1'b0;
                        done <= done + 32'd1;
                        status <= status + 8'd1;
                    end
                end
            end
            S_RSETUP: begin
                icap_rdwrb <= 1'b1;
                ridx <= 5'd0;
                rcnt <= (len > RBUF) ? RBUF : len[4:0];
                state <= S_READ;
            end
            S_READ: begin
                if (ridx == rcnt) begin
                    state <= S_SEND;
                    ridx <= 5'd0;
                    sbyte <= 3'd0;
                    sword <= bswap(rbuf[0]);
                end else begin
                    icap_csib <= 1'b0;
                    rbuf[ridx] <= icap_o;
                    ridx <= ridx + 5'd1;
                end
            end
            S_SEND: if (!tx_busy && !tx_start) begin
                if (ridx == rcnt) begin
                    icap_rdwrb <= 1'b0;
                    state <= S_CMD;
                end else begin
                    tx_data <= sword[31:24];
                    sword <= {sword[23:0], 8'd0};
                    tx_start <= 1'b1;
                    sbyte <= sbyte + 3'd1;
                    if (sbyte == 3'd3) begin
                        sbyte <= 3'd0;
                        ridx <= ridx + 5'd1;
                        sword <= bswap(rbuf[ridx + 5'd1]);
                    end
                end
            end
            S_ACK: if (!tx_busy && !tx_start) begin
                tx_data <= (sbyte == 3'd0) ? "K" : sword[31:24];
                if (sbyte != 3'd0) sword <= {sword[23:0], 8'd0};
                tx_start <= 1'b1;
                sbyte <= sbyte + 3'd1;
                if (sbyte == 3'd4) state <= S_CMD;
            end
        endcase
    end
endmodule
