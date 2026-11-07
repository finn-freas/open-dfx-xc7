module carry4 (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [39:0] y;

    wire [3:0] co, o;
    CARRY4 u_c4 (.CI(1'b0), .CYINIT(s[0]), .DI(s[4:1]), .S(s[8:5]), .O(o), .CO(co));
    reg [31:0] acc = 32'd0;
    always @(posedge clk) acc <= acc + s[63:32];
    assign y = {acc, co, o};
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 40; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
