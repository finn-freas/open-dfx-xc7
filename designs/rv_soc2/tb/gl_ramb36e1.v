`timescale 1ns/1ps
module RAMB36E1 (
    output CASCADEOUTA, output CASCADEOUTB,
    output [31:0] DOADO, output [31:0] DOBDO, output [3:0] DOPADOP, output [3:0] DOPBDOP,
    output [7:0] ECCPARITY, output [8:0] RDADDRECC, output SBITERR, output DBITERR,
    input ENARDEN, input CLKARDCLK, input RSTRAMARSTRAM, input RSTREGARSTREG, input CASCADEINA, input REGCEAREGCE,
    input ENBWREN, input CLKBWRCLK, input RSTRAMB, input RSTREGB, input CASCADEINB, input REGCEB,
    input INJECTDBITERR, input INJECTSBITERR,
    input [15:0] ADDRARDADDR, input [15:0] ADDRBWRADDR,
    input [31:0] DIADI, input [31:0] DIBDI, input [3:0] DIPADIP, input [3:0] DIPBDIP,
    input [3:0] WEA, input [7:0] WEBWE
);
    parameter integer DOA_REG = 0;
    parameter integer DOB_REG = 0;
    parameter EN_ECC_READ = "FALSE";
    parameter EN_ECC_WRITE = "FALSE";
    parameter INIT_A = 36'h0;
    parameter INIT_B = 36'h0;
    parameter INIT_FILE = "NONE";
    parameter RAM_EXTENSION_A = "NONE";
    parameter RAM_EXTENSION_B = "NONE";
    parameter RAM_MODE = "TDP";
    parameter RDADDR_COLLISION_HWCONFIG = "DELAYED_WRITE";
    parameter integer READ_WIDTH_A = 0;
    parameter integer READ_WIDTH_B = 0;
    parameter RSTREG_PRIORITY_A = "RSTREG";
    parameter RSTREG_PRIORITY_B = "RSTREG";
    parameter SIM_COLLISION_CHECK = "ALL";
    parameter SIM_DEVICE = "VIRTEX6";
    parameter SRVAL_A = 36'h0;
    parameter SRVAL_B = 36'h0;
    parameter WRITE_MODE_A = "WRITE_FIRST";
    parameter WRITE_MODE_B = "WRITE_FIRST";
    parameter integer WRITE_WIDTH_A = 0;
    parameter integer WRITE_WIDTH_B = 0;
    parameter IS_CLKARDCLK_INVERTED = 1'b0;
    parameter IS_CLKBWRCLK_INVERTED = 1'b0;
    parameter IS_ENARDEN_INVERTED = 1'b0;
    parameter IS_ENBWREN_INVERTED = 1'b0;
    parameter IS_RSTRAMARSTRAM_INVERTED = 1'b0;
    parameter IS_RSTRAMB_INVERTED = 1'b0;
    parameter IS_RSTREGARSTREG_INVERTED = 1'b0;
    parameter IS_RSTREGB_INVERTED = 1'b0;
    parameter [255:0] INIT_00 = 256'h0;
    parameter [255:0] INIT_01 = 256'h0;
    parameter [255:0] INIT_02 = 256'h0;
    parameter [255:0] INIT_03 = 256'h0;
    parameter [255:0] INIT_04 = 256'h0;
    parameter [255:0] INIT_05 = 256'h0;
    parameter [255:0] INIT_06 = 256'h0;
    parameter [255:0] INIT_07 = 256'h0;
    parameter [255:0] INIT_08 = 256'h0;
    parameter [255:0] INIT_09 = 256'h0;
    parameter [255:0] INIT_0A = 256'h0;
    parameter [255:0] INIT_0B = 256'h0;
    parameter [255:0] INIT_0C = 256'h0;
    parameter [255:0] INIT_0D = 256'h0;
    parameter [255:0] INIT_0E = 256'h0;
    parameter [255:0] INIT_0F = 256'h0;
    parameter [255:0] INIT_10 = 256'h0;
    parameter [255:0] INIT_11 = 256'h0;
    parameter [255:0] INIT_12 = 256'h0;
    parameter [255:0] INIT_13 = 256'h0;
    parameter [255:0] INIT_14 = 256'h0;
    parameter [255:0] INIT_15 = 256'h0;
    parameter [255:0] INIT_16 = 256'h0;
    parameter [255:0] INIT_17 = 256'h0;
    parameter [255:0] INIT_18 = 256'h0;
    parameter [255:0] INIT_19 = 256'h0;
    parameter [255:0] INIT_1A = 256'h0;
    parameter [255:0] INIT_1B = 256'h0;
    parameter [255:0] INIT_1C = 256'h0;
    parameter [255:0] INIT_1D = 256'h0;
    parameter [255:0] INIT_1E = 256'h0;
    parameter [255:0] INIT_1F = 256'h0;
    parameter [255:0] INIT_20 = 256'h0;
    parameter [255:0] INIT_21 = 256'h0;
    parameter [255:0] INIT_22 = 256'h0;
    parameter [255:0] INIT_23 = 256'h0;
    parameter [255:0] INIT_24 = 256'h0;
    parameter [255:0] INIT_25 = 256'h0;
    parameter [255:0] INIT_26 = 256'h0;
    parameter [255:0] INIT_27 = 256'h0;
    parameter [255:0] INIT_28 = 256'h0;
    parameter [255:0] INIT_29 = 256'h0;
    parameter [255:0] INIT_2A = 256'h0;
    parameter [255:0] INIT_2B = 256'h0;
    parameter [255:0] INIT_2C = 256'h0;
    parameter [255:0] INIT_2D = 256'h0;
    parameter [255:0] INIT_2E = 256'h0;
    parameter [255:0] INIT_2F = 256'h0;
    parameter [255:0] INIT_30 = 256'h0;
    parameter [255:0] INIT_31 = 256'h0;
    parameter [255:0] INIT_32 = 256'h0;
    parameter [255:0] INIT_33 = 256'h0;
    parameter [255:0] INIT_34 = 256'h0;
    parameter [255:0] INIT_35 = 256'h0;
    parameter [255:0] INIT_36 = 256'h0;
    parameter [255:0] INIT_37 = 256'h0;
    parameter [255:0] INIT_38 = 256'h0;
    parameter [255:0] INIT_39 = 256'h0;
    parameter [255:0] INIT_3A = 256'h0;
    parameter [255:0] INIT_3B = 256'h0;
    parameter [255:0] INIT_3C = 256'h0;
    parameter [255:0] INIT_3D = 256'h0;
    parameter [255:0] INIT_3E = 256'h0;
    parameter [255:0] INIT_3F = 256'h0;
    parameter [255:0] INIT_40 = 256'h0;
    parameter [255:0] INIT_41 = 256'h0;
    parameter [255:0] INIT_42 = 256'h0;
    parameter [255:0] INIT_43 = 256'h0;
    parameter [255:0] INIT_44 = 256'h0;
    parameter [255:0] INIT_45 = 256'h0;
    parameter [255:0] INIT_46 = 256'h0;
    parameter [255:0] INIT_47 = 256'h0;
    parameter [255:0] INIT_48 = 256'h0;
    parameter [255:0] INIT_49 = 256'h0;
    parameter [255:0] INIT_4A = 256'h0;
    parameter [255:0] INIT_4B = 256'h0;
    parameter [255:0] INIT_4C = 256'h0;
    parameter [255:0] INIT_4D = 256'h0;
    parameter [255:0] INIT_4E = 256'h0;
    parameter [255:0] INIT_4F = 256'h0;
    parameter [255:0] INIT_50 = 256'h0;
    parameter [255:0] INIT_51 = 256'h0;
    parameter [255:0] INIT_52 = 256'h0;
    parameter [255:0] INIT_53 = 256'h0;
    parameter [255:0] INIT_54 = 256'h0;
    parameter [255:0] INIT_55 = 256'h0;
    parameter [255:0] INIT_56 = 256'h0;
    parameter [255:0] INIT_57 = 256'h0;
    parameter [255:0] INIT_58 = 256'h0;
    parameter [255:0] INIT_59 = 256'h0;
    parameter [255:0] INIT_5A = 256'h0;
    parameter [255:0] INIT_5B = 256'h0;
    parameter [255:0] INIT_5C = 256'h0;
    parameter [255:0] INIT_5D = 256'h0;
    parameter [255:0] INIT_5E = 256'h0;
    parameter [255:0] INIT_5F = 256'h0;
    parameter [255:0] INIT_60 = 256'h0;
    parameter [255:0] INIT_61 = 256'h0;
    parameter [255:0] INIT_62 = 256'h0;
    parameter [255:0] INIT_63 = 256'h0;
    parameter [255:0] INIT_64 = 256'h0;
    parameter [255:0] INIT_65 = 256'h0;
    parameter [255:0] INIT_66 = 256'h0;
    parameter [255:0] INIT_67 = 256'h0;
    parameter [255:0] INIT_68 = 256'h0;
    parameter [255:0] INIT_69 = 256'h0;
    parameter [255:0] INIT_6A = 256'h0;
    parameter [255:0] INIT_6B = 256'h0;
    parameter [255:0] INIT_6C = 256'h0;
    parameter [255:0] INIT_6D = 256'h0;
    parameter [255:0] INIT_6E = 256'h0;
    parameter [255:0] INIT_6F = 256'h0;
    parameter [255:0] INIT_70 = 256'h0;
    parameter [255:0] INIT_71 = 256'h0;
    parameter [255:0] INIT_72 = 256'h0;
    parameter [255:0] INIT_73 = 256'h0;
    parameter [255:0] INIT_74 = 256'h0;
    parameter [255:0] INIT_75 = 256'h0;
    parameter [255:0] INIT_76 = 256'h0;
    parameter [255:0] INIT_77 = 256'h0;
    parameter [255:0] INIT_78 = 256'h0;
    parameter [255:0] INIT_79 = 256'h0;
    parameter [255:0] INIT_7A = 256'h0;
    parameter [255:0] INIT_7B = 256'h0;
    parameter [255:0] INIT_7C = 256'h0;
    parameter [255:0] INIT_7D = 256'h0;
    parameter [255:0] INIT_7E = 256'h0;
    parameter [255:0] INIT_7F = 256'h0;
    parameter [255:0] INITP_00 = 256'h0;
    parameter [255:0] INITP_01 = 256'h0;
    parameter [255:0] INITP_02 = 256'h0;
    parameter [255:0] INITP_03 = 256'h0;
    parameter [255:0] INITP_04 = 256'h0;
    parameter [255:0] INITP_05 = 256'h0;
    parameter [255:0] INITP_06 = 256'h0;
    parameter [255:0] INITP_07 = 256'h0;
    parameter [255:0] INITP_08 = 256'h0;
    parameter [255:0] INITP_09 = 256'h0;
    parameter [255:0] INITP_0A = 256'h0;
    parameter [255:0] INITP_0B = 256'h0;
    parameter [255:0] INITP_0C = 256'h0;
    parameter [255:0] INITP_0D = 256'h0;
    parameter [255:0] INITP_0E = 256'h0;
    parameter [255:0] INITP_0F = 256'h0;

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
    reg [31:0] doa, dob;
    reg [3:0] dopa, dopb;

    initial begin
        mem = {INIT_7F, INIT_7E, INIT_7D, INIT_7C, INIT_7B, INIT_7A, INIT_79, INIT_78, INIT_77, INIT_76, INIT_75, INIT_74, INIT_73, INIT_72, INIT_71, INIT_70, INIT_6F, INIT_6E, INIT_6D, INIT_6C, INIT_6B, INIT_6A, INIT_69, INIT_68, INIT_67, INIT_66, INIT_65, INIT_64, INIT_63, INIT_62, INIT_61, INIT_60, INIT_5F, INIT_5E, INIT_5D, INIT_5C, INIT_5B, INIT_5A, INIT_59, INIT_58, INIT_57, INIT_56, INIT_55, INIT_54, INIT_53, INIT_52, INIT_51, INIT_50, INIT_4F, INIT_4E, INIT_4D, INIT_4C, INIT_4B, INIT_4A, INIT_49, INIT_48, INIT_47, INIT_46, INIT_45, INIT_44, INIT_43, INIT_42, INIT_41, INIT_40, INIT_3F, INIT_3E, INIT_3D, INIT_3C, INIT_3B, INIT_3A, INIT_39, INIT_38, INIT_37, INIT_36, INIT_35, INIT_34, INIT_33, INIT_32, INIT_31, INIT_30, INIT_2F, INIT_2E, INIT_2D, INIT_2C, INIT_2B, INIT_2A, INIT_29, INIT_28, INIT_27, INIT_26, INIT_25, INIT_24, INIT_23, INIT_22, INIT_21, INIT_20, INIT_1F, INIT_1E, INIT_1D, INIT_1C, INIT_1B, INIT_1A, INIT_19, INIT_18, INIT_17, INIT_16, INIT_15, INIT_14, INIT_13, INIT_12, INIT_11, INIT_10, INIT_0F, INIT_0E, INIT_0D, INIT_0C, INIT_0B, INIT_0A, INIT_09, INIT_08, INIT_07, INIT_06, INIT_05, INIT_04, INIT_03, INIT_02, INIT_01, INIT_00};
        memp = {INITP_0F, INITP_0E, INITP_0D, INITP_0C, INITP_0B, INITP_0A, INITP_09, INITP_08, INITP_07, INITP_06, INITP_05, INITP_04, INITP_03, INITP_02, INITP_01, INITP_00};
        doa = 32'd0; dob = 32'd0; dopa = 4'd0; dopb = 4'd0;
        if (RAM_MODE != "TDP" || DOA_REG != 0 || DOB_REG != 0 || !okw(READ_WIDTH_A) || !okw(READ_WIDTH_B)
            || !okw(WRITE_WIDTH_A) || !okw(WRITE_WIDTH_B) || WA == 36 || WB == 36
            || (READ_WIDTH_A != 0 && WRITE_WIDTH_A != 0 && READ_WIDTH_A != WRITE_WIDTH_A)
            || (READ_WIDTH_B != 0 && WRITE_WIDTH_B != 0 && READ_WIDTH_B != WRITE_WIDTH_B)
            || RAM_EXTENSION_A != "NONE" || RAM_EXTENSION_B != "NONE" || EN_ECC_READ != "FALSE" || EN_ECC_WRITE != "FALSE"
            || IS_CLKARDCLK_INVERTED || IS_CLKBWRCLK_INVERTED || IS_ENARDEN_INVERTED || IS_ENBWREN_INVERTED
            || IS_RSTRAMARSTRAM_INVERTED || IS_RSTRAMB_INVERTED || IS_RSTREGARSTREG_INVERTED || IS_RSTREGB_INVERTED) begin
            $display("GLSIM-UNSUPPORTED RAMB36E1 %m: RAM_MODE=%0s DOA_REG=%0d DOB_REG=%0d RW_A=%0d WW_A=%0d RW_B=%0d WW_B=%0d",
                     RAM_MODE, DOA_REG, DOB_REG, READ_WIDTH_A, WRITE_WIDTH_A, READ_WIDTH_B, WRITE_WIDTH_B);
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
                if (we[(d >= 8) ? (i / 8) : 0]) begin
                    mem[idx * d + i] = di[i];
                    anywe = 1'b1;
                end
            for (i = 0; i < p; i = i + 1)
                if (we[i]) memp[idx * p + i] = dip[i];
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

    always @(posedge CLKARDCLK) if (WA != 0 && ENARDEN === 1'b1) begin
        ta = doa; tpa = dopa;
        port_access(DA, PA, LA, ADDRARDADDR, DIADI, DIPADIP, (WRITE_WIDTH_A != 0) ? WEA : 4'd0, MODE_A, ta, tpa);
        if (RSTRAMARSTRAM === 1'b1) begin ta = SRVAL_A; tpa = SRVAL_A >> 32; end
        doa <= ta; dopa <= tpa;
    end
    always @(posedge CLKBWRCLK) if (WB != 0 && ENBWREN === 1'b1) begin
        tb = dob; tpb = dopb;
        port_access(DB, PB, LB, ADDRBWRADDR, DIBDI, DIPBDIP, (WRITE_WIDTH_B != 0) ? WEBWE[3:0] : 4'd0, MODE_B, tb, tpb);
        if (RSTRAMB === 1'b1) begin tb = SRVAL_B; tpb = SRVAL_B >> 32; end
        dob <= tb; dopb <= tpb;
    end

    assign DOADO = doa;
    assign DOBDO = dob;
    assign DOPADOP = dopa;
    assign DOPBDOP = dopb;
    assign CASCADEOUTA = 1'b0;
    assign CASCADEOUTB = 1'b0;
    assign ECCPARITY = 8'd0;
    assign RDADDRECC = 9'd0;
    assign SBITERR = 1'b0;
    assign DBITERR = 1'b0;
endmodule
