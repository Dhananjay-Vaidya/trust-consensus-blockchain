"""E3: Which SleeperGuard component matters?  Grid defined in experiments/grid.py."""
import sys

from experiments.grid import main

if __name__ == "__main__":
    sys.argv.insert(1, "e3")
    main()
