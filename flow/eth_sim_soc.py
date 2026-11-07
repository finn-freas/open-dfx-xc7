import os

import litex.tools.litex_sim as ls

CONFIG = {
    "analyzers": ("analyzer",),
    "start_dir": os.getcwd(),
}


class Builder(ls.Builder):
    def build(self, **kwargs):
        cb = kwargs.get("pre_run_callback")

        def pre_run(vns):
            for name in CONFIG["analyzers"]:
                a = getattr(self.soc, name, None)
                if a is not None and a.csr_csv:
                    a.export_csv(vns, os.path.join(CONFIG["start_dir"], a.csr_csv))
            if cb:
                cb(vns)

        kwargs["pre_run_callback"] = pre_run
        return super().build(**kwargs)


if __name__ == "__main__":
    ls.Builder = Builder
    ls.main()
