module rm_bridge_fenced #(parameter TIMEOUT = 64, parameter FENCE = 64) (
    input wire clk, input wire resetn,
    input wire pcpi_valid, input wire [31:0] pcpi_insn, input wire [31:0] pcpi_rs1, input wire [31:0] pcpi_rs2,
    output reg pcpi_wr = 1'b0, output reg [31:0] pcpi_rd = 32'd0, output wire pcpi_wait, output reg pcpi_ready = 1'b0,
    output reg slot_valid = 1'b0, output reg [9:0] slot_funct = 10'd0,
    output reg [31:0] slot_rs1 = 32'd0, output reg [31:0] slot_rs2 = 32'd0,
    input wire [31:0] slot_rd, input wire slot_ready,
    output reg [15:0] timeouts = 16'd0, output reg [15:0] late_answers = 16'd0
);
    localparam S_IDLE = 2'd0, S_BUSY = 2'd1, S_DONE = 2'd2;
    wire is_custom0 = pcpi_valid && pcpi_insn[6:0] == 7'b0001011;
    assign pcpi_wait = is_custom0;
    reg [1:0] state = S_IDLE;
    reg [7:0] cnt = 8'd0;
    reg ready_q = 1'b0;
    reg armed = 1'b0;
    reg [7:0] quiet = 8'd0;
    wire quiet_ok = quiet >= FENCE;
    wire ready_rise = slot_ready && !ready_q;
    always @(posedge clk) begin
        slot_valid <= 1'b0;
        pcpi_ready <= 1'b0;
        pcpi_wr <= 1'b0;
        ready_q <= slot_ready;
        if (slot_ready) quiet <= 8'd0;
        else if (!quiet_ok) quiet <= quiet + 8'd1;
        if (ready_rise && state != S_BUSY) late_answers <= late_answers + 16'd1;
        if (!resetn) begin
            state <= S_IDLE;
            armed <= 1'b0;
            cnt <= 8'd0;
        end else case (state)
            S_IDLE: begin
                if (slot_ready) armed <= 1'b1;
                if (!is_custom0) begin
                    cnt <= 8'd0;
                end else if (!slot_ready && (!armed || quiet_ok)) begin
                    armed <= 1'b0;
                    slot_valid <= 1'b1;
                    slot_funct <= {pcpi_insn[31:25], pcpi_insn[14:12]};
                    slot_rs1 <= pcpi_rs1;
                    slot_rs2 <= pcpi_rs2;
                    cnt <= 8'd0;
                    state <= S_BUSY;
                end else if (cnt == TIMEOUT + FENCE - 1) begin
                    pcpi_rd <= 32'd0;
                    pcpi_wr <= 1'b1;
                    pcpi_ready <= 1'b1;
                    timeouts <= timeouts + 16'd1;
                    cnt <= 8'd0;
                    state <= S_DONE;
                end else begin
                    cnt <= cnt + 8'd1;
                end
            end
            S_BUSY: begin
                cnt <= cnt + 8'd1;
                if (!slot_valid && ready_rise) begin
                    pcpi_rd <= slot_rd;
                    pcpi_wr <= 1'b1;
                    pcpi_ready <= 1'b1;
                    state <= S_DONE;
                end else if (cnt == TIMEOUT - 1) begin
                    pcpi_rd <= 32'd0;
                    pcpi_wr <= 1'b1;
                    pcpi_ready <= 1'b1;
                    timeouts <= timeouts + 16'd1;
                    armed <= 1'b1;
                    quiet <= 8'd0;
                    state <= S_DONE;
                end
            end
            default: begin
                cnt <= 8'd0;
                state <= S_IDLE;
            end
        endcase
    end
endmodule
