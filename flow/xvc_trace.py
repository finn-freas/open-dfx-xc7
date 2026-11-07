import argparse
import json
import socket
import struct
from pathlib import Path

CONFIG = {
    "host": "127.0.0.1",
    "port": 2542,
    "max_vector": 32768,
    "idcode": 0x0362D093,
    "ir_len": 6,
    "ir_capture": 0b110101,
    "ir_names": {0x02: "USER1", 0x03: "USER2", 0x04: "CFG_OUT", 0x05: "CFG_IN", 0x08: "USERCODE", 0x09: "IDCODE",
                 0x0B: "JPROGRAM", 0x0C: "JSTART", 0x0D: "JSHUTDOWN", 0x10: "ISC_ENABLE", 0x11: "ISC_PROGRAM",
                 0x14: "ISC_NOOP", 0x16: "ISC_DISABLE", 0x1F: "STATUS", 0x3F: "BYPASS"},
}

NEXT = {
    "TLR": ("RTI", "TLR"), "RTI": ("RTI", "SELDR"),
    "SELDR": ("CAPDR", "SELIR"), "CAPDR": ("SHDR", "EX1DR"), "SHDR": ("SHDR", "EX1DR"), "EX1DR": ("PADR", "UPDR"),
    "PADR": ("PADR", "EX2DR"), "EX2DR": ("SHDR", "UPDR"), "UPDR": ("RTI", "SELDR"),
    "SELIR": ("CAPIR", "TLR"), "CAPIR": ("SHIR", "EX1IR"), "SHIR": ("SHIR", "EX1IR"), "EX1IR": ("PAIR", "UPIR"),
    "PAIR": ("PAIR", "EX2IR"), "EX2IR": ("SHIR", "UPIR"), "UPIR": ("RTI", "SELDR"),
}


class Tap:
    def __init__(self, log):
        self.state = "TLR"
        self.ir = 0x09
        self.ir_sh = 0
        self.dr_sh = 0
        self.dr_len = 1
        self.dr_bits = 0
        self.cfg = bytearray()
        self.cfg_acc = 0
        self.cfg_n = 0
        self.rti = 0
        self.log = log
        self.event("TLR")

    def name(self):
        return CONFIG["ir_names"].get(self.ir, f"IR_0x{self.ir:02X}")

    def event(self, e):
        if self.log and self.log[-1][0] == e:
            self.log[-1][1] += 1
        else:
            self.log.append([e, 1])

    def flush_rti(self):
        if self.rti:
            self.log.append([f"RTI {self.rti} TCK", 1])
            self.rti = 0

    def capture_dr(self):
        self.dr_bits = 0
        if self.ir == 0x09:
            self.dr_sh, self.dr_len = CONFIG["idcode"], 32
        else:
            self.dr_sh, self.dr_len = 0, 1

    def step(self, tms, tdi):
        st = self.state
        tdo = 0
        if st == "SHIR":
            tdo = self.ir_sh & 1
            self.ir_sh = (self.ir_sh >> 1) | (tdi << (CONFIG["ir_len"] - 1))
        elif st == "SHDR":
            tdo = self.dr_sh & 1
            self.dr_sh = (self.dr_sh >> 1) | (tdi << (self.dr_len - 1))
            self.dr_bits += 1
            if self.ir == 0x05:
                self.cfg_acc |= tdi << self.cfg_n
                self.cfg_n += 1
                if self.cfg_n == 8:
                    self.cfg.append(self.cfg_acc)
                    self.cfg_acc = self.cfg_n = 0
        elif st == "RTI":
            self.rti += 1
        nxt = NEXT[st][tms]
        if nxt != "RTI":
            self.flush_rti()
        if nxt == "TLR" and st != "TLR":
            self.ir = 0x09
            self.event("TLR")
        elif nxt == "CAPIR":
            self.ir_sh = CONFIG["ir_capture"]
        elif nxt == "UPIR":
            self.ir = self.ir_sh & ((1 << CONFIG["ir_len"]) - 1)
            self.event(f"IR {self.name()}")
        elif nxt == "CAPDR":
            self.capture_dr()
        elif nxt == "UPDR":
            self.event(f"DR {self.name()} {self.dr_bits} bits")
        self.state = nxt
        return tdo

    def shift_bytes(self, n, tms, tdi):
        out = bytearray((n + 7) // 8)
        i = 0
        while i < n:
            if self.state == "SHDR" and self.ir == 0x05 and i % 8 == 0 and i + 8 < n and tms[i // 8] == 0 and self.cfg_n == 0:
                self.cfg.append(tdi[i // 8])
                self.dr_bits += 8
                i += 8
                continue
            b = self.step((tms[i // 8] >> (i % 8)) & 1, (tdi[i // 8] >> (i % 8)) & 1)
            out[i // 8] |= b << (i % 8)
            i += 1
        return bytes(out)


def recv_exact(c, n):
    buf = bytearray()
    while len(buf) < n:
        d = c.recv(n - len(buf))
        if not d:
            raise ConnectionError
        buf += d
    return bytes(buf)


def recv_cmd(c):
    buf = b""
    while not buf.endswith(b":"):
        d = c.recv(1)
        if not d:
            raise ConnectionError
        buf += d
    return buf.decode()


def main():
    ap = argparse.ArgumentParser(description="XVC server with a simulated 7-series TAP (xc7a35t IDCODE): logs the JTAG "
                                             "instruction sequence a client sends and keeps the CFG_IN data. No hardware.")
    ap.add_argument("log_json")
    ap.add_argument("--cfg-out", help="write the bytes shifted in under CFG_IN here")
    ap.add_argument("--port", type=int, default=CONFIG["port"])
    a = ap.parse_args()
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((CONFIG["host"], a.port))
    s.listen(1)
    print(f"listening on {CONFIG['host']}:{a.port}", flush=True)
    c, _ = s.accept()
    log = []
    tap = Tap(log)
    try:
        while True:
            cmd = recv_cmd(c)
            if cmd == "getinfo:":
                c.sendall(f"xvcServer_v1.0:{CONFIG['max_vector']}\n".encode())
            elif cmd == "settck:":
                c.sendall(recv_exact(c, 4))
            elif cmd == "shift:":
                n = struct.unpack("<I", recv_exact(c, 4))[0]
                nb = (n + 7) // 8
                tms = recv_exact(c, nb)
                tdi = recv_exact(c, nb)
                c.sendall(tap.shift_bytes(n, tms, tdi))
            else:
                raise ValueError(cmd)
    except ConnectionError:
        pass
    tap.flush_rti()
    c.close()
    s.close()
    instr = [e for e, _ in log if e.startswith("IR ")]
    res = {"sequence": log, "ir_sequence": instr, "cfg_in_bytes": len(tap.cfg),
           "jprogram": "IR JPROGRAM" in instr, "jstart": "IR JSTART" in instr}
    Path(a.log_json).write_text(json.dumps(res, indent=1))
    if a.cfg_out:
        Path(a.cfg_out).write_bytes(bytes(tap.cfg))
    for e, k in log:
        print(f"{e}" + (f" x{k}" if k > 1 else ""))
    print(f"CFG_IN bytes: {len(tap.cfg)}; JPROGRAM sent: {res['jprogram']}; JSTART sent: {res['jstart']}")


if __name__ == "__main__":
    main()
