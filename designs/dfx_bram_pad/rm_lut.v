module rm_slot (input wire clk, input wire [15:0] din, output reg [15:0] dout);
    (* rom_style = "block" *) reg [15:0] rom [0:1023];
    integer i;
    initial for (i = 0; i < 1024; i = i + 1) rom[i] = (i * 16'd40503) ^ 16'h5A5A;
    always @(posedge clk) dout <= rom[din[9:0]];
endmodule
