import pandas as pd
import logging

logger = logging.getLogger("churn_prediction.baseline.feature_engineering")

def compute_rfm_features(orders_df: pd.DataFrame, customers_df: pd.DataFrame, payments_df: pd.DataFrame, cutoff_date: str) -> pd.DataFrame:
    """
    Compute baseline RFM features (Recency, Frequency, Monetary) from raw data.
    Ensures all calculations strictly respect the cutoff_date to prevent data leakage.
    """
    cutoff_dt = pd.to_datetime(cutoff_date)
    
    # 1. Filter orders before or at cutoff
    orders_filtered = orders_df[orders_df['order_purchase_timestamp'] <= cutoff_dt].copy()
    
    # 2. Merge with customers to get customer_unique_id
    orders_cust = pd.merge(orders_filtered, customers_df[['customer_id', 'customer_unique_id']], on='customer_id', how='inner')
    
    if orders_cust.empty:
        logger.warning(f"No orders found before cutoff {cutoff_date}. Returning empty RFM features.")
        return pd.DataFrame(columns=['customer_unique_id', 'recency', 'frequency', 'monetary'])
        
    # 3. Compute Recency: days from last order to cutoff
    # 4. Compute Frequency: number of unique orders
    rf_df = orders_cust.groupby('customer_unique_id').agg(
        last_order_date=('order_purchase_timestamp', 'max'),
        frequency=('order_id', 'nunique')
    ).reset_index()
    
    rf_df['recency'] = (cutoff_dt - rf_df['last_order_date']).dt.days.astype('float32')
    
    # 5. Compute Monetary: sum of payments for those orders
    # First, aggregate payment_value per order_id to prevent double counting
    order_payments = payments_df[payments_df['order_id'].isin(orders_filtered['order_id'])].copy()
    cust_payments = pd.merge(order_payments, orders_cust[['order_id', 'customer_unique_id']], on='order_id', how='inner')
    monetary_df = cust_payments.groupby('customer_unique_id').agg(
        monetary=('payment_value', 'sum')
    ).reset_index()
    
    # 6. Merge RF and Monetary
    rfm_df = pd.merge(rf_df[['customer_unique_id', 'recency', 'frequency']], monetary_df, on='customer_unique_id', how='left')
    rfm_df['monetary'] = rfm_df['monetary'].fillna(0.0).astype('float32')
    rfm_df['frequency'] = rfm_df['frequency'].astype('int32')
    
    logger.info(f"Computed RFM features for {len(rfm_df)} customers as of {cutoff_date}.")
    
    return rfm_df
