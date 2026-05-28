from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path("experiments") / "_generate_paper_figures_impl.py"), run_name="__main__")
