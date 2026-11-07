module spi_master #(parameter DIV = 2) (
    input wire clk, input wire start, input wire [31:0] wdata,
    output reg busy = 1'b0, output reg [31:0] rdata = 32'd0,
    output reg sck = 1'b0, output reg mosi = 1'b0, input wire miso
);
    reg [31:0] sh = 32'd0;
    reg [4:0] nb = 5'd0;
    reg [7:0] cnt = 8'd0;
    reg miso_q = 1'b0;
    always @(posedge clk) begin
        miso_q <= miso;
        if (!busy) begin
            sck <= 1'b0;
            if (start) begin
                busy <= 1'b1;
                sh <= wdata;
                mosi <= wdata[31];
                nb <= 5'd31;
                cnt <= DIV - 1;
            end
        end else if (cnt != 8'd0) begin
            cnt <= cnt - 8'd1;
        end else begin
            cnt <= DIV - 1;
            if (!sck) begin
                sck <= 1'b1;
            end else begin
                sck <= 1'b0;
                rdata <= {rdata[30:0], miso_q};
                sh <= {sh[30:0], 1'b0};
                mosi <= sh[30];
                if (nb == 5'd0) busy <= 1'b0;
                else nb <= nb - 5'd1;
            end
        end
    end
endmodule
