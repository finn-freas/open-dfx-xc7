module x_dbg_net (
    input wire clk,
    input wire [3:0] sw,
    output wire [3:0] led,
    input wire dbg_uart_rx,
    output wire dbg_uart_tx
);
    wire [15:0] dbg_dq;
    wire [15:0] dbg_s;
    x_dbg_net_dbg_inner u_dut (.clk(clk), .sw(sw), .led(led), .dq(dbg_dq), .s(dbg_s));
    scope_core u_dbg (.dbg_clk(clk), .dbg_probe({dbg_s, dbg_dq}), .dbg_serial_rx(dbg_uart_rx), .dbg_serial_tx(dbg_uart_tx));
endmodule
