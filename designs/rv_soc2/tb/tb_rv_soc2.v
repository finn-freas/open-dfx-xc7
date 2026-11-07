`timescale 1ns/1ps
module tb_rv_soc2;
    localparam CPB = 100;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rx = 1'b1;
    wire tx;
    wire [3:0] led;
    rv_soc #(.MEM_INIT("designs/rv_soc2/fw/main.hex"), .CLKS_PER_BIT(CPB)) dut (
        .clk(clk), .uart_txd_in(rx), .uart_rxd_out(tx), .led(led));

    reg [8*16-1:0] rm1, rm2;

    function [31:0] model(input [8*16-1:0] rm, input [31:0] a, input [31:0] b);
        begin
            if (rm == "xor") model = a ^ b;
            else if (rm == "andn") model = a & ~b;
            else if (rm == "add") model = a + b;
            else if (rm == "grey") model = 32'd0;
            else model = 32'hxxxxxxxx;
        end
    endfunction

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

    task wait_bytes(input integer n);
        integer t;
        begin
            t = 0;
            while (ngot < n && t < CPB * 200) begin
                @(posedge clk);
                t = t + 1;
            end
        end
    endtask

    integer errors = 0;
    integer n1 = 0, n2 = 0;
    always @(posedge clk) begin
        if (dut.slot_valid) n1 = n1 + 1;
        if (dut.slot2_valid) n2 = n2 + 1;
    end

    task do_cmd(input [7:0] cmd, input [31:0] a, input [31:0] b);
        integer base, v1, v2;
        reg [31:0] r, e;
        begin
            base = ngot;
            v1 = n1;
            v2 = n2;
            send_byte(cmd); send_word(a); send_word(b);
            wait_bytes(base + 4);
            repeat (CPB * 12) @(posedge clk);
            r = {got[base], got[base + 1], got[base + 2], got[base + 3]};
            e = model(cmd == "C" ? rm1 : rm2, a, b);
            if (ngot != base + 4) begin
                $display("FAIL: %c %08x %08x: got %0d reply bytes, expected 4", cmd, a, b, ngot - base);
                errors = errors + 1;
            end else if (r !== e) begin
                $display("FAIL: %c %08x %08x: reply %08x expected %08x", cmd, a, b, r, e);
                errors = errors + 1;
            end else begin
                $display("ok:   %c %08x %08x -> %08x (%0s)", cmd, a, b, r, cmd == "C" ? rm1 : rm2);
            end
            if (led !== e[3:0]) begin
                $display("FAIL: led=%x expected %x", led, e[3:0]);
                errors = errors + 1;
            end
            if (cmd == "C" && (n1 - v1 != 1 || n2 != v2)) begin
                $display("FAIL: C strobed slot1 %0d times, slot2 %0d times (expected 1, 0)", n1 - v1, n2 - v2);
                errors = errors + 1;
            end
            if (cmd == "D" && (n2 - v2 != 1 || n1 != v1)) begin
                $display("FAIL: D strobed slot2 %0d times, slot1 %0d times (expected 1, 0)", n2 - v2, n1 - v1);
                errors = errors + 1;
            end
        end
    endtask

    reg [31:0] words [0:7];
    integer k, base, nw0;
    initial begin
        if (!$value$plusargs("RM1=%s", rm1)) rm1 = "xor";
        if (!$value$plusargs("RM2=%s", rm2)) rm2 = "add";
        words[0] = 32'hFFFFFFFF; words[1] = 32'hAA995566; words[2] = 32'h20000000; words[3] = 32'h30008001;
        words[4] = 32'h00000007; words[5] = 32'h12345678; words[6] = 32'h80000001; words[7] = 32'h0F1E2D3C;
        repeat (200) @(posedge clk);
        do_cmd("C", 32'h12345678, 32'h11111111);
        do_cmd("D", 32'h12345678, 32'h11111111);
        do_cmd("D", 32'hFFFFFFFF, 32'h00000003);
        do_cmd("C", 32'hFFFFFFFF, 32'h00000003);

        base = ngot;
        nw0 = dut.u_icap.nw;
        send_byte("W"); send_word(32'd8);
        for (k = 0; k < 8; k = k + 1) send_word(words[k]);
        wait_bytes(base + 1);
        repeat (CPB * 12) @(posedge clk);
        if (ngot != base + 1 || got[base] !== "K") begin
            $display("FAIL: W: reply count %0d byte %02x, expected one 'K'", ngot - base, got[base]);
            errors = errors + 1;
        end else begin
            $display("ok:   W 8 words -> 'K'");
        end
        if (dut.u_icap.nw - nw0 != 8) begin
            $display("FAIL: ICAP got %0d writes, expected 8", dut.u_icap.nw - nw0);
            errors = errors + 1;
        end
        for (k = 0; k < 8; k = k + 1)
            if (dut.u_icap.wmem[nw0 + k] !== bswap(words[k])) begin
                $display("FAIL: ICAP word %0d = %08x expected %08x", k, dut.u_icap.wmem[nw0 + k], bswap(words[k]));
                errors = errors + 1;
            end

        do_cmd("C", 32'hA5A5A5A5, 32'h0F0F0F0F);
        do_cmd("D", 32'hA5A5A5A5, 32'h0F0F0F0F);
        do_cmd("D", 32'h80000000, 32'h80000000);
        if (dut.trap) begin
            $display("FAIL: cpu trapped");
            errors = errors + 1;
        end
        if (dut.slot_timeouts != 0) begin
            $display("FAIL: %0d slot timeouts", dut.slot_timeouts);
            errors = errors + 1;
        end
        if (errors == 0) $display("PASS: tb_rv_soc2 rp1=%0s rp2=%0s (slot1 strobes %0d, slot2 strobes %0d)", rm1, rm2, n1, n2);
        else $display("FAIL: tb_rv_soc2 rp1=%0s rp2=%0s (%0d errors)", rm1, rm2, errors);
        $finish;
    end
endmodule
