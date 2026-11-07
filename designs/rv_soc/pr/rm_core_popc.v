module rm_core (input wire valid, input wire [9:0] funct, input wire [31:0] rs1, input wire [31:0] rs2,
                output reg [31:0] rd, output wire ready);
    integer i;
    reg [5:0] n;
    reg seen;
    always @* begin
        n = 6'd0;
        seen = 1'b0;
        for (i = 31; i >= 0; i = i - 1) begin
            seen = seen | rs1[i];
            n = n + (funct[0] ? {5'd0, ~seen} : {5'd0, rs1[i]});
        end
        rd = {26'd0, n};
    end
    assign ready = valid;
endmodule
