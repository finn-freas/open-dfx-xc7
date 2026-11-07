module axi_regs #(
    parameter ID_W     = 12,
    parameter ID_VALUE = 32'h0F5A_7020
) (
    input  wire            clk,
    input  wire            rstn,
    input  wire [31:0]     awaddr,
    input  wire [ID_W-1:0] awid,
    input  wire            awvalid,
    output wire            awready,
    input  wire [31:0]     wdata,
    input  wire [3:0]      wstrb,
    input  wire            wlast,
    input  wire            wvalid,
    output wire            wready,
    output reg  [ID_W-1:0] bid,
    output wire [1:0]      bresp,
    output reg             bvalid,
    input  wire            bready,
    input  wire [31:0]     araddr,
    input  wire [ID_W-1:0] arid,
    input  wire [3:0]      arlen,
    input  wire            arvalid,
    output wire            arready,
    output reg  [ID_W-1:0] rid,
    output reg  [31:0]     rdata,
    output wire [1:0]      rresp,
    output wire            rlast,
    output reg             rvalid,
    input  wire            rready,
    output wire [3:0]      led
);
    reg  [31:0] led_r, scratch_r, count_r;
    reg  [1:0]  waddr;
    reg         wbusy;
    reg  [1:0]  raddr;
    reg  [3:0]  rleft;
    reg         rbusy;

    assign awready = !wbusy && !bvalid;
    assign wready  = wbusy;
    assign bresp   = 2'b00;
    assign arready = !rbusy;
    assign rresp   = 2'b00;
    assign rlast   = rleft == 4'd0;
    assign led     = led_r[3:0];

    function [31:0] merge(input [31:0] old, input [31:0] d, input [3:0] s);
        integer i;
        begin
            for (i = 0; i < 4; i = i + 1)
                merge[i*8 +: 8] = s[i] ? d[i*8 +: 8] : old[i*8 +: 8];
        end
    endfunction

    function [31:0] regval(input [1:0] a);
        case (a)
            2'd0: regval = led_r;
            2'd1: regval = scratch_r;
            2'd2: regval = count_r;
            default: regval = ID_VALUE;
        endcase
    endfunction

    always @(posedge clk) begin
        if (!rstn) begin
            count_r <= 32'd0;
        end else begin
            count_r <= count_r + 32'd1;
        end
    end

    always @(posedge clk) begin
        if (!rstn) begin
            wbusy     <= 1'b0;
            bvalid    <= 1'b0;
            waddr     <= 2'd0;
            bid       <= {ID_W{1'b0}};
            led_r     <= 32'd0;
            scratch_r <= 32'd0;
        end else begin
            if (awvalid && awready) begin
                wbusy <= 1'b1;
                waddr <= awaddr[3:2];
                bid   <= awid;
            end
            if (wvalid && wready) begin
                case (waddr)
                    2'd0: led_r     <= merge(led_r, wdata, wstrb);
                    2'd1: scratch_r <= merge(scratch_r, wdata, wstrb);
                    default: ;
                endcase
                if (wlast) begin
                    wbusy  <= 1'b0;
                    bvalid <= 1'b1;
                end
            end
            if (bvalid && bready)
                bvalid <= 1'b0;
        end
    end

    always @(posedge clk) begin
        if (!rstn) begin
            rbusy  <= 1'b0;
            rvalid <= 1'b0;
            raddr  <= 2'd0;
            rleft  <= 4'd0;
            rid    <= {ID_W{1'b0}};
            rdata  <= 32'd0;
        end else if (arvalid && arready) begin
            rbusy  <= 1'b1;
            rvalid <= 1'b1;
            raddr  <= araddr[3:2];
            rleft  <= arlen;
            rid    <= arid;
            rdata  <= regval(araddr[3:2]);
        end else if (rvalid && rready) begin
            if (rleft == 4'd0) begin
                rbusy  <= 1'b0;
                rvalid <= 1'b0;
            end else begin
                rleft <= rleft - 4'd1;
                rdata <= regval(raddr);
            end
        end
    end
endmodule
