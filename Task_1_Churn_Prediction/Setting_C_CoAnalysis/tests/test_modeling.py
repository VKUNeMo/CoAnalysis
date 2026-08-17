import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
from src.baseline.feature_engineering import compute_rfm_features
from src.baseline.trainer import train_baseline_model
from src.baseline.evaluator import evaluate_baseline

def test_baseline_features_and_training(sample_orders_df, sample_customers_df, sample_payments_df):
    # Compute RFM features
    rfm_df = compute_rfm_features(
        orders_df=sample_orders_df,
        customers_df=sample_customers_df,
        payments_df=sample_payments_df,
        cutoff_date="2018-01-25"
    )
    
    assert len(rfm_df) == 2
    assert set(rfm_df['customer_unique_id']) == {'cust1', 'cust2'}
    
    # Train set
    X_train = rfm_df[['recency', 'frequency', 'monetary']]
    y_train = pd.Series([1, 0], index=rfm_df.index)
    
    model, scaler = train_baseline_model(X_train, y_train)
    assert model is not None
    assert scaler is not None
    
    # Evaluate
    metrics, curves = evaluate_baseline(model, scaler, X_train, y_train)
    assert 'auc_roc' in metrics
    assert 'f1' in metrics
