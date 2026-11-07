`timescale 1ns / 1ps
module PS7 (
`include "ps7_ports.vh"
);
    parameter FCLK0_HALF_NS = 10.0;
    parameter TRACE_MAX = 256;

    reg        clk0 = 1'b0;
    reg        rstn0 = 1'b0;
    reg [31:0] awaddr_r = 0, araddr_r = 0, wdata_r = 0;
    reg [11:0] awid_r = 0, arid_r = 0, wid_r = 0;
    reg [3:0]  wstrb_r = 0;
    reg        awvalid_r = 0, wvalid_r = 0, wlast_r = 0, bready_r = 0, arvalid_r = 0, rready_r = 0;

    assign FCLKCLK    = {3'b000, clk0};
    assign FCLKRESETN = {3'b000, rstn0};
    assign MAXIGP0AWADDR  = awaddr_r;
    assign MAXIGP0AWID    = awid_r;
    assign MAXIGP0AWVALID = awvalid_r;
    assign MAXIGP0AWLEN   = 4'd0;
    assign MAXIGP0AWSIZE  = 2'd2;
    assign MAXIGP0AWBURST = 2'd1;
    assign MAXIGP0WDATA   = wdata_r;
    assign MAXIGP0WID     = wid_r;
    assign MAXIGP0WSTRB   = wstrb_r;
    assign MAXIGP0WLAST   = wlast_r;
    assign MAXIGP0WVALID  = wvalid_r;
    assign MAXIGP0BREADY  = bready_r;
    assign MAXIGP0ARADDR  = araddr_r;
    assign MAXIGP0ARID    = arid_r;
    assign MAXIGP0ARLEN   = 4'd0;
    assign MAXIGP0ARSIZE  = 2'd2;
    assign MAXIGP0ARBURST = 2'd1;
    assign MAXIGP0ARVALID = arvalid_r;
    assign MAXIGP0RREADY  = rready_r;

    always #(FCLK0_HALF_NS) clk0 = ~clk0;

    integer errors = 0, checks = 0, n_ops = 0, timeout;
    reg [31:0] trace [0:3*TRACE_MAX-1];
    reg [31:0] last_count;
    reg        have_count = 0;
    reg [11:0] id_ctr = 12'h101;
    reg [8*256-1:0] trace_file;

    task check(input [8*16-1:0] what, input [31:0] got, input [31:0] want);
        begin
            checks = checks + 1;
            if (got !== want) begin
                errors = errors + 1;
                $display("FAIL %0s: got %08x want %08x at %0t", what, got, want, $time);
            end
        end
    endtask

    task axi_write(input [31:0] a, input [31:0] d);
        reg [11:0] id;
        reg aw_done, w_done;
        begin
            id = id_ctr; id_ctr = id_ctr + 12'h0a3;
            @(posedge clk0); #1;
            awaddr_r = a; awid_r = id; awvalid_r = 1;
            wdata_r = d; wid_r = id; wstrb_r = 4'hf; wlast_r = 1; wvalid_r = 1;
            aw_done = 0; w_done = 0; timeout = 0;
            while (!(aw_done && w_done) && timeout < 1000) begin
                @(posedge clk0);
                if (awvalid_r && MAXIGP0AWREADY === 1'b1) aw_done = 1;
                if (wvalid_r && MAXIGP0WREADY === 1'b1) w_done = 1;
                #1;
                if (aw_done) awvalid_r = 0;
                if (w_done) begin wvalid_r = 0; wlast_r = 0; end
                timeout = timeout + 1;
            end
            bready_r = 1;
            timeout = 0;
            @(posedge clk0);
            while (MAXIGP0BVALID !== 1'b1 && timeout < 1000) begin @(posedge clk0); timeout = timeout + 1; end
            check("bid", {20'd0, MAXIGP0BID}, {20'd0, id});
            check("bresp", {30'd0, MAXIGP0BRESP}, 32'd0);
            #1 bready_r = 0;
            if (timeout >= 1000) begin errors = errors + 1; $display("FAIL write %08x: no response", a); end
        end
    endtask

    task axi_read(input [31:0] a, output [31:0] d);
        reg [11:0] id;
        begin
            id = id_ctr; id_ctr = id_ctr + 12'h0a3;
            @(posedge clk0); #1;
            araddr_r = a; arid_r = id; arvalid_r = 1;
            timeout = 0;
            @(posedge clk0);
            while (MAXIGP0ARREADY !== 1'b1 && timeout < 1000) begin @(posedge clk0); timeout = timeout + 1; end
            #1 arvalid_r = 0; rready_r = 1;
            @(posedge clk0);
            while (MAXIGP0RVALID !== 1'b1 && timeout < 1000) begin @(posedge clk0); timeout = timeout + 1; end
            d = MAXIGP0RDATA;
            check("rid", {20'd0, MAXIGP0RID}, {20'd0, id});
            check("rresp", {30'd0, MAXIGP0RRESP}, 32'd0);
            check("rlast", {31'd0, MAXIGP0RLAST}, 32'd1);
            #1 rready_r = 0;
            if (timeout >= 1000) begin errors = errors + 1; $display("FAIL read %08x: no response", a); end
        end
    endtask

    integer i;
    reg [31:0] op, addr, data, got;
    initial begin
        for (i = 0; i < 3 * TRACE_MAX; i = i + 1) trace[i] = 32'hffffffff;
        if (!$value$plusargs("TRACE=%s", trace_file)) begin
            $display("FAIL no +TRACE=<file>");
            $finish;
        end
        $readmemh(trace_file, trace);
        repeat (8) @(posedge clk0);
        #1 rstn0 = 1;
        repeat (8) @(posedge clk0);
        for (i = 0; trace[3 * i] !== 32'hffffffff && i < TRACE_MAX; i = i + 1) begin
            op = trace[3 * i]; addr = trace[3 * i + 1]; data = trace[3 * i + 2];
            n_ops = n_ops + 1;
            if (op == 1) begin
                axi_write(addr, data);
                if (addr[3:2] == 2'd0) begin
                    repeat (2) @(posedge clk0);
                    check("led pins", {28'd0, tb.led}, {28'd0, data[3:0]});
                end
                $display("op %0d: write %08x <- %08x", i, addr, data);
            end else begin
                axi_read(addr, got);
                if (addr[3:2] == 2'd2) begin
                    checks = checks + 1;
                    if (have_count && got === last_count) begin
                        errors = errors + 1;
                        $display("FAIL count did not advance: %08x", got);
                    end
                    if (^got === 1'bx) begin errors = errors + 1; $display("FAIL count is X"); end
                    last_count = got; have_count = 1;
                end else begin
                    check("rdata", got, data);
                end
                $display("op %0d: read  %08x -> %08x (trace %08x)", i, addr, got, data);
            end
        end
        $display("PS7 BFM: %0d trace ops, %0d checks, %0d errors: %0s", n_ops, checks, errors,
                 (errors == 0 && n_ops > 0) ? "PASS" : "FAIL");
        $finish;
    end

    initial begin
        #5000000;
        $display("PS7 BFM: TIMEOUT FAIL");
        $finish;
    end
endmodule
