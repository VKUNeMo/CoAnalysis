import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
from src.data_splitting.temporal_splitter import temporal_train_test_split
from src.data_splitting.validator import validate_temporal_split

def test_temporal_train_test_split(sample_orders_df, sample_customers_df):
    train_df, test_df, report = temporal_train_test_split(
        sample_orders_df, sample_customers_df,
        train_cutoff="2018-01-18",
        test_cutoff="2018-02-15",
        observation_window_days=30,
        prediction_window_days=30
    )
    
    # Train cohort active between 2017-12-19 and 2018-01-18:
    # cust1 (orders at 2018-01-01, 2018-01-15) -> in train cohort
    # cust2 (order at 2018-01-20) -> not in train
    
    # Test cohort active between 2018-01-16 and 2018-02-15:
    # cust2 (order at 2018-01-20) -> in test cohort
    # cust3 (order at 2018-02-10) -> in test cohort
    
    assert 'cust1' in train_df['customer_unique_id'].values
    assert 'cust2' not in train_df['customer_unique_id'].values
    
    assert 'cust2' in test_df['customer_unique_id'].values
    assert 'cust3' in test_df['customer_unique_id'].values
    
    # Validate split (no leakage)
    val_report = validate_temporal_split(
        train_df, test_df,
        train_cutoff="2018-01-18",
        test_cutoff="2018-02-15"
    )
    assert val_report['temporal_split_valid'] is True
