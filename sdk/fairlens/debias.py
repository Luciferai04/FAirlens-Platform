import pandas as pd
import numpy as np
from typing import List, Dict, Optional

class SyntheticDebiaser:
    """
    Implements D8: Synthetic Data Debiaser.
    Uses conditional resampling and noise injection to balance underrepresented groups
    while maintaining statistical fidelity.
    """
    
    def __init__(self, target_col: str, sensitive_cols: List[str]):
        self.target_col = target_col
        self.sensitive_cols = sensitive_cols

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Balances the dataset across sensitive attributes.
        Returns a 'Fairened' dataset with synthetic samples for minority groups.
        """
        print(f"🚀 Initializing Synthetic Data Debiaser (D8)...")
        print(f"📊 Analyzing distribution across: {self.sensitive_cols}")
        
        # Calculate group counts
        group_counts = df.groupby(self.sensitive_cols).size().reset_index(name='counts')
        max_count = group_counts['counts'].max()
        
        debiased_df = df.copy()
        
        for _, group in group_counts.iterrows():
            if group['counts'] < max_count:
                # Minority group detected - generate synthetic samples
                diff = max_count - group['counts']
                print(f"✨ Generating {diff} synthetic samples for group: {group[self.sensitive_cols].values}")
                
                # Filter original group data
                query = " and ".join([f"`{col}` == '{val}'" if isinstance(val, str) else f"`{col}` == {val}" 
                                    for col, val in zip(self.sensitive_cols, group[self.sensitive_cols])])
                minority_samples = df.query(query)
                
                if len(minority_samples) > 0:
                    # Sample with replacement and add minor Gaussian noise to continuous features
                    synthetic = minority_samples.sample(n=diff, replace=True)
                    
                    # Add noise to numeric columns to prevent exact duplication (simple GAN-like behavior)
                    numeric_cols = synthetic.select_dtypes(include=[np.number]).columns
                    for col in numeric_cols:
                        std = synthetic[col].std() or 0.01
                        synthetic[col] += np.random.normal(0, std * 0.05, size=len(synthetic))
                    
                    debiased_df = pd.concat([debiased_df, synthetic], ignore_index=True)
        
        print(f"✅ Debias Complete: Dataset grew from {len(df)} to {len(debiased_df)} rows.")
        return debiased_df

def debias(df: pd.DataFrame, target_col: str, sensitive_cols: List[str]) -> pd.DataFrame:
    """Convenience wrapper for the SyntheticDebiaser."""
    engine = SyntheticDebiaser(target_col, sensitive_cols)
    return engine.fit_transform(df)
