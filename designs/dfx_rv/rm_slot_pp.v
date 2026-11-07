module rm_slot (input wire clk, input wire valid, input wire [9:0] funct, input wire [31:0] rs1, input wire [31:0] rs2, output wire [31:0] rd, output wire ready);
    wire [31:0] c_rd;
    wire c_ready;
    rm_core core (.valid(valid), .funct(funct), .rs1(rs1), .rs2(rs2), .rd(c_rd), .ready(c_ready));
    assign rd = c_rd;
    FDRE r_ready_0 (.C(clk), .CE(1'b1), .R(1'b0), .D(c_ready), .Q(ready));
endmodule
