module rm_core (input wire valid, input wire [9:0] funct, input wire [31:0] rs1, input wire [31:0] rs2,
                output wire [31:0] rd, output wire ready);
    wire [4:0] sh = funct[0] ? (5'd0 - rs2[4:0]) : rs2[4:0];
    wire [63:0] dbl = {rs1, rs1} << sh;
    assign rd = dbl[63:32];
    assign ready = valid;
endmodule
