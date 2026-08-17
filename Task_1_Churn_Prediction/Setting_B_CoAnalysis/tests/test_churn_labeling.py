import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
from src.churn_labeling.label_calculator import compute_churn_labels
from src.churn_labeling.validator import validate_labels

def test_compute_churn_labels(sample_orders_df, sample_customers_df):
    # Cutoff at 2018-01-25
    # Observation: 180 days -> active since 2017-07-29
    # Prediction window: 90 days -> check delivered orders between 2018-01-25 and 2018-04-25
    
    # Active in obs:
    # cust1 has orders at 2018-01-01, 2018-01-15 -> last order 2018-01-15 -> days since = 10 days
    # cust2 has order at 2018-01-20 -> last order 2018-01-20 -> days since = 5 days
    # cust3 has order at 2018-02-10 (post-cutoff) -> not in cohort
    
    cohort_df, dist = compute_churn_labels(
        sample_orders_df, sample_customers_df,
        cutoff_date="2018-01-25",
        observation_window_days=180,
        churn_window_days=90
    )
    
    assert len(cohort_df) == 2
    assert set(cohort_df['customer_unique_id']) == {'cust1', 'cust2'}
    
    # Check predictions window delivered orders:
    # cust3 has o4 delivered at 2018-02-10, but cust3 not in cohort
    # cust1 has no delivered orders after 2018-01-25 -> churned (1)
    # cust2 has no delivered orders after 2018-01-25 -> churned (1)
    
    cust1_row = cohort_df[cohort_df['customer_unique_id'] == 'cust1'].iloc[0]
    assert cust1_row['churn_label'] == 1
    assert cust1_row['days_since_last_order'] == 10
    
    # Test validator
    val_report = validate_labels(
        cohort_df, sample_orders_df, sample_customers_df,
        cutoff_date="2018-01-25", churn_window_days=90, sample_size=2
    )
    assert val_report['validation_passed'] is True
