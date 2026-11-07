`timescale 1ns/1ps
module tb_isa;
    reg clk = 0;
    always #5 clk = ~clk;
    wire txd;
    wire [3:0] led;
    rv_soc #(.MEM_INIT("build/rv_soc/isa_test.hex"), .CLKS_PER_BIT(100)) dut (
        .clk(clk), .uart_txd_in(1'b1), .uart_rxd_out(txd), .led(led));

`ifdef RM_XOR
    localparam [31:0] CUSTOM = 32'hedcba983;
    localparam NAME = "rm_xor";
    localparam EXP_TIMEOUTS = 0;
`elsif RM_DEAD
    localparam [31:0] CUSTOM = 32'h00000000;
    localparam NAME = "rm_dead";
    localparam EXP_TIMEOUTS = 2;
`else
    localparam [31:0] CUSTOM = 32'h12345673;
    localparam NAME = "rm_add";
    localparam EXP_TIMEOUTS = 0;
`endif

    reg [31:0] exp [0:37];
    reg [9:0] functs [0:7];
    integer nf = 0;
    always @(posedge clk) if (dut.slot_valid) begin
        functs[nf] = dut.slot_funct;
        nf = nf + 1;
    end

    integer k, errors, cyc;
    reg done;
    initial begin
        exp[0] = 32'h12345678; exp[1] = 32'hfffffffb; exp[2] = 32'h12345673; exp[3] = 32'h1234567d;
        exp[4] = 32'hedcba983; exp[5] = 32'hfffffffb; exp[6] = 32'h12345678; exp[7] = 32'h00000001;
        exp[8] = 32'h00000000; exp[9] = 32'h23456780; exp[10] = 32'h0000000f; exp[11] = 32'hfffffffd;
        exp[12] = 32'h91a2b3c0; exp[13] = 32'h1fffffff; exp[14] = 32'hffffffff; exp[15] = 32'h12345000;
        exp[16] = 32'h12345687; exp[17] = 32'h1234567f; exp[18] = 32'h00000070; exp[19] = 32'h00000001;
        exp[20] = 32'h00000001; exp[21] = 32'h00000000; exp[22] = 32'h80818283; exp[23] = 32'hffffff83;
        exp[24] = 32'h00000083; exp[25] = 32'hffff8081; exp[26] = 32'h00008081; exp[27] = 32'h00005500;
        exp[28] = 32'hbeef0000; exp[29] = 32'h0000002a; exp[30] = 32'h00000005; exp[31] = 32'h00000077;
        exp[32] = 32'h00000000; exp[33] = 32'h00000000; exp[34] = CUSTOM; exp[35] = CUSTOM;
        exp[36] = 32'habcde000; exp[37] = 32'h037b0000;
        errors = 0;
        done = 0;
        for (cyc = 0; cyc < 20000 && !done; cyc = cyc + 1) begin
            @(posedge clk);
            if (dut.ram[1024 + 63] === 32'h600df00d) done = 1;
            if (dut.trap) begin
                $display("FAIL: cpu trapped at cycle %0d", cyc);
                errors = errors + 1;
                done = 1;
            end
        end
        if (dut.ram[1024 + 63] !== 32'h600df00d) begin
            $display("FAIL: completion marker not written");
            errors = errors + 1;
        end
        for (k = 0; k <= 37; k = k + 1)
            if (dut.ram[1024 + k] !== exp[k]) begin
                $display("FAIL: result[%0d] = %08x expected %08x", k, dut.ram[1024 + k], exp[k]);
                errors = errors + 1;
            end
        if (nf != 2 || functs[0] !== 10'h000 || functs[1] !== 10'h3ff) begin
            $display("FAIL: rm_slot funct sequence n=%0d %03x %03x (expected 000 3ff)", nf, functs[0], functs[1]);
            errors = errors + 1;
        end
        if (dut.slot_timeouts != EXP_TIMEOUTS) begin
            $display("FAIL: slot timeouts %0d expected %0d", dut.slot_timeouts, EXP_TIMEOUTS);
            errors = errors + 1;
        end
        $display("isa_test[%0s]: %0d results checked, %0d custom0 issues, timeouts=%0d, finished in %0d cycles",
                 NAME, 38, nf, dut.slot_timeouts, cyc);
        if (errors == 0) $display("PASS: tb_isa %0s", NAME);
        else $display("FAIL: tb_isa %0s (%0d errors)", NAME, errors);
        $finish;
    end
endmodule
