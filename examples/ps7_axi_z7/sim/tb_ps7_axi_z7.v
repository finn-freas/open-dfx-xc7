`timescale 1ns / 1ps
module tb;
    wire [3:0] led;
    ps7_axi_z7 dut (.led(led));
endmodule
