module hls_isqrt (input wire clk, output wire [3:0] led);
  reg [3:0] por = 4'd0;
  wire rst_n = &por;
  always @(posedge clk) if (!rst_n) por <= por + 4'd1;

  reg [23:0] tick = 24'd0;
  reg [31:0] n = 32'd0;
  reg start = 1'b0;
  reg [31:0] root = 32'd0;
  wire done;
  wire [31:0] ret;

  always @(posedge clk) begin
    tick <= tick + 24'd1;
    start <= 1'b0;
    if (rst_n && tick == 24'd0) begin
      n <= n + 32'd1;
      start <= 1'b1;
    end
    if (done) root <= ret;
  end

  isqrt u_isqrt (
    .clock(clk),
    .reset(rst_n),
    .start_port(start),
    .done_port(done),
    .x(n),
    .return_port(ret)
  );

  assign led = root[3:0];
endmodule
