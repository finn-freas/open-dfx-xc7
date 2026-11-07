`timescale 1ns/1ps
module R2V_RAMB36E1 #(
    parameter integer DOA_REG = 0,
    parameter integer DOB_REG = 0,
    parameter [35:0] INIT_A = 36'h0,
    parameter [35:0] INIT_B = 36'h0,
    parameter [35:0] SRVAL_A = 36'h0,
    parameter [35:0] SRVAL_B = 36'h0,
    parameter RAM_MODE = "TDP",
    parameter integer READ_WIDTH_A = 0,
    parameter integer READ_WIDTH_B = 0,
    parameter integer WRITE_WIDTH_A = 0,
    parameter integer WRITE_WIDTH_B = 0,
    parameter WRITE_MODE_A = "WRITE_FIRST",
    parameter WRITE_MODE_B = "WRITE_FIRST",
    parameter [0:0] IS_CLKARDCLK_INVERTED = 1'b0,
    parameter [0:0] IS_CLKBWRCLK_INVERTED = 1'b0,
    parameter [0:0] IS_ENARDEN_INVERTED = 1'b0,
    parameter [0:0] IS_ENBWREN_INVERTED = 1'b0,
    parameter [0:0] IS_RSTRAMARSTRAM_INVERTED = 1'b0,
    parameter [0:0] IS_RSTRAMB_INVERTED = 1'b0,
    parameter [0:0] IS_RSTREGARSTREG_INVERTED = 1'b0,
    parameter [0:0] IS_RSTREGB_INVERTED = 1'b0,
    parameter [32767:0] INIT = 32768'h0,
    parameter [4095:0] INITP = 4096'h0
) (
    input CLKARDCLK, input CLKBWRCLK, input ENARDEN, input ENBWREN, input REGCEAREGCE, input REGCEB,
    input RSTRAMARSTRAM, input RSTRAMB, input RSTREGARSTREG, input RSTREGB,
    input [15:0] ADDRARDADDR, input [15:0] ADDRBWRADDR,
    input [31:0] DIADI, input [31:0] DIBDI, input [3:0] DIPADIP, input [3:0] DIPBDIP,
    input [3:0] WEA, input [7:0] WEBWE,
    output [31:0] DOADO, output [31:0] DOBDO, output [3:0] DOPADOP, output [3:0] DOPBDOP
);
    function integer dbits(input integer w);
        dbits = (w == 36) ? 32 : (w == 18) ? 16 : (w == 9) ? 8 : w;
    endfunction
    function integer pbits(input integer w);
        pbits = (w == 36) ? 4 : (w == 18) ? 2 : (w == 9) ? 1 : 0;
    endfunction
    function integer lg2(input integer d);
        lg2 = (d == 32) ? 5 : (d == 16) ? 4 : (d == 8) ? 3 : (d == 4) ? 2 : (d == 2) ? 1 : 0;
    endfunction
    function okw(input integer w);
        okw = (w == 0) || (w == 1) || (w == 2) || (w == 4) || (w == 9) || (w == 18) || (w == 36);
    endfunction

    localparam integer WA = (READ_WIDTH_A > WRITE_WIDTH_A) ? READ_WIDTH_A : WRITE_WIDTH_A;
    localparam integer WB = (READ_WIDTH_B > WRITE_WIDTH_B) ? READ_WIDTH_B : WRITE_WIDTH_B;
    localparam integer DA = dbits(WA);
    localparam integer DB = dbits(WB);
    localparam integer PA = pbits(WA);
    localparam integer PB = pbits(WB);
    localparam integer LA = lg2(DA);
    localparam integer LB = lg2(DB);

    reg [32767:0] mem;
    reg [4095:0] memp;
    reg [31:0] lat_a, lat_b, oreg_a, oreg_b;
    reg [3:0] latp_a, latp_b, oregp_a, oregp_b;

    wire clka = CLKARDCLK ^ IS_CLKARDCLK_INVERTED;
    wire clkb = CLKBWRCLK ^ IS_CLKBWRCLK_INVERTED;
    wire ena = ENARDEN ^ IS_ENARDEN_INVERTED;
    wire enb = ENBWREN ^ IS_ENBWREN_INVERTED;
    wire rsta = RSTRAMARSTRAM ^ IS_RSTRAMARSTRAM_INVERTED;
    wire rstb = RSTRAMB ^ IS_RSTRAMB_INVERTED;
    wire rrga = RSTREGARSTREG ^ IS_RSTREGARSTREG_INVERTED;
    wire rrgb = RSTREGB ^ IS_RSTREGB_INVERTED;

    initial begin
        mem = INIT;
        memp = INITP;
        lat_a = INIT_A[31:0]; latp_a = INIT_A[35:32]; oreg_a = INIT_A[31:0]; oregp_a = INIT_A[35:32];
        lat_b = INIT_B[31:0]; latp_b = INIT_B[35:32]; oreg_b = INIT_B[31:0]; oregp_b = INIT_B[35:32];
        if (RAM_MODE != "TDP" || !okw(READ_WIDTH_A) || !okw(READ_WIDTH_B) || !okw(WRITE_WIDTH_A) || !okw(WRITE_WIDTH_B)
            || (READ_WIDTH_A != 0 && WRITE_WIDTH_A != 0 && READ_WIDTH_A != WRITE_WIDTH_A)
            || (READ_WIDTH_B != 0 && WRITE_WIDTH_B != 0 && READ_WIDTH_B != WRITE_WIDTH_B)) begin
            $display("R2V-UNSUPPORTED R2V_RAMB36E1 %m: RAM_MODE=%0s RW_A=%0d WW_A=%0d RW_B=%0d WW_B=%0d",
                     RAM_MODE, READ_WIDTH_A, WRITE_WIDTH_A, READ_WIDTH_B, WRITE_WIDTH_B);
            $finish;
        end
    end

    task port_access(input integer d, input integer p, input integer l, input [15:0] addr, input [31:0] di, input [3:0] dip,
                     input [3:0] we, input integer mode, inout [31:0] dout, inout [3:0] dpout);
        integer i, idx;
        reg [31:0] rd;
        reg [3:0] rp;
        reg anywe;
        begin
            idx = addr[14:0] >> l;
            rd = 32'd0;
            rp = 4'd0;
            for (i = 0; i < d; i = i + 1) rd[i] = mem[idx * d + i];
            for (i = 0; i < p; i = i + 1) rp[i] = memp[idx * p + i];
            anywe = 1'b0;
            for (i = 0; i < d; i = i + 1)
                if (we[(d >= 8) ? (i / 8) : 0] === 1'b1) begin
                    mem[idx * d + i] = di[i];
                    anywe = 1'b1;
                end
            for (i = 0; i < p; i = i + 1)
                if (we[i] === 1'b1) memp[idx * p + i] = dip[i];
            if (mode == 1) begin
                rd = 32'd0;
                rp = 4'd0;
                for (i = 0; i < d; i = i + 1) rd[i] = mem[idx * d + i];
                for (i = 0; i < p; i = i + 1) rp[i] = memp[idx * p + i];
            end
            if (!(mode == 2 && anywe)) begin
                dout = rd;
                dpout = rp;
            end
        end
    endtask

    localparam integer MODE_A = (WRITE_MODE_A == "WRITE_FIRST") ? 1 : (WRITE_MODE_A == "NO_CHANGE") ? 2 : 0;
    localparam integer MODE_B = (WRITE_MODE_B == "WRITE_FIRST") ? 1 : (WRITE_MODE_B == "NO_CHANGE") ? 2 : 0;
    reg [31:0] ta, tb;
    reg [3:0] tpa, tpb;

    always @(posedge clka) begin
        if (DOA_REG != 0 && REGCEAREGCE === 1'b1) begin
            oreg_a <= (rrga === 1'b1) ? SRVAL_A[31:0] : lat_a;
            oregp_a <= (rrga === 1'b1) ? SRVAL_A[35:32] : latp_a;
        end
        if (WA != 0 && ena === 1'b1) begin
            ta = lat_a; tpa = latp_a;
            port_access(DA, PA, LA, ADDRARDADDR, DIADI, DIPADIP, (WRITE_WIDTH_A != 0) ? WEA : 4'd0, MODE_A, ta, tpa);
            if (rsta === 1'b1) begin ta = SRVAL_A[31:0]; tpa = SRVAL_A[35:32]; end
            lat_a <= ta; latp_a <= tpa;
        end
    end
    always @(posedge clkb) begin
        if (DOB_REG != 0 && REGCEB === 1'b1) begin
            oreg_b <= (rrgb === 1'b1) ? SRVAL_B[31:0] : lat_b;
            oregp_b <= (rrgb === 1'b1) ? SRVAL_B[35:32] : latp_b;
        end
        if (WB != 0 && enb === 1'b1) begin
            tb = lat_b; tpb = latp_b;
            port_access(DB, PB, LB, ADDRBWRADDR, DIBDI, DIPBDIP, (WRITE_WIDTH_B != 0) ? WEBWE[3:0] : 4'd0, MODE_B, tb, tpb);
            if (rstb === 1'b1) begin tb = SRVAL_B[31:0]; tpb = SRVAL_B[35:32]; end
            lat_b <= tb; latp_b <= tpb;
        end
    end

    assign DOADO = (DOA_REG != 0) ? oreg_a : lat_a;
    assign DOPADOP = (DOA_REG != 0) ? oregp_a : latp_a;
    assign DOBDO = (DOB_REG != 0) ? oreg_b : lat_b;
    assign DOPBDOP = (DOB_REG != 0) ? oregp_b : latp_b;
endmodule
