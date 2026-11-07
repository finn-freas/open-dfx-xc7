module rm_slot (input wire clk, input wire valid, input wire [9:0] funct, input wire [31:0] rs1, input wire [31:0] rs2, output wire [31:0] rd, output wire ready);
    reg [31:0] rd_q = 32'd0;
    reg ready_q = 1'b0;
    always @(posedge clk) begin
        ready_q <= valid;
        if (valid) rd_q <= rs1 ^ rs2;
    end
    assign rd = rd_q;
    assign ready = ready_q;
endmodule
