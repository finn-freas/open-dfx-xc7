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
