module rm_core (input wire [7:0] a, output wire [3:0] d);
    assign d = a[3:0] + a[7:4];
endmodule
