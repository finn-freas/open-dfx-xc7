module rm_slot (input wire clk, input wire valid, input wire [9:0] funct, input wire [31:0] rs1, input wire [31:0] rs2, output wire [31:0] rd, output wire ready);
    assign rd = 32'hDEADBEEF;
    assign ready = 1'b0;
endmodule
