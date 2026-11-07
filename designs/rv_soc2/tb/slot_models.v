module rm_slot (input wire clk, input wire valid, input wire [9:0] funct, input wire [31:0] rs1, input wire [31:0] rs2, output wire [31:0] rd, output wire ready);
    wire [31:0] c_rd;
    wire c_ready;
    reg [31:0] rd_q = 32'd0;
    reg ready_q = 1'b0;
    rm_core core (.valid(valid), .funct(funct), .rs1(rs1), .rs2(rs2), .rd(c_rd), .ready(c_ready));
    always @(posedge clk) begin
        rd_q <= c_rd;
        ready_q <= c_ready;
    end
    assign rd = rd_q;
    assign ready = ready_q;
endmodule

module rm_slot2 (input wire clk, input wire valid, input wire [9:0] funct, input wire [31:0] rs1, input wire [31:0] rs2, output wire [31:0] rd, output wire ready);
    wire [31:0] c_rd;
    wire c_ready;
    reg [31:0] rd_q = 32'd0;
    reg ready_q = 1'b0;
    rm_core2 core (.valid(valid), .funct(funct), .rs1(rs1), .rs2(rs2), .rd(c_rd), .ready(c_ready));
    always @(posedge clk) begin
        rd_q <= c_rd;
        ready_q <= c_ready;
    end
    assign rd = rd_q;
    assign ready = ready_q;
endmodule
