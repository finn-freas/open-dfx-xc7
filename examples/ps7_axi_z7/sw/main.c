#include <stdint.h>
#include "regs.h"

static inline uint32_t rd(uint32_t a)
{
    return *(volatile uint32_t *)a;
}

static inline void wr(uint32_t a, uint32_t v)
{
    *(volatile uint32_t *)a = v;
}

static void putch(char c)
{
    while (rd(UART1_BASE + UART_SR) & UART_SR_TXFULL)
        ;
    wr(UART1_BASE + UART_FIFO, (uint32_t)c);
}

static void puts_(const char *s)
{
    while (*s) {
        if (*s == '\n')
            putch('\r');
        putch(*s++);
    }
}

static void puthex(uint32_t v)
{
    static const char hex[] = "0123456789abcdef";
    puts_("0x");
    for (int i = 28; i >= 0; i -= 4)
        putch(hex[(v >> i) & 0xF]);
}

static void show(const char *name, uint32_t v)
{
    puts_(name);
    puts_(" = ");
    puthex(v);
    puts_("\n");
}

static int check(const char *name, uint32_t got, uint32_t want)
{
    puts_(name);
    puts_(": got ");
    puthex(got);
    puts_(" want ");
    puthex(want);
    puts_(got == want ? " ok\n" : " MISMATCH\n");
    return got == want ? 0 : 1;
}

void on_trap(uint32_t far, uint32_t fsr, uint32_t pc, uint32_t kind)
{
    static const char *const names[] = {"?", "undef", "swi", "prefetch abort", "data abort", "irq", "fiq"};
    puts_("ofx-app: TRAP ");
    puts_(names[kind < 7 ? kind : 0]);
    puts_(" pc=");
    puthex(pc);
    puts_(" far=");
    puthex(far);
    puts_(" fsr=");
    puthex(fsr);
    puts_("\n");
}

static void delay(uint32_t n)
{
    for (volatile uint32_t i = 0; i < n; i++)
        ;
}

int main(void)
{
    int fails = 0;

    puts_("\nofx-app: ps7_axi_z7 bare-metal test\n");
    show("FPGA0_CLK_CTRL", rd(FPGA0_CLK_CTRL));
    show("LVL_SHFTR_EN  ", rd(LVL_SHFTR_EN));
    show("FPGA_RST_CTRL ", rd(FPGA_RST_CTRL));
    show("DEVCFG_INT_STS", rd(DEVCFG_INT_STS));
    if (!(rd(DEVCFG_INT_STS) & PCFG_DONE)) {
        puts_("ofx-app: PL not configured (PCFG_DONE=0), not touching M_AXI_GP0\n");
        return 1;
    }
    wr(SLCR_UNLOCK, SLCR_UNLOCK_KEY);
    wr(LVL_SHFTR_EN, 0xF);
    wr(FPGA_RST_CTRL, 0);
    wr(SLCR_LOCK, SLCR_LOCK_KEY);

    fails += check("ID     ", rd(AXI_BASE + REG_ID), ID_VALUE);
    wr(AXI_BASE + REG_SCRATCH, SCRATCH_PATTERN);
    fails += check("SCRATCH", rd(AXI_BASE + REG_SCRATCH), SCRATCH_PATTERN);
    wr(AXI_BASE + REG_LED, LED_PATTERN);
    fails += check("LED    ", rd(AXI_BASE + REG_LED), LED_PATTERN);
    uint32_t c0 = rd(AXI_BASE + REG_COUNT);
    uint32_t c1 = rd(AXI_BASE + REG_COUNT);
    show("COUNT0 ", c0);
    show("COUNT1 ", c1);
    if (c1 == c0) {
        puts_("COUNT  : not running MISMATCH\n");
        fails++;
    }
    puts_(fails ? "ofx-app: FAIL\n" : "ofx-app: PASS\n");

    for (uint32_t i = 0;; i++) {
        wr(AXI_BASE + REG_LED, i);
        delay(2000000);
    }
}
