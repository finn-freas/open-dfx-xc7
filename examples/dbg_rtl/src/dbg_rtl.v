module uart_like (input wire clk, input wire go, output reg busy = 1'b0, output wire tx);
    (* mark_debug = "true" *) reg [2:0] state = 3'd0;
    (* mark_debug = "true" *) reg [7:0] cnt = 8'd0;
    reg [9:0] sh = 10'h3ff;
    assign tx = sh[0];
    always @(posedge clk) begin
        cnt <= cnt + 1'b1;
        case (state)
            3'd0: if (go) begin state <= 3'd1; busy <= 1'b1; sh <= {1'b1, cnt, 1'b0}; end
            3'd1: if (cnt[3:0] == 4'hf) state <= 3'd2;
            3'd2: begin sh <= {1'b1, sh[9:1]}; state <= 3'd3; end
            3'd3: if (sh[9:1] == 9'h1ff) state <= 3'd4; else state <= 3'd2;
            default: begin busy <= 1'b0; state <= 3'd0; end
        endcase
    end
endmodule
module dbg_rtl (input wire clk, input wire [3:0] sw, output wire [3:0] led);
    wire busy, tx;
    uart_like u_core (.clk(clk), .go(sw[0]), .busy(busy), .tx(tx));
    assign led = {2'b00, busy, tx};
endmodule
