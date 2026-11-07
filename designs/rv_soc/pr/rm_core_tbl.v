module rm_core (input wire clk, input wire valid, input wire [9:0] funct, input wire [31:0] rs1, input wire [31:0] rs2,
                output wire [31:0] rd, output wire ready);
    reg [31:0] tbl [0:1023];
    integer i;
    initial for (i = 0; i < 1024; i = i + 1) tbl[i] = i * i * i + 32'h9E3779B9;
    reg [31:0] q, p;
    reg r = 1'b0, f = 1'b0;
    always @(posedge clk) begin
        q <= tbl[rs1[9:0]];
        p <= rs1[15:0] * rs2[15:0];
        r <= valid;
        f <= funct[0];
    end
    assign rd = f ? p : q;
    assign ready = r;
endmodule
