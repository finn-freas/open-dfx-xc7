module x_dbg_net (
    input wire clk,
    input wire [3:0] sw,
    output wire [3:0] led
);
    wire [15:0] dbg_dq;
    x_dbg_net_dbg_inner u_dut (.clk(clk), .sw(sw), .led(led), .dq(dbg_dq));
    scope_core u_dbg (.dbg_clk(clk), .dbg_probe({dbg_dq}));
endmodule
