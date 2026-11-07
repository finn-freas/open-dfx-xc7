module ram32m (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [7:0] y;

    wire [1:0] doa, dob, doc, dod;
    RAM32M #(.INIT_A(64'h0123_4567_89ab_cdef), .INIT_B(64'h1), .INIT_C(64'h2), .INIT_D(64'h3)) u_ram (
        .WCLK(clk), .WE(s[0]), .ADDRA(s[5:1]), .ADDRB(s[10:6]), .ADDRC(s[15:11]), .ADDRD(s[20:16]),
        .DIA(s[22:21]), .DIB(s[24:23]), .DIC(s[26:25]), .DID(s[28:27]),
        .DOA(doa), .DOB(dob), .DOC(doc), .DOD(dod));
    assign y = {doa, dob, doc, dod};
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 8; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
