"""GitHub Releases に保管した学習済みモデルを runs/<run_id>/ に取り出し、sha256 を確かめる。

uv run scripts/fetch.py E0001 baseline --seed 0
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

from project_name.lab import gitstate
from project_name.lab.proposals import exp_dir, find
from project_name.lab.suite import sha256


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("experiment")
    ap.add_argument("variant")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--runs-dir", default="runs")
    args = ap.parse_args()

    root = gitstate.repo_root()
    exp = find(root, args.experiment)
    edir = exp_dir(root, exp)
    path = edir / "artifacts.toml"
    if not path.exists():
        print(f"{path.relative_to(root)} がない (まだ publish していない)", file=sys.stderr)
        return 1
    models = [
        m
        for m in tomllib.loads(path.read_text())["model"]
        if m["variant"] == args.variant and m["seed"] == args.seed
    ]
    if not models:
        print(f"{args.variant} seed {args.seed} は保管されていない", file=sys.stderr)
        return 1
    for m in models:
        dest = root / args.runs_dir / m["run_id"] / m["file"]
        if dest.exists() and sha256(dest) == m["sha256"]:
            print(f"既にある: {dest.relative_to(root)}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                ["gh", "release", "download", m["tag"], "--pattern", m["asset"], "--dir", tmp],
                cwd=root,
                check=True,
            )
            got = Path(tmp) / m["asset"]
            if sha256(got) != m["sha256"]:
                print(f"sha256 が合わない: {m['asset']}", file=sys.stderr)
                return 1
            shutil.move(got, dest)
        print(f"取り出した: {dest.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
