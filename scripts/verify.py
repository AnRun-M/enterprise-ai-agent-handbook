"""Unified local verification workflow（跨平台 Python 单脚本，唯一事实源）。

用法：
    python scripts/verify.py             # pytest + ruff + mkdocs --strict + git diff --check
    python scripts/verify.py --typing    # 额外运行 mypy（optional，不阻塞主验证）

固定原则："One verification workflow, one source of truth."
- 本地聚合 CI 的 tests.yml（pytest + ruff）与 docs.yml（mkdocs build --strict），
  并加 git diff --check——CI job 职责保持清晰，本地减少遗漏，不引入单点脚本
  故障导致所有 CI 同时失效（CI 不调用本脚本）。
- **不默认 git status 为 failure**：未提交合法工作树不应让开发验证失败；
  最后打印 `git status --short` 作为信息。
- `--typing`：mypy 尚处于 optional mode（TASK-0035：examples/text2sql_state
  baseline 仅 4 trivial annotation errors，待阶段 2 Review 批准范围后
  才可能升级为强制 gate——"New quality gate must have a passing baseline
  before it becomes mandatory."）。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS: tuple[tuple[str, list[str]], ...] = (
    ("pytest", [sys.executable, "-m", "pytest", "-q"]),
    ("ruff check .", [sys.executable, "-m", "ruff", "check", "."]),
    ("mkdocs build --strict", [sys.executable, "-m", "mkdocs", "build", "--strict"]),
    ("git diff --check", ["git", "diff", "--check"]),
)

# optional mode：不阻塞主验证；失败仅报告（TASK-0035 方案 C 过渡形态）
TYPING_STEP: tuple[str, list[str]] = (
    "mypy (examples/text2sql_state)",
    [
        sys.executable,
        "-m",
        "mypy",
        "--explicit-package-bases",
        "examples/text2sql_state",
    ],
)


def run(name: str, command: list[str], fail_on_error: bool) -> bool:
    """顺序执行一步验证；返回是否通过。"""
    print(f"==> {name}")
    result = subprocess.run(command, cwd=ROOT, check=False)
    ok = result.returncode == 0
    print(f"    {'PASS' if ok else 'FAIL'} - {name}")
    return ok or not fail_on_error


def main() -> int:
    failed: list[str] = []
    for name, command in STEPS:
        if not run(name, command, fail_on_error=True):
            failed.append(name)

    if "--typing" in sys.argv:
        run(TYPING_STEP[0], TYPING_STEP[1], fail_on_error=False)

    # 信息输出：未提交合法工作树不应使开发验证失败
    print("==> git status --short (informational)")
    subprocess.run(["git", "status", "--short"], cwd=ROOT, check=False)

    if failed:
        print(f"VERIFY FAILED: {', '.join(failed)}")
        return 1
    print("VERIFY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
