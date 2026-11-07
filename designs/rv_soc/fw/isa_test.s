start:
    lui t6, 1
    li a0, 0x12345678
    sw a0, 0(t6)
    li a1, -5
    sw a1, 4(t6)
    add a2, a0, a1
    sw a2, 8(t6)
    sub a2, a0, a1
    sw a2, 12(t6)
    xor a2, a0, a1
    sw a2, 16(t6)
    or a2, a0, a1
    sw a2, 20(t6)
    and a2, a0, a1
    sw a2, 24(t6)
    slt a2, a1, a0
    sw a2, 28(t6)
    sltu a2, a1, a0
    sw a2, 32(t6)
    slli a2, a0, 4
    sw a2, 36(t6)
    srli a2, a1, 28
    sw a2, 40(t6)
    srai a2, a1, 1
    sw a2, 44(t6)
    li t0, 3
    sll a2, a0, t0
    sw a2, 48(t6)
    srl a2, a1, t0
    sw a2, 52(t6)
    sra a2, a1, t0
    sw a2, 56(t6)
    addi a2, a0, -0x678
    sw a2, 60(t6)
    xori a2, a0, 0xff
    sw a2, 64(t6)
    ori a2, a0, 7
    sw a2, 68(t6)
    andi a2, a0, 0xf0
    sw a2, 72(t6)
    slti a2, a1, -4
    sw a2, 76(t6)
    sltiu a2, a0, -1
    sw a2, 80(t6)
here:
    auipc a2, 0
    la a3, here
    sub a2, a2, a3
    sw a2, 84(t6)
    li t0, 0x80818283
    sw t0, 88(t6)
    lb a2, 88(t6)
    sw a2, 92(t6)
    lbu a2, 88(t6)
    sw a2, 96(t6)
    lh a2, 90(t6)
    sw a2, 100(t6)
    lhu a2, 90(t6)
    sw a2, 104(t6)
    sw zero, 108(t6)
    li t0, 0x55
    sb t0, 109(t6)
    sw zero, 112(t6)
    li t0, 0xbeef
    sh t0, 114(t6)
    li t1, 0
    beq a0, a0, b1
    ori t1, t1, 1
b1:
    bne a0, a0, b2
    ori t1, t1, 2
b2:
    blt a1, a0, b3
    ori t1, t1, 4
b3:
    bge a1, a0, b4
    ori t1, t1, 8
b4:
    bltu a0, a1, b5
    ori t1, t1, 16
b5:
    bgeu a0, a1, b6
    ori t1, t1, 32
b6:
    sw t1, 116(t6)
    li t2, 5
    li t3, 0
back:
    addi t3, t3, 1
    bne t3, t2, back
    sw t3, 120(t6)
    li a4, 0
    jal ra, func
after:
    sw a4, 124(t6)
    la a5, after
    sub a5, ra, a5
    sw a5, 128(t6)
    la t4, func2
    jalr s7, 0(t4)
after2:
    la a5, after2
    sub a5, s7, a5
    sw a5, 132(t6)
    custom0 a2, a0, a1, 0, 0
    sw a2, 136(t6)
    custom0 a2, a0, a1, 0x7f, 7
    sw a2, 140(t6)
    lui a2, 0xabcde
    sw a2, 144(t6)
    lui s0, 0x10000
    lw a2, 0x14(s0)
    sw a2, 148(t6)
    li a2, 0x600df00d
    sw a2, 252(t6)
halt:
    j halt
func:
    li a4, 0x77
    jalr zero, 0(ra)
func2:
    jalr zero, 0(s7)
