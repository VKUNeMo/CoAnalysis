import pandas as pd
import logging
from src.churn_labeling.label_calculator import compute_churn_labels

logger = logging.getLogger("churn_prediction.data_splitting.temporal_splitter")

def temporal_train_test_split(orders_df, customers_df, train_cutoff, test_cutoff,
                              observation_window_days=180, prediction_window_days=90):
    """
    Construct train and test cohorts based on strict cutoff dates and observation/prediction windows.
    No random splitting is performed.
    """
    logger.info(f"Generating train cohort as of {train_cutoff}...")
    train_df, train_dist = compute_churn_labels(
        orders_df, customers_df, train_cutoff,
        observation_window_days, prediction_window_days
    )
    
    logger.info(f"Generating test cohort as of {test_cutoff}...")
    test_df, test_dist = compute_churn_labels(
        orders_df, customers_df, test_cutoff,
        observation_window_days, prediction_window_days
    )
    
    total_train = len(train_df)
    total_test = len(test_df)
    total_combined = total_train + total_test
    
    train_churn_rate = train_df['churn_label'].mean() if total_train > 0 else 0
    test_churn_rate = test_df['churn_label'].mean() if total_test > 0 else 0
    
    split_report = {
        'train_cutoff': train_cutoff,
        'test_cutoff': test_cutoff,
        'train_size': total_train,
        'test_size': total_test,
        'train_churn_rate': float(train_churn_rate),
        'test_churn_rate': float(test_churn_rate),
        'test_ratio': float(total_test / total_combined) if total_combined > 0 else 0
    }
    
    logger.info(f"Temporal split complete. Report: {split_report}")
    
    return train_df, test_df, split_report
