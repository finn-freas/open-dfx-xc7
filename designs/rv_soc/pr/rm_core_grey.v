module rm_core (input wire valid, input wire [9:0] funct, input wire [31:0] rs1, input wire [31:0] rs2,
                output wire [31:0] rd, output wire ready);
    assign rd = 32'd0;
    assign ready = valid;
endmodule
