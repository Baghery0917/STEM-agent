"""Shrink bundle media for git: longest side 1000px, JPEG quality 70. Uses macOS sips. Output: clean/bundle_media_small/"""
import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "clean/bundle/media"
DST = ROOT / "clean/bundle_media_small"


def one(p: Path):
    rel = p.relative_to(SRC)
    out = DST / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        return
    if p.suffix.lower() in (".jpg", ".jpeg", ".png"):
        r = subprocess.run(["sips", "-Z", "1000", "--setProperty", "formatOptions", "70", str(p), "--out", str(out)], capture_output=True)
        if r.returncode == 0 and out.exists():
            return
    out.write_bytes(p.read_bytes())


files = [p for p in SRC.rglob("*") if p.is_file()]
with ThreadPoolExecutor(8) as ex:
    list(ex.map(one, files))
tot = sum(p.stat().st_size for p in DST.rglob("*") if p.is_file())
print(f"{len(files)} files -> {tot/1e6:.1f} MB")
