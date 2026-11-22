"""runs/ の結果を、施策ディレクトリの results/ に写して集計する。

uv run scripts/collect.py E0007
"""

import argparse
import json
import shutil
import subprocess
from pathlib import Path

COPIED = ("config.toml", "meta.json", "metrics.json", "per_problem.jsonl")


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
    )
    return Path(out.stdout.strip())


def collect(root: Path, exp_id: str) -> Path:
    """runs/ の該当する実行を results/<案>/s<seed>/ に写し、summary.md を書く。"""
    matches = sorted((root / "experiments").glob(f"{exp_id}-*"))
    if not matches:
        raise SystemExit(f"施策 {exp_id} のディレクトリが experiments/ にない。")
    results = matches[0] / "results"
    rows: list[str] = []
    for run_dir in sorted((root / "runs").glob(f"*-{exp_id}-*-s*")):
        meta_path = run_dir / "meta.json"
        if run_dir.parent.name == "dev" or not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text())
        target = results / str(meta["variant"]) / f"s{meta['seed']}"
        target.mkdir(parents=True, exist_ok=True)
        for name in COPIED:
            if (run_dir / name).exists():
                shutil.copy(run_dir / name, target / name)
        metrics: dict[str, object] = {}
        if (run_dir / "metrics.json").exists():
            metrics = json.loads((run_dir / "metrics.json").read_text())
        scalar = ", ".join(
            f"{k}={v}" for k, v in metrics.items() if isinstance(v, int | float | str)
        )
        rows.append(
            f"| {meta['variant']} | {meta['seed']} | {str(meta['commit'])[:7]} | {meta['dirty']} "
            f"| {meta['device']} | {meta['host']} | {meta['exit_code']} | {scalar} |"
        )
    header = (
        f"# {exp_id} の結果\n\n"
        "| 案 | seed | commit | dirty | device | host | 終了コード | 指標 |\n"
        "|---|---|---|---|---|---|---|---|\n"
    )
    results.mkdir(parents=True, exist_ok=True)
    summary = results / "summary.md"
    summary.write_text(header + "\n".join(rows) + ("\n" if rows else ""))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("experiment", help="施策 ID (E0007 など)")
    args = parser.parse_args(argv)
    summary = collect(repo_root(), args.experiment)
    print(f"集計: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
