module rm_core (input wire clk, input wire valid, input wire [9:0] funct, input wire [31:0] rs1, input wire [31:0] rs2,
                output wire [31:0] rd, output wire ready);
    reg [31:0] q = 32'd0;
    reg r = 1'b0;
    always @(posedge clk) begin
        q <= funct[0] ? (rs1 & rs2) : (rs1 ^ rs2);
        r <= valid;
    end
    assign rd = q;
    assign ready = r;
endmodule
