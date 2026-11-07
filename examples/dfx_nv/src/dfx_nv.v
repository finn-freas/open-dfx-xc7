module dfx_nv (
    input  wire       clk,
    output wire [3:0] led
);
    reg [31:0] a = 32'h00000001;
    reg [31:0] b = 32'h0;
    reg [9:0] f = 10'd0;
    reg v = 1'b0;
    always @(posedge clk) begin
        a <= {a[30:0], a[31] ^ a[21] ^ a[1] ^ a[0]};
        b <= b + 32'h9E3779B9;
        f <= f + 10'd1;
        v <= ~v;
    end
    wire [31:0] rd;
    wire ready;
    rm_slot u_rm (.clk(clk), .valid(v), .funct(f), .rs1(a), .rs2(b), .rd(rd), .ready(ready));
    reg [31:0] acc = 32'h0;
    always @(posedge clk) if (ready) acc <= acc ^ rd;
    assign led = acc[3:0] ^ acc[7:4] ^ acc[11:8] ^ acc[15:12] ^ acc[19:16] ^ acc[23:20] ^ acc[27:24] ^ acc[31:28];
endmodule
