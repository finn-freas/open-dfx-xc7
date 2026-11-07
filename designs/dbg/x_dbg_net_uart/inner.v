
module x_dbg_net_dbg_inner(clk, sw, led, dq);
  input clk;
  wire clk;
  input [3:0] sw;
  wire [3:0] sw;
  output [3:0] led;
  wire [3:0] led;
  output [15:0] dq;
  reg [15:0] dq = 16'h0000;
  wire [15:0] _00_;
  wire [15:0] _01_;
  wire [15:0] _02_;
  wire [15:0] _03_;
  wire [15:0] _04_;
  wire [15:0] _05_;
  wire [15:0] _06_;
  wire [15:0] _07_;
  wire [15:0] _08_;
  wire [15:0] _09_;
  wire [15:0] _10_;
  wire [15:0] _11_;
  reg [15:0] s = 16'h0000;
  wire [15:0] t0;
  wire [15:0] t1;
  assign _00_ = s + { 12'h000, sw };
  assign _01_ = _00_ + 16'h0001;
  assign _02_ = _04_ + s;
  assign _03_ = _02_ + 16'h0000;
  assign _04_ = s ^ { s[0], s[15:1] };
  assign _05_ = _07_ + t0;
  assign _06_ = _05_ + 16'h79b1;
  assign _07_ = t0 ^ { t0[3:0], t0[15:4] };
  always @(posedge clk)
    dq <= _06_;
  always @(posedge clk)
    s <= _01_;
  assign t0 = _03_;
  assign t1 = _06_;
  assign led = dq[15:12];
  assign _10_ = 16'h0000;
  assign _11_ = 16'h0000;
  assign _08_ = _06_;
  assign _09_ = _01_;
endmodule
