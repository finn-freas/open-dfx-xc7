"""SA study: the SA's timing model (its TimingAnalyser on the Vivado-fitted arc model, stub chipdb cell delays)
against Vivado's timer on the same placement (exact import). Model endpoint slacks come from `-o sa-refine=...:dump=FILE`
(build/sa/dump/<design>_<variant>_s<seed>/endpoints.txt, flow/sa_dumprun.py); Vivado's from paths_noicap.txt (200
worst non-ICAP paths, one per endpoint). Prints, per run: matched endpoints, Vivado - model slack (mean, sd),
Pearson r, how many of the model's 50 worst endpoints are among Vivado's 200 worst, and the model slack at Vivado's
worst endpoint.
usage: sa_endpoints.py DESIGN VARIANT SEED..."""
import statistics, sys
from pathlib import Path

R = Path.home() / "open-dfx-xc7"
V = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build")
PORT = {"R": "SR", "S": "SR", "CLR": "SR", "PRE": "SR"}


def main():
    d, v = sys.argv[1], sys.argv[2]
    for s in sys.argv[3:]:
        name = f"{d}_p5_{v}_s{s}_exact"
        out = V / "exact_sa" / name
        if not (out / "status.txt").exists():
            out = V / "exact" / name
        dump = R / "build/sa/dump" / f"{d}_{v}_s{s}" / "endpoints.txt"
        if not (out / "paths_noicap.txt").exists() or not dump.exists():
            print(f"{name}: missing {'Vivado run' if not (out / 'paths_noicap.txt').exists() else 'dump'}")
            continue
        model = {}
        for ln in dump.read_text().splitlines():
            c, p, sl = ln.split("\t")
            model[(c, p)] = int(sl) / 1000.0
        viv = []
        for ln in (out / "paths_noicap.txt").read_text().splitlines():
            f = ln.split("\t")
            ep = f[3].split()[-1]
            c, p = ep.rsplit("/", 1)
            p = PORT.get(p, p)
            viv.append((c, p, float(f[0])))
        pairs = [(model[(c, p)], vs) for c, p, vs in viv if (c, p) in model]
        if len(pairs) < 3:
            print(f"{name}: {len(pairs)} matched endpoints")
            continue
        ms, vs = zip(*pairs)
        diff = [b - a for a, b in pairs]
        r = statistics.correlation(ms, vs)
        worst_model = sorted(model.items(), key=lambda kv: kv[1])[:50]
        vset = {(c, p) for c, p, _ in viv}
        hit = sum(1 for k, _ in worst_model if k in vset)
        print(f"{name}: {len(pairs)}/{len(viv)} matched; Vivado - model slack mean {statistics.mean(diff):+.3f} ns "
              f"(sd {statistics.pstdev(diff):.3f}); r {r:.2f}; model worst {worst_model[0][1]:.3f} ns, Vivado worst "
              f"{viv[0][2]:.3f} ns (model there {pairs[0][0] if (viv[0][0], viv[0][1]) in model else float('nan'):.3f}); "
              f"model's 50 worst endpoints among Vivado's 200 worst: {hit}")


if __name__ == "__main__":
    main()
