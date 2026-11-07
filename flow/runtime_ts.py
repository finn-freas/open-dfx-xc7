import sys
import time

t0 = float(sys.argv[2]) if len(sys.argv) > 2 else time.time()
out = sys.stdout.buffer
with open(sys.argv[1], "w") as ts:
    for raw in sys.stdin.buffer:
        out.write(raw)
        out.flush()
        ts.write(f"{time.time() - t0:.3f}\t{raw.decode('utf-8', 'replace').rstrip()}\n")
