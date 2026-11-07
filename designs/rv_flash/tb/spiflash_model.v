`timescale 1ns/1ps
module spiflash_model #(
    parameter WIN_BASE = 32'h0040_0000,
    parameter WIN_BYTES = 32'h0003_0000,
    parameter INIT = "build/rv_flash/sim/flash_window.hex",
    parameter [23:0] JEDEC = 24'h012018,
    parameter real TV_NS = 8.0,
    parameter real MIN_PERIOD_NS = 20.0
) (input wire cs_n, input wire sck, input wire mosi, output reg miso = 1'bz);
    reg [7:0] mem [0:WIN_BYTES-1];
    initial $readmemh(INIT, mem);
    integer nbits = 0;
    reg [7:0] cmd = 8'd0;
    reg [23:0] addr = 24'd0;
    integer reads = 0, ids = 0, unknown = 0, timing_errors = 0;
    real last_rise = -1.0;

    function [7:0] rdbyte(input [31:0] a);
        begin
            if (a >= WIN_BASE && a < WIN_BASE + WIN_BYTES) rdbyte = mem[a - WIN_BASE];
            else rdbyte = 8'hFF;
        end
    endfunction

    always @(negedge cs_n) begin
        nbits = 0;
        cmd = 8'd0;
    end
    always @(posedge cs_n) begin
        miso <= 1'bz;
        if (nbits >= 8) begin
            if (cmd == 8'h03) reads = reads + 1;
            else if (cmd == 8'h9F) ids = ids + 1;
            else unknown = unknown + 1;
        end
    end
    always @(posedge sck) if (!cs_n) begin
        if (last_rise >= 0.0 && $realtime - last_rise < MIN_PERIOD_NS) begin
            timing_errors = timing_errors + 1;
            $display("FLASH: SCK period %0.1f ns < %0.1f ns", $realtime - last_rise, MIN_PERIOD_NS);
        end
        last_rise = $realtime;
        if (nbits < 8) cmd = {cmd[6:0], mosi};
        else if (nbits < 32 && cmd == 8'h03) addr = {addr[22:0], mosi};
        nbits = nbits + 1;
    end
    always @(negedge sck) if (!cs_n) begin : drive
        integer j;
        reg [7:0] b;
        if (cmd == 8'h03 && nbits >= 32) begin
            j = nbits - 32;
            b = rdbyte(addr + j / 8);
            miso <= #(TV_NS) b[7 - j % 8];
        end else if (cmd == 8'h9F && nbits >= 8) begin
            j = nbits - 8;
            b = j < 8 ? JEDEC[23:16] : j < 16 ? JEDEC[15:8] : j < 24 ? JEDEC[7:0] : 8'hFF;
            miso <= #(TV_NS) b[7 - j % 8];
        end
    end
endmodule
