module rm_core (input wire [7:0] a, output wire [3:0] d);
    (* keep, BEL = "X30Y30/SLICE_X1Y0.A6LUT" *) LUT1 #(.INIT(2'b10)) l0 (.I0(a[4]), .O(d[0]));
    (* keep, BEL = "X30Y30/SLICE_X1Y0.B6LUT" *) LUT1 #(.INIT(2'b10)) l1 (.I0(a[5]), .O(d[1]));
    (* keep, BEL = "X30Y30/SLICE_X1Y0.C6LUT" *) LUT1 #(.INIT(2'b10)) l2 (.I0(a[6]), .O(d[2]));
    (* keep, BEL = "X30Y30/SLICE_X1Y0.D6LUT" *) LUT1 #(.INIT(2'b10)) l3 (.I0(a[7]), .O(d[3]));
endmodule
