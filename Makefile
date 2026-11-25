# Cross-platform equivalents of every target: python scripts/reproduce.py ... (see docs/DECISIONS.md D17)
PY ?= python

.PHONY: test smoke reproduce assets paper lint typecheck clean-smoke e14

test:
	$(PY) -m pytest -q tests

smoke:
	$(PY) scripts/reproduce.py --smoke

reproduce:   # runs every experiment incl. E4 band/leakage, then regenerates paper assets
	$(PY) scripts/reproduce.py

e14:   # change-detection baselines (calibration seeds 20-29, search 30-39, eval 100-129)
	$(PY) scripts/reproduce.py --only e14

assets:
	$(PY) paper/make_assets.py

paper: assets
	cd paper && latexmk -pdf -interaction=nonstopmode main.tex

lint:
	$(PY) -m ruff check main.py src experiments paper/make_assets.py scripts tests

typecheck:
	$(PY) -m mypy main.py src/config src/crypto src/trust/sleeper_guard.py src/trust/capping.py src/trust/detectors.py src/env src/metrics src/stats src/consensus

clean-smoke:
	rm -rf results/raw/*_smoke
