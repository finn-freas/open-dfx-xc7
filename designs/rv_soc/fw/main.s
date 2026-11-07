.equ IO_LED, 0x0
.equ IO_TX, 0x4
.equ IO_TXBUSY, 0x8
.equ IO_RX, 0xC
.equ IO_ICAPW, 0x10
start:
    lui s0, 0x10000
loop:
    jal ra, getc
    li t2, 'W'
    beq a0, t2, cmd_w
    li t2, 'C'
    beq a0, t2, cmd_c
    j loop
cmd_w:
    jal s1, getw
    mv s3, a1
w_loop:
    beq s3, zero, w_done
    jal s1, getw
    sw a1, IO_ICAPW(s0)
    addi s3, s3, -1
    j w_loop
w_done:
    li a0, 'K'
    jal ra, putc
    j loop
cmd_c:
    jal s1, getw
    mv s4, a1
    jal s1, getw
    mv s5, a1
    custom0 s6, s4, s5, 0, 0
    sw s6, IO_LED(s0)
    srli a0, s6, 24
    jal ra, putc
    srli a0, s6, 16
    jal ra, putc
    srli a0, s6, 8
    jal ra, putc
    mv a0, s6
    jal ra, putc
    j loop
getc:
    lw t0, IO_RX(s0)
    andi t1, t0, 256
    beq t1, zero, getc
    andi a0, t0, 255
    jalr zero, 0(ra)
putc:
    lw t0, IO_TXBUSY(s0)
    andi t0, t0, 1
    bne t0, zero, putc
    sw a0, IO_TX(s0)
    jalr zero, 0(ra)
getw:
    li a1, 0
    li t3, 4
getw_loop:
    jal ra, getc
    slli a1, a1, 8
    or a1, a1, a0
    addi t3, t3, -1
    bne t3, zero, getw_loop
    jalr zero, 0(s1)
