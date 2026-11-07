module prbs32 (
    input  wire        clk,
    input  wire        en,
    output reg  [31:0] q = 32'h0
);
    always @(posedge clk)
        if (en)
            q <= {q[30:0], ~(q[31] ^ q[21] ^ q[1] ^ q[0])};
endmodule
