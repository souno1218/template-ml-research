"""1 本の計算 (学習・評価) を回し、runs/<run_id>/ に記録を残す。

push 済みの commit からしか実行しない (docs/rules/running.md)。動作確認だけなら --dev。

  uv run scripts/run.py --config experiments/E0001-larger-lr/configs/baseline.toml \
      --experiment E0001 --variant baseline --seed 0
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import traceback
from pathlib import Path

from project_name import registry
from project_name.lab import gitstate
from project_name.lab.config import dump_config, load_config
from project_name.lab.proposals import rules_version
from project_name.lab.runs import environment, find_runs, make_run_id
from project_name.lab.suite import load_suite


class Tee:
    """書き込みを、元の出力とログファイルの両方へ流す。"""

    def __init__(self, stream, log):
        self.stream, self.log = stream, log

    def write(self, s):
        self.stream.write(s)
        self.log.write(s)
        self.log.flush()

    def flush(self):
        self.stream.flush()
        self.log.flush()


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--config", required=True)
    ap.add_argument("--experiment", required=True, help="施策の ID (E0001 など)")
    ap.add_argument("--variant", required=True, help="案の名前")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument(
        "--dev",
        action="store_true",
        help="動作確認。git の確認を飛ばし、runs/dev/ に書く (集計されない)",
    )
    ap.add_argument("--runs-dir", default="runs")
    args = ap.parse_args()

    root = gitstate.repo_root()
    st = gitstate.state(root)
    if not args.dev:
        problems = gitstate.check_runnable(st)
        if problems:
            print(
                "実行しません (push 済みの commit からだけ実行する。docs/rules/running.md):",
                file=sys.stderr,
            )
            for p in problems:
                print(f"  - {p}", file=sys.stderr)
            return 2

    config_path = Path(args.config).resolve()
    cfg = load_config(config_path)
    run_cfg = cfg.get("run", {})
    registry.load_plugins(root / p for p in run_cfg.get("plugins", []))
    job = registry.get("job", run_cfg["job"])

    # 評価一式を使う設定なら、照合してから版とハッシュを記録する (変えていない評価で測った証拠)
    suite_info = None
    suite_version = cfg.get("eval", {}).get("suite")
    if suite_version:
        suite = load_suite(suite_version, root)
        suite.verify()
        suite_info = {"version": suite.version, "sha256": suite.fingerprint()}

    # 同じ施策・案・seed・commit で終わっていない run があれば、その続きから再開する
    resumed = None
    if not args.dev:
        for r in find_runs(root / args.runs_dir, args.experiment, finished_only=False):
            m = r.meta
            if (m["variant"], int(m["seed"]), m["commit"]) == (
                args.variant,
                args.seed,
                st.commit,
            ) and m.get("status") != "ok":
                resumed = r
    if resumed is not None:
        run_id, run_dir = resumed.run_id, resumed.dir
        print(f"終わっていない run {run_id} の続きから再開する")
    else:
        run_id = make_run_id(args.experiment, args.variant, args.seed)
        run_dir = root / args.runs_dir / ("dev" if args.dev else "") / run_id
        run_dir.mkdir(parents=True)
    dump_config(cfg, run_dir / "config.toml")
    meta = {
        "run_id": run_id,
        "experiment": args.experiment,
        "variant": args.variant,
        "seed": args.seed,
        "config": str(config_path.relative_to(root)),
        "dev": args.dev,
        "commit": st.commit,
        "branch": st.branch,
        "dirty": st.dirty,
        "rules_version": rules_version(root),
        "suite": suite_info,
        **environment(),
        "started": dt.datetime.now().isoformat(timespec="seconds"),
        "status": "running",
        "resumes": (resumed.meta.get("resumes", 0) + 1) if resumed is not None else 0,
    }
    if resumed is not None:
        meta["first_started"] = resumed.meta.get("first_started", resumed.meta.get("started"))

    def save_meta():
        (run_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))

    save_meta()
    code = 0
    with open(run_dir / "log.txt", "a") as log:
        out, err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = Tee(out, log), Tee(err, log)
        try:
            print(f"run {run_id}  commit {st.short}  job {run_cfg['job']}")
            job(cfg, run_dir, args.seed)
            if (run_dir / "metrics.json").exists():
                meta["status"] = "ok"
            else:
                meta["status"], code = "failed", 1
                print("ジョブが metrics.json を書かなかった", file=sys.stderr)
        except KeyboardInterrupt:
            meta["status"], code = "interrupted", 130
            print("中断しました", file=sys.stderr)
        except Exception:
            meta["status"], code = "failed", 1
            traceback.print_exc()
        finally:
            sys.stdout, sys.stderr = out, err
            meta["finished"] = dt.datetime.now().isoformat(timespec="seconds")
            save_meta()
    print(f"{meta['status']}: {run_dir.relative_to(root)}")
    return code


if __name__ == "__main__":
    sys.exit(main())
