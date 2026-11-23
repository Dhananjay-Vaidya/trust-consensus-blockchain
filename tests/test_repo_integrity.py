"""No source file may be silently excluded by .gitignore (audit finding A15).

An unanchored `ENV/` rule matched `src/env/` on a case-insensitive filesystem, so the simulator core was
never committed and a fresh clone could not run. This test fails if any source, experiment, paper or
docs file is ignored.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = ["src/**/*.py", "experiments/*.py", "scripts/*.py", "tests/**/*.py", "paper/*.tex", "paper/*.py",
            "paper/*.bib", "docs/*.md", "docs/*.csv", "dashboard/src/**/*.ts", "dashboard/src/**/*.tsx",
            "dashboard/src/**/*.css"]


@pytest.mark.skipif(shutil.which("git") is None or not (ROOT / ".git").exists(), reason="needs a git checkout")
def test_no_source_file_is_gitignored():
    files = sorted({p for pat in PATTERNS for p in ROOT.glob(pat) if "__pycache__" not in p.parts})
    rel = [str(p.relative_to(ROOT)).replace("\\", "/") for p in files]
    out = subprocess.run(["git", "check-ignore", "--stdin"], cwd=ROOT, input="\n".join(rel),
                         capture_output=True, text=True)
    ignored = [line for line in out.stdout.splitlines() if line.strip()]
    assert not ignored, "source files excluded by .gitignore:\n" + "\n".join(ignored)
