"""E1: Does the TDP collapse reproduce without the oracle?  Grid defined in experiments/grid.py."""
import sys

from experiments.grid import main

if __name__ == "__main__":
    sys.argv.insert(1, "e1")
    main()
