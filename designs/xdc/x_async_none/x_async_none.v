module x_async_none (input wire clk, input wire [3:0] sw, output wire [3:0] led);
    reg s1 = 1'b0;
    reg s2 = 1'b0;
    reg s3 = 1'b0;
    always @(posedge clk) begin
        s1 <= sw[0];
        s2 <= s1;
        s3 <= s2;
    end
    assign led = {3'd0, s3};
endmodule
