    .syntax unified
    .arm

    .section .vectors, "ax"
    .global _vectors
    .balign 32
_vectors:
    ldr pc, =_start
    ldr pc, =trap_undef
    ldr pc, =trap_swi
    ldr pc, =trap_pabt
    ldr pc, =trap_dabt
    nop
    ldr pc, =trap_irq
    ldr pc, =trap_fiq
    .ltorg

    .text
    .global _start
_start:
    cpsid if
    ldr r0, =_vectors
    mcr p15, 0, r0, c12, c0, 0
    mrc p15, 0, r0, c1, c0, 0
    bic r0, r0, #(1 << 13)
    mcr p15, 0, r0, c1, c0, 0
    isb
    cps #0x17
    ldr sp, =_abt_stack_top
    cps #0x1b
    ldr sp, =_abt_stack_top
    cps #0x13
    ldr sp, =_stack_top
    ldr r0, =_bss_start
    ldr r1, =_bss_end
    mov r2, #0
1:  cmp r0, r1
    strlo r2, [r0], #4
    blo 1b
    bl main
2:  wfe
    b 2b

trap_undef:
    mov r3, #1
    sub r2, lr, #4
    b trap_common
trap_swi:
    mov r3, #2
    sub r2, lr, #4
    b trap_common
trap_pabt:
    mov r3, #3
    sub r2, lr, #4
    mrc p15, 0, r0, c6, c0, 2
    mrc p15, 0, r1, c5, c0, 1
    b trap_report
trap_dabt:
    mov r3, #4
    sub r2, lr, #8
    mrc p15, 0, r0, c6, c0, 0
    mrc p15, 0, r1, c5, c0, 0
    b trap_report
trap_irq:
    mov r3, #5
    sub r2, lr, #4
    b trap_common
trap_fiq:
    mov r3, #6
    sub r2, lr, #4
trap_common:
    mov r0, #0
    mov r1, #0
trap_report:
    ldr sp, =_abt_stack_top
    bl on_trap
3:  wfe
    b 3b
    .ltorg
