module top (input wire clk, output reg [3:0] led);
    reg [27:0] count = 28'd0;
    wire [15:0] rm_out;
    always @(posedge clk) begin
        count <= count + 28'd1;
        led <= rm_out[3:0] ^ rm_out[7:4] ^ rm_out[11:8] ^ rm_out[15:12];
    end
    rm_slot u_rm (.clk(clk), .din(count[27:12]), .dout(rm_out));
endmodule
