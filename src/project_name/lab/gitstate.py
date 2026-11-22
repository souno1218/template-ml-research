"""git の状態を調べる。リポジトリの根は、パッケージの場所ではなく今いるディレクトリから決める。"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


def _git(*args: str, cwd: str | Path | None = None) -> str:
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} が失敗: {out.stderr.strip()}")
    return out.stdout.strip()


def repo_root(cwd: str | Path | None = None) -> Path:
    """今いるディレクトリを含む git リポジトリの根。"""
    return Path(_git("rev-parse", "--show-toplevel", cwd=cwd))


@dataclass
class GitState:
    commit: str  # HEAD の完全なハッシュ
    short: str
    branch: str  # detached なら "HEAD"
    dirty: bool  # 追跡中のファイルに未コミットの変更がある、または追跡していないファイルがある
    upstream: str | None  # 追跡している origin のブランチ (なければ None)
    upstream_commit: str | None

    @property
    def pushed(self) -> bool:
        return self.upstream_commit is not None and self.upstream_commit == self.commit


def state(cwd: str | Path | None = None) -> GitState:
    commit = _git("rev-parse", "HEAD", cwd=cwd)
    branch = _git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd)
    # runs/ などは .gitignore で除外されているので、ここに出るのは本当の変更だけ
    dirty = bool(_git("status", "--porcelain", cwd=cwd))
    try:
        upstream = _git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", cwd=cwd)
        upstream_commit = _git("rev-parse", "@{u}", cwd=cwd)
    except RuntimeError:
        upstream, upstream_commit = None, None
    return GitState(commit, commit[:7], branch, dirty, upstream, upstream_commit)


def check_runnable(st: GitState) -> list[str]:
    """push 済みの commit から実行できる状態かを調べ、問題の一覧を返す (空なら実行してよい)。"""
    problems = []
    if st.dirty:
        problems.append(
            "未コミットの変更 (または追跡していないファイル) がある。commit して push する"
        )
    if st.upstream is None:
        problems.append(
            f"ブランチ {st.branch} が origin を追跡していない。git push -u origin {st.branch} する"
        )
    elif not st.pushed:
        problems.append(
            f"HEAD ({st.short}) が {st.upstream} ({(st.upstream_commit or '')[:7]}) と一致しない。"
            "push していないか、pull していない"
        )
    return problems
