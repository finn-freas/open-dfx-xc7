module single_port_ram #(parameter ADDR_WIDTH = 1, parameter DATA_WIDTH = 1) (
    input  wire                  clk,
    input  wire [ADDR_WIDTH-1:0] addr,
    input  wire [DATA_WIDTH-1:0] data,
    input  wire                  we,
    output reg  [DATA_WIDTH-1:0] out
);
    reg [DATA_WIDTH-1:0] mem [0:(1 << ADDR_WIDTH) - 1];
    always @(posedge clk) begin
        if (we)
            mem[addr] <= data;
        out <= mem[addr];
    end
endmodule

module dual_port_ram #(parameter ADDR_WIDTH = 1, parameter DATA_WIDTH = 1) (
    input  wire                  clk,
    input  wire [ADDR_WIDTH-1:0] addr1,
    input  wire [ADDR_WIDTH-1:0] addr2,
    input  wire [DATA_WIDTH-1:0] data1,
    input  wire [DATA_WIDTH-1:0] data2,
    input  wire                  we1,
    input  wire                  we2,
    output reg  [DATA_WIDTH-1:0] out1,
    output reg  [DATA_WIDTH-1:0] out2
);
    reg [DATA_WIDTH-1:0] mem [0:(1 << ADDR_WIDTH) - 1];
    always @(posedge clk) begin
        if (we1)
            mem[addr1] <= data1;
        out1 <= mem[addr1];
    end
    always @(posedge clk) begin
        if (we2)
            mem[addr2] <= data2;
        out2 <= mem[addr2];
    end
endmodule
