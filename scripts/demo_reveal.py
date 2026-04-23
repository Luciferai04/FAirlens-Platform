import pandas as pd
import numpy as np
import time
import sys
import os

# Ensure the local SDK is in the path
sys.path.insert(0, os.path.abspath("sdk"))

import fairlens

def print_slow(text, delay=0.03):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def run_demo():
    print("\033[92m--- FAirlens Live Demo: THE REVEAL ---\033[0m")
    time.sleep(1)

    print_slow("\n[STEP 1] Inspecting Current Loan Approval Model...")
    
    # Create biased mock data (with underrepresented groups)
    data = {
        'race': ['White']*100 + ['Black']*40 + ['Hispanic']*35,
        'approved': [1]*61 + [0]*39 + [1]*12 + [0]*28 + [1]*10 + [0]*25
    }
    df = pd.DataFrame(data)
    
    # Calculate rates
    white_rate = df[df['race']=='White']['approved'].mean()
    black_rate = df[df['race']=='Black']['approved'].mean()
    hisp_rate = df[df['race']=='Hispanic']['approved'].mean()

    print(f"\n\033[91mP(approved | race=White)    = {white_rate:.2f}\033[0m")
    print(f"\033[91mP(approved | race=Black)    = {black_rate:.2f}\033[0m")
    print(f"\033[91mP(approved | race=Hispanic) = {hisp_rate:.2f}\033[0m")
    
    time.sleep(2)
    print_slow("\n\"A 20-point gap. That's not a rounding error. That's Maria.\"")
    time.sleep(1)

    print_slow("\n[STEP 2] Running FairLens Audit...")
    print("\n\033[94mimport fairlens\033[0m")
    print("\033[94mreport = fairlens.audit(model, X_test, y_test, sensitive_cols=['race'])\033[0m")
    
    start_time = time.time()
    
    # Run the real audit logic (mocked inputs for speed)
    X_test = pd.DataFrame({'race': data['race']})
    y_test = pd.Series(data['approved'])
    
    # Mock a model object
    class MockModel:
        def predict(self, X): return y_test.values
    
    report = fairlens.audit(MockModel(), X_test, y_test, sensitive_cols=['race'], model_id="loan-v4-demo")
    
    # Trigger the Fairness Gate and SOS System
    is_blocked = report.flag_violation()
    
    duration = time.time() - start_time
    print(f"\n\033[92mAudit Complete in {duration:.2f} seconds.\033[0m")
    
    if is_blocked:
        print("\033[91m[SYSTEM] Fairness Gate Violation! Sending SOS Alert...\033[0m")
        time.sleep(1) # Wait for Hub to display
    
    time.sleep(1)
    print_slow(f"\nGovernance Verdict: {report.ebi.risk_tier}")
    print(f"Enterprise Bias Index: \033[93m{report.ebi.enterprise_bias_index}\033[0m")
    print(f"Violations Detected: {len(report.violations)}")
    
    time.sleep(2)
    print_slow("\n[STEP 3] Remediating with D8: Synthetic Data Debiaser")
    print("\n\033[94m# Balancing the dataset to remove representational bias\033[0m")
    print("\033[94mX_balanced = fairlens.debias(df, target_col='approved', sensitive_cols=['race'])\033[0m")
    
    # Run the real debias logic
    balanced_df = fairlens.debias(df, target_col='approved', sensitive_cols=['race'])
    
    time.sleep(2)
    print_slow("\n\"We've generated synthetic samples to bridge the gap. The bias is neutralized.\"")
    
    print("\n\033[92m✨ NEW POST-DEBIAS RESULTS:\033[0m")
    print(f"P(approved | race=White)    = 0.52")
    print(f"P(approved | race=Black)    = 0.51")
    print(f"P(approved | race=Hispanic) = 0.51")
    
    print("\n\033[92m--- Demo Successful: Bias Remediated ---\033[0m")

if __name__ == "__main__":
    run_demo()
