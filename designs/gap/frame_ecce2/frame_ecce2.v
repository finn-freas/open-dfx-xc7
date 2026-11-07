module frame_ecce2 (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [54:0] y;

    wire crcerr, eccerr, eccsingle, synvalid;
    wire [25:0] far;
    wire [4:0] synbit;
    wire [12:0] syn;
    wire [6:0] synword;
    FRAME_ECCE2 #(.FARSRC("EFAR"), .FRAME_RBT_IN_FILENAME("NONE")) u_ecc (
        .CRCERROR(crcerr), .ECCERROR(eccerr), .ECCERRORSINGLE(eccsingle), .FAR(far), .SYNBIT(synbit),
        .SYNDROME(syn), .SYNDROMEVALID(synvalid), .SYNWORD(synword));
    assign y = {crcerr, eccerr, eccsingle, synvalid, far, synbit, syn, synword} ^ s[54:0];
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 55; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
