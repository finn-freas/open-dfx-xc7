module tb_axi_regs;
    reg         clk = 0;
    reg         rstn = 0;
    reg  [31:0] awaddr = 0, araddr = 0, wdata = 0;
    reg  [11:0] awid = 0, arid = 0;
    reg  [3:0]  wstrb = 0, arlen = 0;
    reg         awvalid = 0, wvalid = 0, wlast = 0, bready = 0, arvalid = 0, rready = 0;
    wire        awready, wready, bvalid, arready, rvalid, rlast;
    wire [11:0] bid, rid;
    wire [1:0]  bresp, rresp;
    wire [31:0] rdata;
    wire [3:0]  led;
    integer     errors = 0;
    integer     checks = 0;

    always #10 clk = ~clk;

    axi_regs dut (
        .clk(clk), .rstn(rstn),
        .awaddr(awaddr), .awid(awid), .awvalid(awvalid), .awready(awready),
        .wdata(wdata), .wstrb(wstrb), .wlast(wlast), .wvalid(wvalid), .wready(wready),
        .bid(bid), .bresp(bresp), .bvalid(bvalid), .bready(bready),
        .araddr(araddr), .arid(arid), .arlen(arlen), .arvalid(arvalid), .arready(arready),
        .rid(rid), .rdata(rdata), .rresp(rresp), .rlast(rlast), .rvalid(rvalid), .rready(rready),
        .led(led)
    );

    task chk(input [255:0] what, input [31:0] got, input [31:0] want);
        begin
            checks = checks + 1;
            if (got !== want) begin
                errors = errors + 1;
                $display("FAIL %0s: got %08x want %08x", what, got, want);
            end
        end
    endtask

    task write_burst(input [31:0] a, input [11:0] id, input [31:0] d0, input [3:0] s, input integer beats,
                     input integer w_first, input integer b_wait);
        integer i;
        begin
            @(negedge clk);
            if (w_first) begin
                wvalid = 1; wdata = d0; wstrb = s; wlast = (beats == 1);
                repeat (2) @(negedge clk);
            end
            awaddr = a; awid = id; awvalid = 1;
            @(posedge clk); while (!awready) @(posedge clk);
            @(negedge clk); awvalid = 0;
            for (i = 0; i < beats; i = i + 1) begin
                wvalid = 1; wdata = d0 + i; wstrb = s; wlast = (i == beats - 1);
                @(posedge clk); while (!wready) @(posedge clk);
                @(negedge clk);
            end
            wvalid = 0; wlast = 0;
            repeat (b_wait) @(negedge clk);
            bready = 1;
            @(posedge clk); while (!bvalid) @(posedge clk);
            chk("bid", bid, id);
            chk("bresp", bresp, 0);
            @(negedge clk); bready = 0;
        end
    endtask

    task read_burst(input [31:0] a, input [11:0] id, input [3:0] len, input [31:0] want, input integer r_wait,
                    input integer check_value);
        integer i;
        begin
            @(negedge clk);
            araddr = a; arid = id; arlen = len; arvalid = 1;
            @(posedge clk); while (!arready) @(posedge clk);
            @(negedge clk); arvalid = 0;
            for (i = 0; i <= len; i = i + 1) begin
                repeat (r_wait) @(negedge clk);
                rready = 1;
                @(posedge clk); while (!rvalid) @(posedge clk);
                chk("rid", rid, id);
                chk("rresp", rresp, 0);
                chk("rlast", rlast, i == len);
                if (check_value) chk("rdata", rdata, want);
                @(negedge clk); rready = 0;
            end
        end
    endtask

    reg [31:0] c0, c1;
    task read_count(output [31:0] v);
        begin
            @(negedge clk);
            araddr = 32'h4000_0008; arid = 12'h5; arlen = 0; arvalid = 1;
            @(posedge clk); while (!arready) @(posedge clk);
            @(negedge clk); arvalid = 0; rready = 1;
            @(posedge clk); while (!rvalid) @(posedge clk);
            v = rdata;
            @(negedge clk); rready = 0;
        end
    endtask

    initial begin
        repeat (4) @(negedge clk);
        rstn = 1;
        read_burst(32'h4000_000C, 12'h123, 0, 32'h0F5A_7020, 0, 1);
        write_burst(32'h4000_0004, 12'h0A1, 32'hA5C3_F00F, 4'hF, 1, 0, 0);
        read_burst(32'h4000_0004, 12'h0A2, 0, 32'hA5C3_F00F, 0, 1);
        write_burst(32'h4000_0004, 12'h0A3, 32'h1122_3344, 4'b0101, 1, 1, 3);
        read_burst(32'h4000_0004, 12'h0A4, 0, 32'hA522_F044, 2, 1);
        write_burst(32'h4000_0000, 12'h7FF, 32'h0000_000A, 4'h1, 1, 0, 0);
        chk("led", {28'd0, led}, 32'hA);
        read_burst(32'h4000_0000, 12'h001, 3, 32'h0000_000A, 1, 1);
        write_burst(32'h4000_0004, 12'h0B0, 32'hCAFE_0000, 4'hF, 4, 0, 1);
        read_burst(32'h4000_0004, 12'h0B1, 0, 32'hCAFE_0003, 0, 1);
        write_burst(32'h4000_000C, 12'h0C0, 32'hFFFF_FFFF, 4'hF, 1, 0, 0);
        read_burst(32'h4000_000C, 12'h0C1, 0, 32'h0F5A_7020, 0, 1);
        read_count(c0);
        repeat (10) @(negedge clk);
        read_count(c1);
        checks = checks + 1;
        if (c1 - c0 < 10) begin
            errors = errors + 1;
            $display("FAIL count: %0d -> %0d", c0, c1);
        end
        $display("axi_regs: %0d checks, %0d errors: %0s", checks, errors, errors ? "FAIL" : "PASS");
        $finish;
    end

    initial begin
        #200000;
        $display("axi_regs: TIMEOUT FAIL");
        $finish;
    end
endmodule
