import pandas as pd
from utils.logger import get_logger

logger = get_logger("data_preparation.datetime_normalizer")

def normalize_timestamps(orders_df):
    """
    Parses datetime columns, filters for delivered orders, and ensures both actual
    and estimated delivery dates are present.
    """
    logger.info("Normalizing orders timestamps and filtering delivered orders...")
    total_raw_orders = len(orders_df)
    
    # Create a copy to prevent SettingWithCopyWarning
    df = orders_df.copy()
    
    # Parse columns to datetime
    timestamp_cols = [
        'order_purchase_timestamp', 
        'order_estimated_delivery_date', 
        'order_delivered_customer_date'
    ]
    
    for col in timestamp_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        
    # Filter: order_status == 'delivered'
    df_delivered = df[df['order_status'] == 'delivered']
    dropped_status = total_raw_orders - len(df_delivered)
    logger.info(f"Filtered out {dropped_status} orders with status other than 'delivered'.")
    
    # Filter: actual and estimated delivery dates are not null
    df_clean = df_delivered[
        df_delivered['order_estimated_delivery_date'].notna() & 
        df_delivered['order_delivered_customer_date'].notna()
    ]
    dropped_nulls = len(df_delivered) - len(df_clean)
    logger.info(f"Filtered out {dropped_nulls} delivered orders due to missing delivery/estimated timestamps.")
    
    logger.info(f"Normalisation complete. Returned {len(df_clean)} orders.")
    return df_clean
