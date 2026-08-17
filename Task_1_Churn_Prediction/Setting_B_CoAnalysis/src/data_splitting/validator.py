import pandas as pd
import logging

logger = logging.getLogger("churn_prediction.data_splitting.validator")

def validate_temporal_split(train_cohort, test_cohort, train_cutoff, test_cutoff):
    """
    Validate that the temporal split contains no data leakage.
    Ensures that for each cohort, all historical order dates are on or before the cutoff date,
    and reports distribution details.
    """
    train_cutoff_dt = pd.to_datetime(train_cutoff)
    test_cutoff_dt = pd.to_datetime(test_cutoff)
    
    # Check max order date in train cohort (which should be <= train_cutoff)
    max_train_date = train_cohort['last_order_date'].max()
    max_train_date_ok = max_train_date <= train_cutoff_dt
    
    # Check max order date in test cohort (which should be <= test_cutoff)
    max_test_date = test_cohort['last_order_date'].max()
    max_test_date_ok = max_test_date <= test_cutoff_dt
    
    # Data leakage check: train_cohort customer labels must not be derived from test period
    # Calculate days since last order check
    train_violations = (train_cohort['last_order_date'] > train_cutoff_dt).sum()
    test_violations = (test_cohort['last_order_date'] > test_cutoff_dt).sum()
    
    leakage_detected = (train_violations > 0) or (test_violations > 0)
    
    # Overlap analysis
    train_customers = set(train_cohort['customer_unique_id'].unique())
    test_customers = set(test_cohort['customer_unique_id'].unique())
    overlap = len(train_customers.intersection(test_customers))
    
    report = {
        'max_train_date': str(max_train_date),
        'max_test_date': str(max_test_date),
        'train_cutoff_respected': bool(max_train_date_ok),
        'test_cutoff_respected': bool(max_test_date_ok),
        'train_violations': int(train_violations),
        'test_violations': int(test_violations),
        'overlap_count': overlap,
        'leakage_detected': bool(leakage_detected),
        'temporal_split_valid': bool(not leakage_detected and max_train_date_ok and max_test_date_ok)
    }
    
    if report['temporal_split_valid']:
        logger.info(f"Temporal split is VALID. No leakage detected. Overlap: {overlap} customers.")
    else:
        logger.error(f"Temporal split is INVALID! Leakage detected: {report}")
        
    return report
