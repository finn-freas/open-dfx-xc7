module rm_core (input wire [7:0] a, output wire [3:0] d);
    (* keep, BEL = "X30Y30/SLICE_X1Y0.A6LUT" *) LUT2 #(.INIT(4'b0001)) l0 (.I0(a[6]), .I1(a[7]), .O(d[0]));
    (* keep, BEL = "X30Y30/SLICE_X1Y0.B6LUT" *) LUT2 #(.INIT(4'b0010)) l1 (.I0(a[6]), .I1(a[7]), .O(d[1]));
    (* keep, BEL = "X30Y30/SLICE_X1Y0.C6LUT" *) LUT2 #(.INIT(4'b0100)) l2 (.I0(a[6]), .I1(a[7]), .O(d[2]));
    (* keep, BEL = "X30Y30/SLICE_X1Y0.D6LUT" *) LUT2 #(.INIT(4'b1000)) l3 (.I0(a[6]), .I1(a[7]), .O(d[3]));
endmodule
