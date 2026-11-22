"""施策の run の結果を experiments/Exxxx-*/results/ に写し、summary.md を作る。

(案, seed) ごとに、終わった run のうち最も新しいものを使う。モデルのファイルは写さない
(publish.py で GitHub Releases に保管する)。

  uv run scripts/collect.py E0001
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from project_name.lab import gitstate
from project_name.lab.proposals import exp_dir, find
from project_name.lab.runs import find_runs, latest_by_variant_seed
from project_name.lab.stats import bootstrap_rate

COPY_FILES = ("meta.json", "config.toml", "metrics.json", "per_sample.jsonl")

# 表で先に並べる指標 (あるものだけ、この順)。残りの数値の指標は名前順に後ろへ並べる
KEY_METRICS: tuple[str, ...] = ()


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("experiment", help="施策の ID (E0001 など)")
    ap.add_argument("--runs-dir", default="runs")
    args = ap.parse_args()

    root = gitstate.repo_root()
    results = exp_dir(root, find(root, args.experiment)) / "results"
    runs = latest_by_variant_seed(find_runs(root / args.runs_dir, args.experiment))
    if not runs:
        print(f"{args.experiment} の終わった run が {args.runs_dir}/ にない", file=sys.stderr)
        return 1

    for (variant, seed), r in sorted(runs.items()):
        dest = results / variant / f"s{seed}"
        dest.mkdir(parents=True, exist_ok=True)
        for name in COPY_FILES:
            if (r.dir / name).exists():
                shutil.copy2(r.dir / name, dest / name)
        print(f"写した: {variant} seed {seed} ← {r.run_id}")

    # 集計は results/ にあるもの全部から作る (別のマシンで写して push された結果も含める)
    rows = collected_rows(results)
    (results / "summary.md").write_text(summary(args.experiment, rows))
    print(f"書いた: {(results / 'summary.md').relative_to(root)}")
    return 0


def collected_rows(results: Path) -> list:
    """results/<案>/s<seed>/ を全部読む。戻り: (案, seed, meta, metrics, ok) の列"""
    rows = []
    for d in sorted(results.glob("*/s*")):
        if (
            not d.name[1:].isdigit()
            or not (d / "meta.json").exists()
            or not (d / "metrics.json").exists()
        ):
            continue
        meta = json.loads((d / "meta.json").read_text())
        metrics = json.loads((d / "metrics.json").read_text())
        rows.append(
            (d.parent.name, int(d.name[1:]), meta, metrics, _ok_flags(d / "per_sample.jsonl"))
        )
    return sorted(rows, key=lambda row: (row[0], row[1]))


def _ok_flags(path: Path) -> list[bool] | None:
    if not path.exists():
        return None
    flags = []
    for line in path.read_text().splitlines():
        rec = json.loads(line)
        if "ok" not in rec:
            return None
        flags.append(bool(rec["ok"]))
    return flags


def summary(exp_id: str, rows: list) -> str:
    present = {k for *_, m, _ in rows for k, v in m.items() if isinstance(v, int | float)}
    keys = [k for k in KEY_METRICS if k in present] + sorted(present - set(KEY_METRICS))
    head = ["案", "seed", "run_id", "commit", "マシン", "評価一式", "ok の割合 (95% 区間)", *keys]
    lines = [
        f"# {exp_id} の結果の集計",
        "",
        "`uv run scripts/collect.py` が作る (手で編集しない)。",
        "",
        "| " + " | ".join(head) + " |",
        "|" + "---|" * len(head),
    ]
    for variant, seed, meta, metrics, ok in rows:
        if ok:
            rate, lo, hi = bootstrap_rate(ok)
            s = f"{rate:.1%} ({lo:.1%}–{hi:.1%})"
        else:
            s = "—"
        suite = meta.get("suite") or {}
        suite_s = f"{suite['version']} ({suite['sha256'][:8]})" if suite else "—"
        vals = [_fmt(metrics.get(k)) for k in keys]
        lines.append(
            f"| {variant} | {seed} | {meta['run_id']} | {meta['commit'][:7]} | "
            f"{meta.get('machine', '')} | "
            f"{suite_s} | {s} | " + " | ".join(vals) + " |"
        )
    return "\n".join(lines) + "\n"


def _fmt(v: object) -> str:
    if v is None:
        return "—"
    return f"{v:.4g}" if isinstance(v, float) else str(v)


if __name__ == "__main__":
    sys.exit(main())
