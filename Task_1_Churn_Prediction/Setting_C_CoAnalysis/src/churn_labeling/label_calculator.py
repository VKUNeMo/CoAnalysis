import pandas as pd
import logging

logger = logging.getLogger("churn_prediction.churn_labeling.label_calculator")

def compute_churn_labels(orders_df, customers_df, cutoff_date, observation_window_days=180, churn_window_days=90):
    """
    Compute binary churn label for each customer in the cohort defined by cutoff_date.
    Cohort: customers who placed at least one order in [cutoff_date - observation_window_days, cutoff_date].
    Label: churn=1 if no 'delivered' orders in (cutoff_date, cutoff_date + churn_window_days], else churn=0.
    """
    cutoff_dt = pd.to_datetime(cutoff_date)
    obs_start_dt = cutoff_dt - pd.Timedelta(days=observation_window_days)
    pred_end_dt = cutoff_dt + pd.Timedelta(days=churn_window_days)
    
    # Associate orders with customer_unique_id
    orders_extended = pd.merge(orders_df, customers_df[['customer_id', 'customer_unique_id']], on='customer_id', how='left')
    
    # 1. Identify cohort (customers active in observation window)
    obs_orders = orders_extended[
        (orders_extended['order_purchase_timestamp'] >= obs_start_dt) &
        (orders_extended['order_purchase_timestamp'] <= cutoff_dt)
    ]
    
    if obs_orders.empty:
        logger.warning(f"No orders found in the observation window [{obs_start_dt}, {cutoff_dt}].")
        return pd.DataFrame(), {}
        
    cohort_customers = obs_orders['customer_unique_id'].unique()
    logger.info(f"Cohort size at cutoff {cutoff_date}: {len(cohort_customers)} unique customers.")
    
    # 2. Get last order date before cutoff for each customer in cohort
    last_order_before_cutoff = obs_orders.groupby('customer_unique_id')['order_purchase_timestamp'].max()
    
    # 3. Check for delivered orders in prediction window (cutoff_dt, pred_end_dt]
    pred_orders = orders_extended[
        (orders_extended['order_purchase_timestamp'] > cutoff_dt) &
        (orders_extended['order_purchase_timestamp'] <= pred_end_dt) &
        (orders_extended['order_status'] == 'delivered')
    ]
    
    active_in_pred = set(pred_orders['customer_unique_id'].unique())
    
    # 4. Build customer-level cohort dataframe with labels
    cohort_rows = []
    for cust_id in cohort_customers:
        last_date = last_order_before_cutoff[cust_id]
        days_since = (cutoff_dt - last_date).days
        
        # Churn=1 if not active in prediction window, 0 otherwise
        churn_label = 0 if cust_id in active_in_pred else 1
        
        cohort_rows.append({
            'customer_unique_id': cust_id,
            'last_order_date': last_date,
            'days_since_last_order': days_since,
            'churn_label': churn_label
        })
        
    cohort_df = pd.DataFrame(cohort_rows)
    
    # Calculate class distribution
    class_counts = cohort_df['churn_label'].value_counts().to_dict()
    class_distribution = {
        0: class_counts.get(0, 0),
        1: class_counts.get(1, 0)
    }
    
    logger.info(f"Churn label calculation complete. Class distribution: {class_distribution}")
    
    return cohort_df, class_distribution
