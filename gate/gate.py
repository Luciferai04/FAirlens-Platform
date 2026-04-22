#!/usr/bin/env python3
"""
FairLens CI/CD Fairness Gate
Usage: python gate.py --model-path model.pkl --eval-csv eval.csv --sensitive-cols gender,race
Exit 0 = pass. Exit 1 = violation. Exit 2 = error.
"""
import argparse
import json
import os
import sys
import pickle

import numpy as np
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description="FairLens Fairness Gate")
    parser.add_argument("--model-path", required=True,
                        help="Path to pickled sklearn model or model directory")
    parser.add_argument("--eval-csv", required=True,
                        help="Path to evaluation dataset CSV")
    parser.add_argument("--sensitive-cols", required=True,
                        help="Comma-separated sensitive attribute column names")
    parser.add_argument("--label-col", default="label",
                        help="Name of the label column in eval CSV")
    parser.add_argument("--policy", default="/gate/policy/default_policy.yaml",
                        help="Path to YAML policy file")
    parser.add_argument("--output-json", default=None,
                        help="Optional path to write JSON report")
    parser.add_argument("--feature-cols", default=None,
                        help="Comma-separated feature columns for model input (if not all columns)")
    args = parser.parse_args()

    try:
        # Import fairlens SDK
        try:
            import fairlens
        except ImportError:
            print("[FairLens Gate] ❌ ERROR: fairlens SDK not installed.", file=sys.stderr)
            print("  Install with: pip install fairlens", file=sys.stderr)
            sys.exit(2)

        # Load model
        print(f"[FairLens Gate] Loading model: {args.model_path}")
        with open(args.model_path, "rb") as f:
            model = pickle.load(f)

        # Load evaluation dataset
        print(f"[FairLens Gate] Loading eval dataset: {args.eval_csv}")
        df = pd.read_csv(args.eval_csv)
        y_test = df[args.label_col]
        X_test = df.drop(columns=[args.label_col])

        sensitive_cols = [c.strip() for c in args.sensitive_cols.split(",")]
        print(f"[FairLens Gate] Auditing across: {sensitive_cols}")

        # If feature-cols specified, wrap model to only pass those columns
        if args.feature_cols:
            feature_cols = [c.strip() for c in args.feature_cols.split(",")]
            class _FeatureWrapper:
                def __init__(self, m, cols):
                    self.m = m
                    self.cols = cols
                def predict(self, X):
                    return self.m.predict(X[self.cols])
            model = _FeatureWrapper(model, feature_cols)

        # Determine policy path
        policy_path = args.policy
        if not os.path.exists(policy_path):
            # Try relative to gate directory
            alt = os.path.join(os.path.dirname(__file__), "policy", "default_policy.yaml")
            if os.path.exists(alt):
                policy_path = alt
            else:
                policy_path = None  # Use defaults

        report = fairlens.audit(
            model=model,
            X_test=X_test,
            y_test=y_test,
            sensitive_cols=sensitive_cols,
            threshold_config=policy_path,
            triggered_by="ci_gate",
        )

        # Output structured JSON report
        result = report.to_dict()
        result_json = json.dumps(result, indent=2)
        print(result_json)

        if args.output_json:
            with open(args.output_json, "w") as f:
                f.write(result_json)

        if report.flag_violation():
            print(f"\n[FairLens Gate] ❌ FAILED — {len(report.violations)} violation(s)")
            for v in report.violations:
                print(f"  {v['col']}.{v['metric']}: {v['value']:.4f} "
                      f"(threshold: {v['threshold']:.4f})")
            sys.exit(1)
        else:
            print("\n[FairLens Gate] ✅ PASSED — all metrics within thresholds")
            sys.exit(0)

    except SystemExit:
        raise
    except Exception as e:
        print(f"[FairLens Gate] ❌ ERROR: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
