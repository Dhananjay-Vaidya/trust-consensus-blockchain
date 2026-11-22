"""DoD 2: no decision path references ground truth.

Ground truth lives in src/env/world.py (the simulated world) and src/env/attacks.py (the adversary).
Only src/metrics/ may read it.  This test fails if any other module under src/ touches the
world's private state or names ground-truth fields, except for the narrow exceptions below.
"""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
ALLOWED = {SRC / "env" / "world.py", SRC / "env" / "attacks.py"}
ALLOWED_DIRS = {SRC / "metrics"}

P_WORLD = r"\b_world\b"
P_COALITION = r"\bcoalition\b"
P_IS_MAL = r"\bis_malicious\b"
FORBIDDEN = [
    P_WORLD,
    r"ground_truth_record",
    r"\bis_valid\b",
    r"\bvalidity\b",
    r"\b_validity\b",
    P_COALITION,
    r"true_malicious",
    r"true_honest",
    P_IS_MAL,
    r"\bbribed_at\b",
]

# Narrow, per-file exceptions:
#  * honest_env.py constructs the world and calls its public protocol (checked below);
#  * the API forwards post-hoc display labels obtained from src.metrics (dashboard colouring only),
#    under the pre-existing event key ``is_malicious``.
PER_FILE_EXCEPTIONS = {
    "src/env/honest_env.py": {P_WORLD, P_COALITION},
    "src/api/models.py": {P_IS_MAL},
    "src/api/simulation_runner.py": {P_IS_MAL},
}


def _scan() -> list[tuple[str, int, str, str]]:
    hits = []
    for p in SRC.rglob("*.py"):
        if p in ALLOWED or any(d in p.parents for d in ALLOWED_DIRS):
            continue
        rel = p.relative_to(SRC.parent).as_posix()
        for ln, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            code = line.split("#", 1)[0]
            for pat in FORBIDDEN:
                if re.search(pat, code) and pat not in PER_FILE_EXCEPTIONS.get(rel, set()):
                    hits.append((rel, ln, pat, line.strip()))
    return hits


def test_no_ground_truth_identifiers_outside_metrics_and_world():
    bad = _scan()
    assert not bad, "ground truth referenced outside src/metrics:\n" + "\n".join(map(str, bad))


def test_honest_env_only_uses_world_through_its_public_protocol():
    """HonestEnv may call new_transactions / cast_votes / audit / publish / corrupt, and read the
    coalition only to build the candidate list for the E8 briber (adversary-side code path)."""
    src = (SRC / "env" / "honest_env.py").read_text(encoding="utf-8")
    uses = set(re.findall(r"self\._world\.(\w+)", src))
    assert uses <= {"new_transactions", "cast_votes", "audit", "publish", "corrupt", "coalition"}, uses
    for line in src.splitlines():
        if "self._world.coalition" in line:
            assert "candidates" in line, line


def test_api_gets_labels_only_from_metrics():
    runner = (SRC / "api" / "simulation_runner.py").read_text(encoding="utf-8")
    for line in runner.splitlines():
        if '"is_malicious"' in line:
            assert "display_labels" in line or line.strip().endswith("{},"), line
