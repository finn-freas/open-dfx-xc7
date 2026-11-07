`timescale 1ns/1ps
module tb_rv_flash;
    localparam CPB = 100;
    localparam [23:0] JEDEC = 24'h012018;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rx = 1'b1;
    wire tx;
    wire [3:0] led;
    wire cs, sck, dq0, dq1, dq2, dq3;
    pullup (dq1);
    rv_flash #(.MEM_INIT("designs/rv_flash/fw/main.hex"), .CLKS_PER_BIT(CPB), .SPI_DIV(`SPI_DIV)) dut (
        .clk(clk), .uart_txd_in(rx), .uart_rxd_out(tx), .led(led),
        .qspi_cs(cs), .qspi_sck(sck), .qspi_dq0(dq0), .qspi_dq1(dq1), .qspi_dq2(dq2), .qspi_dq3(dq3));
    spiflash_model #(.WIN_BASE(32'h0040_0000), .WIN_BYTES(32'h0003_0000), .INIT("build/rv_flash/sim/flash_window.hex"),
                     .JEDEC(JEDEC)) u_flash (.cs_n(cs), .sck(sck), .mosi(dq0), .miso(dq1));

    reg [31:0] pw [0:16383];
    integer npw;
    integer icap_writes = 0, icap_wr_coupled = 0, rp_valid_decoupled = 0, decoupled_cycles = 0;
    always @(posedge clk) begin
        if (!dut.icap_csib && !dut.icap_rdwrb) begin
            icap_writes = icap_writes + 1;
            if (!dut.decouple_r) icap_wr_coupled = icap_wr_coupled + 1;
        end
        if (dut.decouple_r) decoupled_cycles = decoupled_cycles + 1;
        if (dut.decouple_r && dut.rp_valid) rp_valid_decoupled = rp_valid_decoupled + 1;
    end
    initial begin : load_words
        integer i;
        for (i = 0; i < 16384; i = i + 1) pw[i] = 32'hxxxxxxxx;
        $readmemh("build/rv_flash/sim/slot0_words.hex", pw);
        npw = 0;
        while (npw < 16384 && pw[npw] !== 32'hxxxxxxxx) npw = npw + 1;
    end

    function [31:0] bswap(input [31:0] w);
        integer i;
        begin
            for (i = 0; i < 32; i = i + 1) bswap[i] = w[(i & ~7) + (7 - (i & 7))];
        end
    endfunction

    task send_byte(input [7:0] b);
        integer i;
        begin
            rx = 1'b0;
            repeat (CPB) @(posedge clk);
            for (i = 0; i < 8; i = i + 1) begin
                rx = b[i];
                repeat (CPB) @(posedge clk);
            end
            rx = 1'b1;
            repeat (CPB) @(posedge clk);
        end
    endtask

    task send_word(input [31:0] w);
        begin
            send_byte(w[31:24]); send_byte(w[23:16]); send_byte(w[15:8]); send_byte(w[7:0]);
        end
    endtask

    reg [7:0] got [0:255];
    integer ngot = 0;
    always @(negedge tx) begin : rxmon
        integer i;
        reg [7:0] b;
        repeat (CPB + CPB / 2) @(posedge clk);
        for (i = 0; i < 8; i = i + 1) begin
            b[i] = tx;
            repeat (CPB) @(posedge clk);
        end
        got[ngot] = b;
        ngot = ngot + 1;
    end

    task wait_bytes(input integer n, input integer max_cycles);
        integer t;
        begin
            t = 0;
            while (ngot < n && t < max_cycles) begin
                @(posedge clk);
                t = t + 1;
            end
            repeat (CPB * 12) @(posedge clk);
        end
    endtask

    integer errors = 0;
    integer fout;

    task check_icap(input integer first, input integer n, input [8*16-1:0] what);
        integer k, bad;
        begin
            bad = 0;
            if (n != npw) begin
                $display("FAIL: %0s: ICAP got %0d words, partial has %0d", what, n, npw);
                errors = errors + 1;
            end
            for (k = 0; k < npw && k < n; k = k + 1)
                if (dut.u_icap.wmem[first + k] !== bswap(pw[k])) begin
                    if (bad < 5) $display("FAIL: %0s: ICAP word %0d = %08x expected %08x (bswap of %08x)",
                                          what, k, dut.u_icap.wmem[first + k], bswap(pw[k]), pw[k]);
                    bad = bad + 1;
                end
            if (bad) errors = errors + 1;
            else if (n == npw) $display("ok:   %0s: %0d ICAP words == bswap(partial words), first %08x last %08x",
                                        what, n, dut.u_icap.wmem[first], dut.u_icap.wmem[first + n - 1]);
        end
    endtask

    task expect_bytes(input integer base, input integer n, input [8*48-1:0] what);
        begin
            if (ngot != base + n) begin
                $display("FAIL: %0s: got %0d reply bytes, expected %0d", what, ngot - base, n);
                errors = errors + 1;
            end
        end
    endtask

    integer base, nw0, k, t0;
    reg [31:0] r;
    initial begin
        repeat (200) @(posedge clk);

        base = ngot;
        send_byte("J");
        wait_bytes(base + 3, 20000);
        expect_bytes(base, 3, "J");
        if ({got[base], got[base + 1], got[base + 2]} !== JEDEC) begin
            $display("FAIL: J: %02x %02x %02x expected %06x", got[base], got[base + 1], got[base + 2], JEDEC);
            errors = errors + 1;
        end else $display("ok:   J -> %02x %02x %02x", got[base], got[base + 1], got[base + 2]);

        base = ngot;
        send_byte("R"); send_word(32'h0040_0000);
        wait_bytes(base + 4, 20000);
        r = {got[base], got[base + 1], got[base + 2], got[base + 3]};
        if (r !== 32'h50524631) begin
            $display("FAIL: R 00400000 -> %08x expected 50524631", r);
            errors = errors + 1;
        end else $display("ok:   R 00400000 -> %08x (slot 0 magic)", r);

        base = ngot;
        nw0 = dut.u_icap.nw;
        t0 = $time;
        send_byte("S"); send_byte(8'd0);
        wait_bytes(base + 1, 20000000);
        expect_bytes(base, 1, "S 0");
        if (got[base] !== "K") begin
            $display("FAIL: S 0 status %02x expected 'K'", got[base]);
            errors = errors + 1;
        end else $display("ok:   S 0 -> 'K' after %0d us simulated", ($time - t0) / 1000);
        check_icap(nw0, dut.u_icap.nw - nw0, "S 0");
        fout = $fopen("build/rv_flash/sim/icap_words_s0.hex", "w");
        for (k = nw0; k < dut.u_icap.nw; k = k + 1) $fwrite(fout, "%08x\n", dut.u_icap.wmem[k]);
        $fclose(fout);

        base = ngot;
        nw0 = dut.u_icap.nw;
        send_byte("S"); send_byte(8'd1);
        wait_bytes(base + 1, 200000);
        if (got[base] !== "E" || dut.u_icap.nw != nw0) begin
            $display("FAIL: S 1 (erased) status %02x, %0d ICAP writes; expected 'E' and 0", got[base], dut.u_icap.nw - nw0);
            errors = errors + 1;
        end else $display("ok:   S 1 (erased slot) -> 'E', 0 ICAP writes");

        base = ngot;
        nw0 = dut.u_icap.nw;
        send_byte("S"); send_byte(8'd2);
        wait_bytes(base + 1, 20000000);
        if (got[base] !== "X" || dut.u_icap.nw != nw0) begin
            $display("FAIL: S 2 (corrupt) status %02x, %0d ICAP writes; expected 'X' and 0", got[base], dut.u_icap.nw - nw0);
            errors = errors + 1;
        end else $display("ok:   S 2 (one flipped bit) -> 'X', 0 ICAP writes");

        base = ngot;
        send_byte("C"); send_word(32'h12345678); send_word(32'h0F0F0F0F);
        wait_bytes(base + 4, 200000);
        r = {got[base], got[base + 1], got[base + 2], got[base + 3]};
        if (r !== 32'h12345678 + 32'h0F0F0F0F) begin
            $display("FAIL: C -> %08x expected %08x", r, 32'h12345678 + 32'h0F0F0F0F);
            errors = errors + 1;
        end else $display("ok:   C 12345678 0F0F0F0F -> %08x (rm_add in sim)", r);

        base = ngot;
        nw0 = dut.u_icap.nw;
        send_byte("A"); send_word(32'h12345678); send_word(32'h0F0F0F0F);
        wait_bytes(base + 7, 40000000);
        expect_bytes(base, 7, "A");
        r = {got[base + 1], got[base + 2], got[base + 3], got[base + 4]};
        if (got[base] !== "K" || r !== 32'h12345678 + 32'h0F0F0F0F || got[base + 5] !== "E" || got[base + 6] !== ".") begin
            $display("FAIL: A -> %02x %08x %02x %02x expected 'K' %08x 'E' '.'", got[base], r, got[base + 5], got[base + 6],
                     32'h12345678 + 32'h0F0F0F0F);
            errors = errors + 1;
        end else $display("ok:   A -> 'K' %08x 'E' '.' (slot 0 loaded and run, stopped at erased slot 1)", r);
        check_icap(nw0, dut.u_icap.nw - nw0, "A slot 0");

        if (dut.trap) begin
            $display("FAIL: cpu trapped");
            errors = errors + 1;
        end
        if (icap_wr_coupled || rp_valid_decoupled || dut.decouple_r || !decoupled_cycles) begin
            $display("FAIL: decoupler: %0d ICAP writes while coupled, %0d RP valid while decoupled, decouple at end %0d, %0d decoupled cycles",
                     icap_wr_coupled, rp_valid_decoupled, dut.decouple_r, decoupled_cycles);
            errors = errors + 1;
        end else $display("ok:   decoupler: 0 of %0d ICAP writes while coupled, 0 RP valid while decoupled, %0d decoupled cycles, released at end",
                          icap_writes, decoupled_cycles);
        if (u_flash.timing_errors || u_flash.unknown) begin
            $display("FAIL: flash model: %0d timing errors, %0d unknown commands", u_flash.timing_errors, u_flash.unknown);
            errors = errors + 1;
        end
        $display("flash model: %0d READ transactions, %0d RDID; SPI_DIV=%0d; slot timeouts=%0d late=%0d",
                 u_flash.reads, u_flash.ids, `SPI_DIV, dut.slot_timeouts, dut.slot_late);
        if (errors == 0) $display("PASS: tb_rv_flash");
        else $display("FAIL: tb_rv_flash (%0d errors)", errors);
        $finish;
    end
endmodule
