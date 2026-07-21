"""Runs the test suite and prints the required report bundle:

  1. pytest summary
  2. share-completeness backlog
  3. thin-bucket census
  4. outbound sensitivity number
  5. baseline-vs-current schema gap finding
  6. which tests failed and why (from pytest's own output)

Run:
    cd backend && .venv/bin/python -m tests.run_report
"""
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).parent
OUT = HERE / "_out"


def line(char="=", width=76):
    print(char * width)


def show_file(path: Path, header: str) -> None:
    line()
    print(header)
    line()
    if not path.exists():
        print(f"  (missing: {path.name})")
        return
    print(path.read_text().rstrip("\n"))


def main() -> int:
    # Run pytest — verbose, no capture, tests write their own artefacts.
    print("\nRunning pytest…\n")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", "--tb=short", "backend/tests"],
        cwd=HERE.parent.parent,
        capture_output=False,
    )
    exit_code = result.returncode
    print()

    # Artefacts written by individual tests
    show_file(OUT / "share_backlog.txt",       "SHARE-COMPLETENESS BACKLOG (full list, sorted by shortfall)")
    show_file(OUT / "thin_buckets.txt",        "THIN-BUCKET CENSUS")
    show_file(OUT / "outbound_sensitivity.txt","OUTBOUND SENSITIVITY (probe)")
    show_file(OUT / "schema_gap.txt",          "BASELINE vs CURRENT SEVERITY — schema gap finding")

    line()
    print("Done.")
    print(f"pytest exit: {exit_code}   (nonzero means one or more tests fail)")
    line()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
