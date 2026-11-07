`timescale 1ns/1ps
module tb_axi_xbar;
    reg clk = 0;
    always #5 clk = ~clk;
    wire [3:0] led;
    axi_xbar dut (.clk(clk), .led(led));
    integer n0 = 0, n1 = 0;
    reg d0 = 0, d1 = 0;
    integer hit [0:3];
    integer k;
    initial for (k = 0; k < 4; k = k + 1) hit[k] = 0;
    always @(posedge clk) begin
        if (dut.done[0] != d0) begin d0 <= dut.done[0]; n0 <= n0 + 1; end
        if (dut.done[1] != d1) begin d1 <= dut.done[1]; n1 <= n1 + 1; end
        for (k = 0; k < 4; k = k + 1) if (dut.m_awvalid[k] && dut.m_awready[k]) hit[k] = hit[k] + 1;
        if (|dut.err) begin $display("FAIL err=%b at %0t", dut.err, $time); $finish; end
    end
`ifdef INJECT
    initial begin #1000000; force dut.m_rdata[3] = 1'b1; end
`endif
    initial begin
        #2000000;
        $display("transactions m0=%0d m1=%0d slave writes %0d %0d %0d %0d err=%b", n0, n1, hit[0], hit[1], hit[2], hit[3], dut.err);
        if (n0 > 100 && n1 > 100 && hit[0] > 0 && hit[1] > 0 && hit[2] > 0 && hit[3] > 0 && dut.err == 0) $display("PASS");
        else $display("FAIL");
        $finish;
    end
endmodule
