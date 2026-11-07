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
    parameter RAM_EXTENSION_A = "NONE";
    parameter RAM_EXTENSION_B = "NONE";
    parameter RAM_MODE = "TDP";
    parameter integer READ_WIDTH_A = 0;
    parameter integer READ_WIDTH_B = 0;
    parameter SRVAL_A = 36'h0;
    parameter SRVAL_B = 36'h0;
    parameter WRITE_MODE_A = "WRITE_FIRST";
    parameter WRITE_MODE_B = "WRITE_FIRST";
    parameter integer WRITE_WIDTH_A = 0;
    parameter integer WRITE_WIDTH_B = 0;
    parameter RDADDR_COLLISION_HWCONFIG = "DELAYED_WRITE";
    parameter RSTREG_PRIORITY_A = "RSTREG";
    parameter RSTREG_PRIORITY_B = "RSTREG";
    parameter SIM_COLLISION_CHECK = "ALL";
    parameter SIM_DEVICE = "7SERIES";
    parameter INIT_FILE = "NONE";
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

    B2N_RAMB36E1_CORE #(
        .DOA_REG(DOA_REG), .DOB_REG(DOB_REG), .EN_ECC_READ(EN_ECC_READ), .EN_ECC_WRITE(EN_ECC_WRITE),
        .INIT_A(INIT_A), .INIT_B(INIT_B), .RAM_EXTENSION_A(RAM_EXTENSION_A), .RAM_EXTENSION_B(RAM_EXTENSION_B),
        .RAM_MODE(RAM_MODE), .READ_WIDTH_A(READ_WIDTH_A), .READ_WIDTH_B(READ_WIDTH_B),
        .SRVAL_A(SRVAL_A), .SRVAL_B(SRVAL_B), .WRITE_MODE_A(WRITE_MODE_A), .WRITE_MODE_B(WRITE_MODE_B),
        .WRITE_WIDTH_A(WRITE_WIDTH_A), .WRITE_WIDTH_B(WRITE_WIDTH_B),
        .INIT_00(INIT_00),
        .INIT_01(INIT_01),
        .INIT_02(INIT_02),
        .INIT_03(INIT_03),
        .INIT_04(INIT_04),
        .INIT_05(INIT_05),
        .INIT_06(INIT_06),
        .INIT_07(INIT_07),
        .INIT_08(INIT_08),
        .INIT_09(INIT_09),
        .INIT_0A(INIT_0A),
        .INIT_0B(INIT_0B),
        .INIT_0C(INIT_0C),
        .INIT_0D(INIT_0D),
        .INIT_0E(INIT_0E),
        .INIT_0F(INIT_0F),
        .INIT_10(INIT_10),
        .INIT_11(INIT_11),
        .INIT_12(INIT_12),
        .INIT_13(INIT_13),
        .INIT_14(INIT_14),
        .INIT_15(INIT_15),
        .INIT_16(INIT_16),
        .INIT_17(INIT_17),
        .INIT_18(INIT_18),
        .INIT_19(INIT_19),
        .INIT_1A(INIT_1A),
        .INIT_1B(INIT_1B),
        .INIT_1C(INIT_1C),
        .INIT_1D(INIT_1D),
        .INIT_1E(INIT_1E),
        .INIT_1F(INIT_1F),
        .INIT_20(INIT_20),
        .INIT_21(INIT_21),
        .INIT_22(INIT_22),
        .INIT_23(INIT_23),
        .INIT_24(INIT_24),
        .INIT_25(INIT_25),
        .INIT_26(INIT_26),
        .INIT_27(INIT_27),
        .INIT_28(INIT_28),
        .INIT_29(INIT_29),
        .INIT_2A(INIT_2A),
        .INIT_2B(INIT_2B),
        .INIT_2C(INIT_2C),
        .INIT_2D(INIT_2D),
        .INIT_2E(INIT_2E),
        .INIT_2F(INIT_2F),
        .INIT_30(INIT_30),
        .INIT_31(INIT_31),
        .INIT_32(INIT_32),
        .INIT_33(INIT_33),
        .INIT_34(INIT_34),
        .INIT_35(INIT_35),
        .INIT_36(INIT_36),
        .INIT_37(INIT_37),
        .INIT_38(INIT_38),
        .INIT_39(INIT_39),
        .INIT_3A(INIT_3A),
        .INIT_3B(INIT_3B),
        .INIT_3C(INIT_3C),
        .INIT_3D(INIT_3D),
        .INIT_3E(INIT_3E),
        .INIT_3F(INIT_3F),
        .INIT_40(INIT_40),
        .INIT_41(INIT_41),
        .INIT_42(INIT_42),
        .INIT_43(INIT_43),
        .INIT_44(INIT_44),
        .INIT_45(INIT_45),
        .INIT_46(INIT_46),
        .INIT_47(INIT_47),
        .INIT_48(INIT_48),
        .INIT_49(INIT_49),
        .INIT_4A(INIT_4A),
        .INIT_4B(INIT_4B),
        .INIT_4C(INIT_4C),
        .INIT_4D(INIT_4D),
        .INIT_4E(INIT_4E),
        .INIT_4F(INIT_4F),
        .INIT_50(INIT_50),
        .INIT_51(INIT_51),
        .INIT_52(INIT_52),
        .INIT_53(INIT_53),
        .INIT_54(INIT_54),
        .INIT_55(INIT_55),
        .INIT_56(INIT_56),
        .INIT_57(INIT_57),
        .INIT_58(INIT_58),
        .INIT_59(INIT_59),
        .INIT_5A(INIT_5A),
        .INIT_5B(INIT_5B),
        .INIT_5C(INIT_5C),
        .INIT_5D(INIT_5D),
        .INIT_5E(INIT_5E),
        .INIT_5F(INIT_5F),
        .INIT_60(INIT_60),
        .INIT_61(INIT_61),
        .INIT_62(INIT_62),
        .INIT_63(INIT_63),
        .INIT_64(INIT_64),
        .INIT_65(INIT_65),
        .INIT_66(INIT_66),
        .INIT_67(INIT_67),
        .INIT_68(INIT_68),
        .INIT_69(INIT_69),
        .INIT_6A(INIT_6A),
        .INIT_6B(INIT_6B),
        .INIT_6C(INIT_6C),
        .INIT_6D(INIT_6D),
        .INIT_6E(INIT_6E),
        .INIT_6F(INIT_6F),
        .INIT_70(INIT_70),
        .INIT_71(INIT_71),
        .INIT_72(INIT_72),
        .INIT_73(INIT_73),
        .INIT_74(INIT_74),
        .INIT_75(INIT_75),
        .INIT_76(INIT_76),
        .INIT_77(INIT_77),
        .INIT_78(INIT_78),
        .INIT_79(INIT_79),
        .INIT_7A(INIT_7A),
        .INIT_7B(INIT_7B),
        .INIT_7C(INIT_7C),
        .INIT_7D(INIT_7D),
        .INIT_7E(INIT_7E),
        .INIT_7F(INIT_7F),
        .INITP_00(INITP_00),
        .INITP_01(INITP_01),
        .INITP_02(INITP_02),
        .INITP_03(INITP_03),
        .INITP_04(INITP_04),
        .INITP_05(INITP_05),
        .INITP_06(INITP_06),
        .INITP_07(INITP_07),
        .INITP_08(INITP_08),
        .INITP_09(INITP_09),
        .INITP_0A(INITP_0A),
        .INITP_0B(INITP_0B),
        .INITP_0C(INITP_0C),
        .INITP_0D(INITP_0D),
        .INITP_0E(INITP_0E),
        .INITP_0F(INITP_0F)
    ) core (
        .CASCADEOUTA(CASCADEOUTA), .CASCADEOUTB(CASCADEOUTB),
        .DOADO(DOADO), .DOBDO(DOBDO), .DOPADOP(DOPADOP), .DOPBDOP(DOPBDOP),
        .ECCPARITY(ECCPARITY), .RDADDRECC(RDADDRECC), .SBITERR(SBITERR), .DBITERR(DBITERR),
        .ENARDEN(ENARDEN ^ (IS_ENARDEN_INVERTED != 0)), .CLKARDCLK(CLKARDCLK ^ (IS_CLKARDCLK_INVERTED != 0)),
        .RSTRAMARSTRAM(RSTRAMARSTRAM ^ (IS_RSTRAMARSTRAM_INVERTED != 0)), .RSTREGARSTREG(RSTREGARSTREG ^ (IS_RSTREGARSTREG_INVERTED != 0)),
        .CASCADEINA(CASCADEINA), .REGCEAREGCE(REGCEAREGCE),
        .ENBWREN(ENBWREN ^ (IS_ENBWREN_INVERTED != 0)), .CLKBWRCLK(CLKBWRCLK ^ (IS_CLKBWRCLK_INVERTED != 0)),
        .RSTRAMB(RSTRAMB ^ (IS_RSTRAMB_INVERTED != 0)), .RSTREGB(RSTREGB ^ (IS_RSTREGB_INVERTED != 0)),
        .CASCADEINB(CASCADEINB), .REGCEB(REGCEB),
        .INJECTDBITERR(INJECTDBITERR), .INJECTSBITERR(INJECTSBITERR),
        .ADDRARDADDR(ADDRARDADDR), .ADDRBWRADDR(ADDRBWRADDR),
        .DIADI(DIADI), .DIBDI(DIBDI), .DIPADIP(DIPADIP), .DIPBDIP(DIPBDIP),
        .WEA(WEA), .WEBWE(WEBWE)
    );
endmodule
