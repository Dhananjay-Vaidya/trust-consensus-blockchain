"""E2: Does SleeperGuard fix it?  Grid defined in experiments/grid.py."""
import sys

from experiments.grid import main

if __name__ == "__main__":
    sys.argv.insert(1, "e2")
    main()
