module usr_accesse2 (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [32:0] y;

    wire [31:0] data;
    wire cfgclk, dv;
    USR_ACCESSE2 u_usr (.CFGCLK(cfgclk), .DATA(data), .DATAVALID(dv));
    assign y = {data, dv};
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 33; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
