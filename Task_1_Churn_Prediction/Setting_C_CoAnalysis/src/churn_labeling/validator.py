import pandas as pd
import logging

logger = logging.getLogger("churn_prediction.churn_labeling.validator")

def validate_labels(cohort_df, orders_df, customers_df, cutoff_date, churn_window_days=90, sample_size=10, random_seed=42):
    """
    Validate churn labeling by sampling customers, checking their post-cutoff order history,
    and verifying if expected_label matches actual_label.
    """
    if cohort_df.empty:
        logger.warning("Cohort dataframe is empty. Skipping label validation.")
        return {"validation_passed": False}
        
    cutoff_dt = pd.to_datetime(cutoff_date)
    pred_end_dt = cutoff_dt + pd.Timedelta(days=churn_window_days)
    
    # Merge orders to get customer_unique_id
    orders_extended = pd.merge(orders_df, customers_df[['customer_id', 'customer_unique_id']], on='customer_id', how='left')
    
    # Sample customers
    sample_df = cohort_df.sample(n=min(sample_size, len(cohort_df)), random_state=random_seed)
    
    sampled_customers = []
    all_checks_passed = True
    
    for idx, row in sample_df.iterrows():
        cust_id = row['customer_unique_id']
        actual_label = row['churn_label']
        
        # Look up orders for this customer in prediction window
        cust_pred_orders = orders_extended[
            (orders_extended['customer_unique_id'] == cust_id) &
            (orders_extended['order_purchase_timestamp'] > cutoff_dt) &
            (orders_extended['order_purchase_timestamp'] <= pred_end_dt) &
            (orders_extended['order_status'] == 'delivered')
        ]
        
        expected_label = 0 if len(cust_pred_orders) > 0 else 1
        check_passed = (expected_label == actual_label)
        
        if not check_passed:
            all_checks_passed = False
            logger.error(f"Validation FAILED for customer {cust_id}: actual_label={actual_label}, expected_label={expected_label}")
            
        sampled_customers.append({
            'customer_unique_id': cust_id,
            'last_order_date': str(row['last_order_date']),
            'days_since_last_order': int(row['days_since_last_order']),
            'actual_label': int(actual_label),
            'expected_label': int(expected_label),
            'check_passed': bool(check_passed)
        })
        
    class_counts = cohort_df['churn_label'].value_counts().to_dict()
    total = len(cohort_df)
    class_distribution = {
        '0': class_counts.get(0, 0),
        '1': class_counts.get(1, 0),
        '0_pct': class_counts.get(0, 0) / total if total > 0 else 0,
        '1_pct': class_counts.get(1, 0) / total if total > 0 else 0
    }
    
    validation_report = {
        'sampled_customers': sampled_customers,
        'class_distribution': class_distribution,
        'validation_passed': all_checks_passed
    }
    
    logger.info(f"Label validation completed. Passed: {all_checks_passed}. Class distribution: {class_distribution}")
    
    return validation_report
