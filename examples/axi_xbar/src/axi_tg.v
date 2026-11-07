module axi_tg #(
    parameter ADDR_WIDTH = 16,
    parameter ID_WIDTH = 4,
    parameter [ID_WIDTH-1:0] ID = 0,
    parameter [15:0] SEED = 16'hace1,
    parameter LANE = 0
) (
    input  wire                  clk,
    input  wire                  rst,
    output reg  [ID_WIDTH-1:0]   awid,
    output reg  [ADDR_WIDTH-1:0] awaddr,
    output wire [7:0]            awlen,
    output wire [2:0]            awsize,
    output wire [1:0]            awburst,
    output reg                   awvalid,
    input  wire                  awready,
    output reg  [31:0]           wdata,
    output wire [3:0]            wstrb,
    output reg                   wlast,
    output reg                   wvalid,
    input  wire                  wready,
    input  wire [ID_WIDTH-1:0]   bid,
    input  wire [1:0]            bresp,
    input  wire                  bvalid,
    output reg                   bready,
    output reg  [ID_WIDTH-1:0]   arid,
    output reg  [ADDR_WIDTH-1:0] araddr,
    output wire [7:0]            arlen,
    output wire [2:0]            arsize,
    output wire [1:0]            arburst,
    output reg                   arvalid,
    input  wire                  arready,
    input  wire [ID_WIDTH-1:0]   rid,
    input  wire [31:0]           rdata,
    input  wire [1:0]            rresp,
    input  wire                  rlast,
    input  wire                  rvalid,
    output reg                   rready,
    output reg                   err,
    output reg                   done
);
    localparam S_AW = 3'd0, S_W = 3'd1, S_B = 3'd2, S_AR = 3'd3, S_R = 3'd4;
    assign awlen = 8'd3;
    assign arlen = 8'd3;
    assign awsize = 3'd2;
    assign arsize = 3'd2;
    assign awburst = 2'b01;
    assign arburst = 2'b01;
    assign wstrb = 4'hf;

    reg [2:0] st;
    reg [15:0] lfsr;
    reg [15:0] pass;
    reg [1:0] beat;
    reg [ADDR_WIDTH-1:0] base;

    function [31:0] pat(input [ADDR_WIDTH-1:0] a, input [1:0] b, input [15:0] p);
        pat = {p ^ SEED, a} ^ {b, 30'h2aaa_5555};
    endfunction

    wire [ADDR_WIDTH-1:0] next_addr = {lfsr[ADDR_WIDTH-1:10], LANE[0], lfsr[8:4], 4'b0000};

    always @(posedge clk) begin
        if (rst) begin
            st <= S_AW;
            lfsr <= SEED;
            pass <= 16'd0;
            beat <= 2'd0;
            awvalid <= 1'b0;
            wvalid <= 1'b0;
            wlast <= 1'b0;
            bready <= 1'b0;
            arvalid <= 1'b0;
            rready <= 1'b0;
            err <= 1'b0;
            done <= 1'b0;
            awid <= ID;
            arid <= ID;
            awaddr <= 0;
            araddr <= 0;
            base <= 0;
            wdata <= 32'd0;
        end else begin
            case (st)
                S_AW: begin
                    if (!awvalid) begin
                        base <= next_addr;
                        awaddr <= next_addr;
                        awvalid <= 1'b1;
                    end else if (awready) begin
                        awvalid <= 1'b0;
                        beat <= 2'd0;
                        wdata <= pat(base, 2'd0, pass);
                        wlast <= 1'b0;
                        wvalid <= 1'b1;
                        st <= S_W;
                    end
                end
                S_W: if (wready) begin
                    if (wlast) begin
                        wvalid <= 1'b0;
                        wlast <= 1'b0;
                        bready <= 1'b1;
                        st <= S_B;
                    end else begin
                        beat <= beat + 2'd1;
                        wdata <= pat(base, beat + 2'd1, pass);
                        wlast <= (beat == 2'd2);
                    end
                end
                S_B: if (bvalid) begin
                    bready <= 1'b0;
                    if (bresp != 2'b00 || bid != ID) err <= 1'b1;
                    araddr <= base;
                    arvalid <= 1'b1;
                    st <= S_AR;
                end
                S_AR: if (arready) begin
                    arvalid <= 1'b0;
                    rready <= 1'b1;
                    beat <= 2'd0;
                    st <= S_R;
                end
                S_R: if (rvalid) begin
                    if (rdata != pat(base, beat, pass) || rresp != 2'b00 || rid != ID || rlast != (beat == 2'd3))
                        err <= 1'b1;
                    beat <= beat + 2'd1;
                    if (rlast) begin
                        rready <= 1'b0;
                        done <= ~done;
                        pass <= pass + 16'd1;
                        lfsr <= {lfsr[14:0], lfsr[15] ^ lfsr[13] ^ lfsr[12] ^ lfsr[10]};
                        st <= S_AW;
                    end
                end
                default: st <= S_AW;
            endcase
        end
    end
endmodule
