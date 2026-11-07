module rm_slot (input wire clk, input wire [7:0] din, output reg [3:0] dout);
    localparam N = 48;
    (* shreg_extract = "no" *) reg [31:0] s [0:N-1];
    integer i;
    always @(posedge clk) begin
        s[0] <= {din, ~din, din ^ 8'h5A, din + 8'h3C};
        for (i = 1; i < N; i = i + 1)
            s[i] <= s[i-1] ^ {s[i-1][26:0], s[i-1][31:27]} ^ (32'h9E3779B9 >> (i % 31));
        dout <= s[N-1][3:0] ^ s[N-1][11:8] ^ s[N-1][19:16] ^ s[N-1][27:24];
    end
endmodule
