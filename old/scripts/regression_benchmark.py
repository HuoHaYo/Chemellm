"""Compare regression output to archived NIST StRD certified numbers."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.benchmarks import evaluate_regression


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/qa/regression-benchmark.json"))
    args = parser.parse_args()
    output = evaluate_regression()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"passed": output["passed"], "cases": [{"name": r["name"], "passed": r["passed"]} for r in output["results"]], "report": str(args.output)}, ensure_ascii=False))
    return 0 if output["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
