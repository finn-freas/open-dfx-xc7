`timescale 1ns/1ps
module rm_lat (input wire clk, input wire valid, input wire [9:0] funct, input wire [31:0] rs1, input wire [31:0] rs2,
               output reg [31:0] rd = 32'd0, output reg ready = 1'b0);
    reg [31:0] due_t [0:3];
    reg [31:0] due_v [0:3];
    reg busy [0:3];
    integer t = 0, i, k, lat, stuck_until = 0;
    initial for (i = 0; i < 4; i = i + 1) busy[i] = 1'b0;
    always @(posedge clk) begin
        t = t + 1;
        ready <= t < stuck_until;
        for (i = 0; i < 4; i = i + 1)
            if (busy[i] && due_t[i] == t) begin
                rd <= due_v[i];
                ready <= 1'b1;
                busy[i] = 1'b0;
            end
        if (valid && funct == 10'd3) begin
            stuck_until = t + 300;
            rd <= 32'hDEADBEEF;
            ready <= 1'b1;
        end else if (valid) begin
            lat = funct == 10'd1 ? 100 : funct == 10'd2 ? 40 : 1;
            k = 0;
            for (i = 3; i >= 0; i = i - 1) if (!busy[i]) k = i;
            busy[k] = 1'b1;
            due_t[k] = t + lat;
            due_v[k] = rs1 + rs2;
        end
    end
endmodule
