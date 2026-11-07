ENTRY(_start)

MEMORY
{
    ddr (rwx) : ORIGIN = 0x04000000, LENGTH = 0x00100000
}

SECTIONS
{
    .text : {
        KEEP(*(.vectors))
        *(.text*)
        *(.rodata*)
    } > ddr
    .data : ALIGN(4) {
        *(.data*)
    } > ddr
    .bss (NOLOAD) : ALIGN(4) {
        _bss_start = .;
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _bss_end = .;
    } > ddr
    .stack (NOLOAD) : ALIGN(16) {
        . += 0x1000;
        _abt_stack_top = .;
        . += 0x4000;
        _stack_top = .;
    } > ddr
    /DISCARD/ : { *(.ARM.exidx*) *(.comment) }
}
