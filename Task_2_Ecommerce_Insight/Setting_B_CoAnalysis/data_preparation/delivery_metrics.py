import pandas as pd
from utils.logger import get_logger

logger = get_logger("data_preparation.delivery_metrics")

def calculate_delivery_metrics(orders_normalized_df):
    """
    Computes delivery performance metrics: is_late, delivery_days, estimated_days, and late_days.
    """
    logger.info("Calculating delivery days and SLA metrics...")
    df = orders_normalized_df.copy()
    
    # Use dt.normalize() to get the date-only component at midnight for correct date-level subtraction
    actual_date = df['order_delivered_customer_date'].dt.normalize()
    estimated_date = df['order_estimated_delivery_date'].dt.normalize()
    purchase_date = df['order_purchase_timestamp'].dt.normalize()
    
    # is_late is True when the actual delivery date is strictly after estimated delivery date
    df['is_late'] = (actual_date > estimated_date).astype(bool)
    
    # Difference in days
    df['delivery_days'] = (df['order_delivered_customer_date'] - df['order_purchase_timestamp']).dt.days
    df['estimated_days'] = (df['order_estimated_delivery_date'] - df['order_purchase_timestamp']).dt.days
    
    # late_days is the difference between actual delivery date and estimated delivery date
    # (can be positive if late, or negative/zero if on time/early)
    df['late_days'] = (actual_date - estimated_date).dt.days
    
    # Validation checks
    negative_delivery = (df['delivery_days'] < 0).sum()
    negative_estimated = (df['estimated_days'] < 0).sum()
    
    if negative_delivery > 0:
        logger.warning(f"Found {negative_delivery} orders with negative delivery_days.")
    if negative_estimated > 0:
        logger.warning(f"Found {negative_estimated} orders with negative estimated_days.")
        
    logger.info(f"Delivery metrics calculated. Total orders: {len(df)}. Late rate: {df['is_late'].mean():.2%}")
    return df
