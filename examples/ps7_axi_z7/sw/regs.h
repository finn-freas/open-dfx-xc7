#ifndef PS7_AXI_Z7_REGS_H
#define PS7_AXI_Z7_REGS_H

#define AXI_BASE        0x40000000u
#define REG_LED         0x00u
#define REG_SCRATCH     0x04u
#define REG_COUNT       0x08u
#define REG_ID          0x0Cu
#define ID_VALUE        0x0F5A7020u

#define UART1_BASE      0xE0001000u
#define UART_SR         0x2Cu
#define UART_FIFO       0x30u
#define UART_SR_TXFULL  (1u << 4)

#define SLCR_LOCK       0xF8000004u
#define SLCR_UNLOCK     0xF8000008u
#define SLCR_LOCK_KEY   0x767Bu
#define SLCR_UNLOCK_KEY 0xDF0Du
#define FPGA0_CLK_CTRL  0xF8000170u
#define FPGA_RST_CTRL   0xF8000240u
#define LVL_SHFTR_EN    0xF8000900u
#define DEVCFG_INT_STS  0xF800700Cu
#define PCFG_DONE       (1u << 2)

#define SCRATCH_PATTERN 0xA5C3F00Fu
#define LED_PATTERN     0x0000000Au

#endif
