"""E7: What do false quarantines cost?  Grid defined in experiments/grid.py."""
import sys

from experiments.grid import main

if __name__ == "__main__":
    sys.argv.insert(1, "e7")
    main()
