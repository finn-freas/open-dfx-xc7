module rm_slot (input wire clk, input wire [15:0] din, output reg [15:0] dout);
    (* rom_style = "block" *) reg [15:0] rom [0:1023];
    integer i;
    initial for (i = 0; i < 1024; i = i + 1) rom[i] = (i * i) ^ 16'hC3C3;
    reg [15:0] q = 16'd0;
    reg [7:0] a = 8'd0, b = 8'd0;
    (* use_dsp = "yes" *) reg [15:0] p = 16'd0;
    always @(posedge clk) begin
        q <= rom[din[9:0]];
        a <= din[7:0];
        b <= din[15:8];
        p <= a * b;
        dout <= q ^ p;
    end
endmodule
