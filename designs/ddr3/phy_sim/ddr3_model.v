`timescale 1ps / 1ps

module ddr3_model #(
    parameter CL    = 6,
    parameter CWL   = 5,
    parameter TCK   = 2500,
    parameter LANES = 2
) (
    input                    ck_p,
    input                    ck_n,
    input                    cke,
    input                    cs_n,
    input                    ras_n,
    input                    cas_n,
    input                    we_n,
    input              [2:0] ba,
    input             [13:0] a,
    input        [LANES-1:0] dm,
    inout      [8*LANES-1:0] dq,
    inout        [LANES-1:0] dqs_p,
    inout        [LANES-1:0] dqs_n,
    input                    odt,
    input                    reset_n
);

    localparam DQ = 8 * LANES;

    reg [DQ-1:0] mem [0:(1 << 20) - 1];
    reg   [13:0] open_row [0:7];

    reg          rd_oe;
    reg          dqs_val;
    reg [DQ-1:0] dq_out;

    assign dq    = rd_oe ? dq_out : {DQ{1'bz}};
    assign dqs_p = rd_oe ? {LANES{dqs_val}} : {LANES{1'bz}};
    assign dqs_n = rd_oe ? {LANES{~dqs_val}} : {LANES{1'bz}};

    integer n_act, n_wr, n_rd, n_mrs, n_other;
    integer wr_cnt [0:LANES-1];
    time    wr_first [0:LANES-1];
    time    wr_t0;
    reg     wr_armed;
    integer wr_base;
    integer rd_base;
    time    rd_t0;
    integer i;

    function integer index(input [2:0] b, input [13:0] row, input [9:0] col);
        index = {b, row[6:0], col[9:3], 3'b000};
    endfunction

    integer rd_extra;

    initial begin
        if (!$value$plusargs("RD_EXTRA=%d", rd_extra))
            rd_extra = 0;
        $display("[ddr3_model] CL %0d CWL %0d tCK %0d ps, extra read delay %0d ps", CL, CWL, TCK, rd_extra);
        rd_oe = 0; dqs_val = 0; dq_out = 0; wr_armed = 0;
        n_act = 0; n_wr = 0; n_rd = 0; n_mrs = 0; n_other = 0;
        for (i = 0; i < 8; i = i + 1) open_row[i] = 0;
        for (i = 0; i < LANES; i = i + 1) wr_cnt[i] = 8;
    end

    always @(posedge ck_p) begin
        if (reset_n === 1'b1 && cke === 1'b1 && cs_n === 1'b0) begin
            case ({ras_n, cas_n, we_n})
                3'b011: begin
                    open_row[ba] <= a;
                    n_act = n_act + 1;
                    if (n_act <= 3)
                        $display("[ddr3_model] ACT command sampled at %0t ps", $time);
                end
                3'b100: begin
                    wr_t0    = $time;
                    wr_base  = index(ba, open_row[ba], a[9:0]);
                    wr_armed = 1;
                    for (i = 0; i < LANES; i = i + 1) wr_cnt[i] = 0;
                    n_wr = n_wr + 1;
                    if (n_wr <= 2)
                        $display("[ddr3_model] WRITE command sampled at %0t ps", $time);
                end
                3'b101: begin
                    rd_t0   = $time;
                    rd_base = index(ba, open_row[ba], a[9:0]);
                    n_rd = n_rd + 1;
                    if (n_rd <= 3)
                        $display("[ddr3_model] READ command sampled at %0t ps; data beat 0 (DQS rising) at %0t ps", $time,
                                 $time + CL * TCK + rd_extra);
                    read_burst(rd_base);
                end
                3'b000: n_mrs = n_mrs + 1;
                default: n_other = n_other + 1;
            endcase
        end
    end

    task read_burst(input integer base);
        integer b;
        begin
            fork
                begin
                    #((CL - 1) * TCK + rd_extra);
                    dqs_val = 0;
                    rd_oe   = 1;
                    #(TCK);
                    for (b = 0; b < 8; b = b + 1) begin
                        dqs_val = ~b[0];
                        dq_out  = mem[base + b];
                        #(TCK / 2);
                    end
                    dqs_val = 0;
                    dq_out  = {DQ{1'bx}};
                    #(TCK / 2);
                    rd_oe = 0;
                end
            join_none
        end
    endtask

    genvar l;
    generate
        for (l = 0; l < LANES; l = l + 1) begin : lane
            always @(dqs_p[l]) begin
                if (wr_armed && (dqs_p[l] === 1'b1 || dqs_p[l] === 1'b0) && wr_cnt[l] < 8 &&
                    $time >= wr_t0 + CWL * TCK - TCK / 2 && $time <= wr_t0 + (CWL + 4) * TCK + TCK / 2) begin
                    if (wr_cnt[l] == 0)
                        wr_first[l] = $time - wr_t0;
                    if (dm[l] === 1'b0)
                        mem[wr_base + wr_cnt[l]][8 * l +: 8] = dq[8 * l +: 8];
                    else if (dm[l] !== 1'b1)
                        $display("[ddr3_model] %t lane %0d beat %0d: DM is %b", $time, l, wr_cnt[l], dm[l]);
                    wr_cnt[l] = wr_cnt[l] + 1;
                end
            end
        end
    endgenerate
endmodule
