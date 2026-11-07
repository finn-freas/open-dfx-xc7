module x_arst (input wire clk, input wire [3:0] sw, output wire [3:0] led);
    reg r1 = 1'b1, r2 = 1'b1;
    always @(posedge clk) begin
        r1 <= sw[0];
        r2 <= r1;
    end
    reg [7:0] cnt;
    always @(posedge clk or posedge r2)
        if (r2) cnt <= 8'd0;
        else cnt <= cnt + {7'd0, sw[1]};
    reg [3:0] q;
    always @(posedge clk or posedge r2)
        if (r2) q <= 4'hf;
        else q <= cnt[7:4] ^ {4{sw[2]}};
    assign led = q ^ cnt[3:0];
endmodule
