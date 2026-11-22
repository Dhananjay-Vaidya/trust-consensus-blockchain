"""E6: How does the audit budget trade off against detection?  Grid defined in experiments/grid.py."""
import sys

from experiments.grid import main

if __name__ == "__main__":
    sys.argv.insert(1, "e6")
    main()
