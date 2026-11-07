.equ IO_LED, 0x0
.equ IO_TX, 0x4
.equ IO_TXBUSY, 0x8
.equ IO_RX, 0xC
.equ IO_ICAPW, 0x10
.equ IO_SPICS, 0x20
.equ IO_SPIX, 0x24
.equ IO_SPIRX, 0x28
.equ IO_DECOUPLE, 0x2C
.equ SETTLE, 256
.equ FLASH_BASE, 0x400000
.equ SLOT_SHIFT, 16
.equ MAX_SLOTS, 16
.equ MAX_BYTES, 0xFFF0
.equ MAGIC, 0x50524631
start:
    lui s0, 0x10000
    sw zero, IO_SPICS(s0)
    sw zero, IO_SPIX(s0)
loop:
    jal ra, getc
    li t2, 'W'
    beq a0, t2, cmd_w
    li t2, 'C'
    beq a0, t2, cmd_c
    li t2, 'S'
    beq a0, t2, cmd_s
    li t2, 'A'
    beq a0, t2, cmd_a
    li t2, 'J'
    beq a0, t2, cmd_j
    li t2, 'R'
    beq a0, t2, cmd_r
    j loop
cmd_w:
    jal s1, getw
    mv s3, a1
    li t0, 1
    sw t0, IO_DECOUPLE(s0)
w_loop:
    beq s3, zero, w_done
    jal s1, getw
    sw a1, IO_ICAPW(s0)
    addi s3, s3, -1
    j w_loop
w_done:
    jal t5, recouple
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
    jal s1, putw
    j loop
cmd_s:
    jal ra, getc
    jal s9, load_slot
    jal ra, putc
    j loop
cmd_a:
    jal s1, getw
    mv s4, a1
    jal s1, getw
    mv s5, a1
    li s10, 0
a_loop:
    mv a0, s10
    jal s9, load_slot
    mv s11, a0
    jal ra, putc
    li t2, 'K'
    bne s11, t2, a_done
    custom0 s6, s4, s5, 0, 0
    sw s6, IO_LED(s0)
    jal s1, putw
    addi s10, s10, 1
    li t2, MAX_SLOTS
    bne s10, t2, a_loop
a_done:
    li a0, '.'
    jal ra, putc
    j loop
cmd_j:
    li t0, 1
    sw t0, IO_SPICS(s0)
    li t0, 0x9F000000
    sw t0, IO_SPIX(s0)
    sw zero, IO_SPICS(s0)
    lw s6, IO_SPIRX(s0)
    srli a0, s6, 16
    jal ra, putc
    srli a0, s6, 8
    jal ra, putc
    mv a0, s6
    jal ra, putc
    j loop
cmd_r:
    jal s1, getw
    mv a2, a1
    jal t6, flash_begin
    lw s6, IO_SPIX(s0)
    sw zero, IO_SPICS(s0)
    jal s1, putw
    j loop
load_slot:
    li t2, MAX_SLOTS
    bgeu a0, t2, ls_bad
    li s2, FLASH_BASE
    slli t0, a0, SLOT_SHIFT
    add s2, s2, t0
    mv a2, s2
    jal t6, flash_begin
    lw a5, IO_SPIX(s0)
    lw s3, IO_SPIX(s0)
    lw s7, IO_SPIX(s0)
    lw t0, IO_SPIX(s0)
    sw zero, IO_SPICS(s0)
    li t1, MAGIC
    bne a5, t1, ls_bad
    beq s3, zero, ls_bad
    li t1, MAX_BYTES
    bltu t1, s3, ls_bad
    andi t1, s3, 3
    bne t1, zero, ls_bad
    srli s8, s3, 2
    addi a2, s2, 16
    jal t6, flash_begin
    mv a3, s8
    li a4, 0
ls_sum:
    lw t0, IO_SPIX(s0)
    add a4, a4, t0
    addi a3, a3, -1
    bne a3, zero, ls_sum
    sw zero, IO_SPICS(s0)
    bne a4, s7, ls_sum_bad
    addi a2, s2, 16
    jal t6, flash_begin
    mv a3, s8
    li t0, 1
    sw t0, IO_DECOUPLE(s0)
ls_icap:
    lw t0, IO_SPIX(s0)
    sw t0, IO_ICAPW(s0)
    addi a3, a3, -1
    bne a3, zero, ls_icap
    sw zero, IO_SPICS(s0)
    jal t5, recouple
    li a0, 'K'
    jalr zero, 0(s9)
ls_sum_bad:
    li a0, 'X'
    jalr zero, 0(s9)
ls_bad:
    sw zero, IO_SPICS(s0)
    li a0, 'E'
    jalr zero, 0(s9)
recouple:
    li t4, SETTLE
recouple_wait:
    addi t4, t4, -1
    bne t4, zero, recouple_wait
    sw zero, IO_DECOUPLE(s0)
    jalr zero, 0(t5)
flash_begin:
    li t0, 1
    sw t0, IO_SPICS(s0)
    li t1, 0x03000000
    or t1, t1, a2
    sw t1, IO_SPIX(s0)
    jalr zero, 0(t6)
putw:
    srli a0, s6, 24
    jal ra, putc
    srli a0, s6, 16
    jal ra, putc
    srli a0, s6, 8
    jal ra, putc
    mv a0, s6
    jal ra, putc
    jalr zero, 0(s1)
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
