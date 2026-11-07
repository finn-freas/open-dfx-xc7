module rm_core (input wire valid, input wire [9:0] funct, input wire [31:0] rs1, input wire [31:0] rs2,
                output wire [31:0] rd, output wire ready);
    wire lt = funct[1] ? (rs1 < rs2) : ($signed(rs1) < $signed(rs2));
    assign rd = (lt ^ funct[0]) ? rs1 : rs2;
    assign ready = valid;
endmodule
