`timescale 1ns/1ps
module tb_bridge;
    reg clk = 0;
    always #5 clk = ~clk;
    reg resetn = 0;
    reg pcpi_valid = 0;
    reg [31:0] pcpi_insn = 0, pcpi_rs1 = 0, pcpi_rs2 = 0;
    wire pcpi_wr, pcpi_wait, pcpi_ready;
    wire [31:0] pcpi_rd;
    wire slot_valid, slot_ready;
    wire [9:0] slot_funct;
    wire [31:0] slot_rs1, slot_rs2, slot_rd;
    wire [15:0] timeouts;
`ifdef OLD
    localparam NAME = "rm_bridge (designs/rv_soc, unchanged)";
    wire [15:0] late = 16'd0;
    rm_bridge #(.TIMEOUT(64)) dut (
`else
    localparam NAME = "rm_bridge_fenced (designs/rv_flash)";
    wire [15:0] late;
    rm_bridge_fenced #(.TIMEOUT(64), .FENCE(64)) dut (
`endif
        .clk(clk), .resetn(resetn),
        .pcpi_valid(pcpi_valid), .pcpi_insn(pcpi_insn), .pcpi_rs1(pcpi_rs1), .pcpi_rs2(pcpi_rs2),
        .pcpi_wr(pcpi_wr), .pcpi_rd(pcpi_rd), .pcpi_wait(pcpi_wait), .pcpi_ready(pcpi_ready),
        .slot_valid(slot_valid), .slot_funct(slot_funct), .slot_rs1(slot_rs1), .slot_rs2(slot_rs2),
        .slot_rd(slot_rd), .slot_ready(slot_ready), .timeouts(timeouts)
`ifndef OLD
        , .late_answers(late)
`endif
    );
    rm_lat u_rm (.clk(clk), .valid(slot_valid), .funct(slot_funct), .rs1(slot_rs1), .rs2(slot_rs2),
                 .rd(slot_rd), .ready(slot_ready));

    integer errors = 0, cyc = 0;
    always @(posedge clk) cyc = cyc + 1;

    task issue(input [9:0] f, input [31:0] a, input [31:0] b, input [31:0] expect_new, input [31:0] expect_old,
               input [8*24-1:0] what);
        integer n, t0;
        reg [31:0] r, e;
        begin
            @(posedge clk);
            #1;
            t0 = cyc;
            pcpi_valid = 1;
            pcpi_insn = {f[9:3], 5'd0, 5'd0, f[2:0], 5'd0, 7'b0001011};
            pcpi_rs1 = a;
            pcpi_rs2 = b;
            n = 0;
            while (!pcpi_ready && n < 2000) begin
                @(posedge clk);
                #1;
                n = n + 1;
            end
            r = pcpi_wr ? pcpi_rd : 32'hXXXXXXXX;
            #0;
`ifdef OLD
            e = expect_old;
`else
            e = expect_new;
`endif
            @(posedge clk);
            #1;
            pcpi_valid = 0;
            if (n >= 2000) begin
                $display("FAIL: %0s: no pcpi_ready (hang)", what);
                errors = errors + 1;
            end else if (r !== e) begin
                $display("FAIL: %0s: funct %0d rd=%08x expected %08x (%0d cycles)", what, f, r, e, cyc - t0);
                errors = errors + 1;
            end else begin
                $display("ok:   %0s: funct %0d rd=%08x (%0d cycles)", what, f, r, cyc - t0);
            end
            repeat (4) @(posedge clk);
        end
    endtask

    initial begin
        repeat (4) @(posedge clk);
        resetn = 1;
        repeat (4) @(posedge clk);
        issue(10'd0, 32'h1, 32'h2, 32'h3, 32'h3, "fast answer");
        issue(10'd1, 32'h100, 32'h200, 32'h0, 32'h0, "slow answer times out");
        issue(10'd2, 32'h10, 32'h20, 32'h30, 32'h300, "next after late answer");
        issue(10'd3, 32'h0, 32'h0, 32'hDEADBEEF, 32'hDEADBEEF, "ready stuck high");
        issue(10'd0, 32'h5, 32'h6, 32'h0, 32'h30, "issue while ready stuck");
        repeat (400) @(posedge clk);
        issue(10'd0, 32'h7, 32'h8, 32'hF, 32'hF, "after stuck ends");
        $display("%0s: timeouts=%0d late_answers=%0d", NAME, timeouts, late);
`ifndef OLD
        if (timeouts != 2) begin
            $display("FAIL: timeouts=%0d expected 2", timeouts);
            errors = errors + 1;
        end
`endif
`ifdef OLD
        if (errors == 0) $display("REPRODUCED: %0s takes stale answers (0x300, 0x30) as shown above", NAME);
        else $display("NOT REPRODUCED: %0s (%0d differences from the predicted stale answers)", NAME, errors);
`else
        if (errors == 0) $display("PASS: tb_bridge %0s", NAME);
        else $display("FAIL: tb_bridge %0s (%0d errors)", NAME, errors);
`endif
        $finish;
    end
endmodule
