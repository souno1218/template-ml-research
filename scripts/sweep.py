"""施策の sweep.toml に書いた案 × seed を、決めた本数ずつ同時に回す。

同じ commit で終わっている (案, seed) は飛ばすので、中断しても同じコマンドで続きから回せる。

  uv run scripts/sweep.py experiments/E0001-larger-lr/sweep.toml
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
import tomllib
from pathlib import Path

from project_name.lab import gitstate
from project_name.lab.proposals import STEM_RE
from project_name.lab.runs import find_runs


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("sweep", help="experiments/Exxxx-*/sweep.toml")
    ap.add_argument("--parallel", type=int, help="sweep.toml の parallel を上書きする")
    ap.add_argument("--dev", action="store_true", help="動作確認 (run.py --dev で回す)")
    ap.add_argument("--runs-dir", default="runs")
    args = ap.parse_args()

    root = gitstate.repo_root()
    sweep_path = Path(args.sweep).resolve()
    exp_dir = sweep_path.parent
    m = STEM_RE.match(exp_dir.name)
    if m is None:
        print(f"施策のディレクトリではない: {exp_dir}", file=sys.stderr)
        return 2
    exp_id = m.group(1)
    with open(sweep_path, "rb") as f:
        spec = tomllib.load(f)
    parallel = args.parallel or int(spec.get("parallel", 1))

    st = gitstate.state(root)
    if not args.dev:
        problems = gitstate.check_runnable(st)
        if problems:
            print("実行しません (docs/rules/running.md):", file=sys.stderr)
            for p in problems:
                print(f"  - {p}", file=sys.stderr)
            return 2

    done = set()
    if not args.dev:
        for r in find_runs(root / args.runs_dir, exp_id):
            if r.meta.get("commit") == st.commit:
                done.add((r.meta["variant"], int(r.meta["seed"])))

    jobs = []
    for v in spec["variants"]:
        cfg = exp_dir / "configs" / f"{v}.toml"
        if not cfg.exists():
            print(f"案 {v} の設定がない: {cfg}", file=sys.stderr)
            return 2
        for s in spec["seeds"]:
            if (v, int(s)) in done:
                print(f"飛ばす (この commit で終わっている): {v} seed {s}")
                continue
            jobs.append((v, int(s), cfg))

    out_dir = root / args.runs_dir / "_sweep"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"{exp_id}: {len(jobs)} 本を {parallel} 本ずつ回す (commit {st.short})")
    running: list[tuple[str, int, subprocess.Popen, Path]] = []
    failed = []
    while jobs or running:
        while jobs and len(running) < parallel:
            v, s, cfg = jobs.pop(0)
            out = out_dir / f"{time.strftime('%Y%m%d-%H%M%S')}-{exp_id}-{v}-s{s}.out"
            cmd = [
                sys.executable,
                str(Path(__file__).resolve().parent / "run.py"),
                "--config",
                str(cfg),
                "--experiment",
                exp_id,
                "--variant",
                v,
                "--seed",
                str(s),
                "--runs-dir",
                args.runs_dir,
            ] + (["--dev"] if args.dev else [])
            with open(out, "w") as fh:  # 子プロセスが複製を持つので、親側はすぐ閉じてよい
                p = subprocess.Popen(cmd, cwd=root, stdout=fh, stderr=subprocess.STDOUT)
            running.append((v, s, p, out))
            print(f"開始: {v} seed {s}  (出力 {out.relative_to(root)})", flush=True)
        time.sleep(1)
        for item in list(running):
            v, s, p, out = item
            if p.poll() is not None:
                running.remove(item)
                ok = p.returncode == 0
                print(
                    f"{'終了' if ok else '失敗'}: {v} seed {s}  (終了コード {p.returncode})",
                    flush=True,
                )
                if not ok:
                    failed.append((v, s, out))
    if failed:
        print("失敗した run:", file=sys.stderr)
        for v, s, out in failed:
            print(f"  - {v} seed {s}: {out.relative_to(root)}", file=sys.stderr)
        return 1
    print("全部終わりました。次は: uv run scripts/collect.py " + exp_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
