module drc_idelay_noctrl (input wire clk, input wire [1:0] sw, output wire [3:0] led, input wire din);
    reg [23:0] c = 24'd0;
    always @(posedge clk) c <= c + 24'd1 + sw;
    wire dd;
    reg r = 1'b0;
    (* IODELAY_GROUP = "g0" *) IDELAYE2 #(.IDELAY_TYPE("FIXED"), .IDELAY_VALUE(5), .DELAY_SRC("IDATAIN")) u_dly (
        .IDATAIN(din), .DATAOUT(dd), .C(1'b0), .CE(1'b0), .INC(1'b0), .LD(1'b0), .LDPIPEEN(1'b0),
        .REGRST(1'b0), .CINVCTRL(1'b0), .CNTVALUEIN(5'd0), .DATAIN(1'b0), .CNTVALUEOUT());
    always @(posedge clk) r <= dd;
    assign led = {c[23:21], r};
endmodule
