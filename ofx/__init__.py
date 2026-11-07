from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FLOW = ROOT / "flow"
BOARDS = ROOT / "boards"
VERSION = (ROOT / "VERSION").read_text().strip() if (ROOT / "VERSION").exists() else "unknown"
