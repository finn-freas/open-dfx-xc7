module bscane2 (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [8:0] y;

    wire capture, drck, rst, runtest, sel, shift, tck, tdi, tms, update;
    reg tdo = 1'b0;
    BSCANE2 #(.JTAG_CHAIN(1)) u_bscan (.CAPTURE(capture), .DRCK(drck), .RESET(rst), .RUNTEST(runtest), .SEL(sel),
        .SHIFT(shift), .TCK(tck), .TDI(tdi), .TMS(tms), .UPDATE(update), .TDO(tdo));
    always @(posedge tck) tdo <= tdi ^ sel;
    assign y = {capture, rst, runtest, sel, shift, tdi, tms, update, drck};
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 9; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
