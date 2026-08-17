import pandas as pd
import logging
from src.data_loading.memory_monitor import check_usage

logger = logging.getLogger("churn_prediction.data_loading.merger")

def merge_to_customer_level(dfs, cutoff_date=None, memory_threshold=6.0):
    """
    Merge 9 Olist tables into a customer-level dataframe with memory monitoring.
    If cutoff_date is provided, only orders placed on or before cutoff_date are included
    to prevent look-ahead data leakage.
    """
    diagnostics = {}
    
    # 1. Extract individual dataframes
    orders = dfs['orders']
    customers = dfs['customers']
    order_items = dfs['order_items']
    payments = dfs['order_payments']
    reviews = dfs['order_reviews']
    products = dfs['products']
    sellers = dfs['sellers']
    geolocation = dfs['geolocation']
    translation = dfs['translation']
    
    diagnostics['raw_orders_rows'] = len(orders)
    diagnostics['raw_customers_rows'] = len(customers)
    
    # 2. Merge customers and orders (left join on customer_id)
    # This associates each order with the customer_unique_id
    orders_cust = pd.merge(orders, customers, on='customer_id', how='left')
    check_usage(orders_cust, threshold_gb=memory_threshold)
    diagnostics['orders_cust_rows'] = len(orders_cust)
    
    # Apply cutoff if provided
    if cutoff_date is not None:
        cutoff_dt = pd.to_datetime(cutoff_date)
        orders_cust = orders_cust[orders_cust['order_purchase_timestamp'] <= cutoff_dt]
        logger.info(f"Filtered orders by cutoff date <= {cutoff_date}. Remaining orders: {len(orders_cust)}")
        diagnostics['filtered_orders_rows'] = len(orders_cust)
    
    # 3. Aggregate order details per customer_unique_id
    # We will build customer-level base features from here
    # total_orders: count of order_id
    # last_order_date: max of order_purchase_timestamp
    # first_order_date: min of order_purchase_timestamp
    cust_orders_agg = orders_cust.groupby('customer_unique_id').agg(
        total_orders=('order_id', 'nunique'),
        last_order_date=('order_purchase_timestamp', 'max'),
        first_order_date=('order_purchase_timestamp', 'min')
    ).reset_index()
    
    # Filter out customers with no orders in this period
    cust_orders_agg = cust_orders_agg[cust_orders_agg['total_orders'] > 0]
    diagnostics['unique_customers_with_orders'] = len(cust_orders_agg)
    
    # 4. Integrate items and compute revenue
    # Map orders_cust to items
    items_merged = pd.merge(order_items, orders_cust[['order_id', 'customer_unique_id']], on='order_id', how='inner')
    cust_revenue = items_merged.groupby('customer_unique_id').agg(
        total_revenue=('price', 'sum'),
        total_freight=('freight_value', 'sum'),
        total_items=('order_item_id', 'count')
    ).reset_index()
    
    # Join with base customer df
    customer_df = pd.merge(cust_orders_agg, cust_revenue, on='customer_unique_id', how='left')
    customer_df['total_revenue'] = customer_df['total_revenue'].fillna(0.0).astype('float32')
    customer_df['total_freight'] = customer_df['total_freight'].fillna(0.0).astype('float32')
    customer_df['total_items'] = customer_df['total_items'].fillna(0).astype('int32')
    
    # 5. Integrate reviews
    reviews_merged = pd.merge(reviews, orders_cust[['order_id', 'customer_unique_id']], on='order_id', how='inner')
    cust_reviews = reviews_merged.groupby('customer_unique_id').agg(
        avg_review_score=('review_score', 'mean')
    ).reset_index()
    customer_df = pd.merge(customer_df, cust_reviews, on='customer_unique_id', how='left')
    customer_df['avg_review_score'] = customer_df['avg_review_score'].fillna(5.0).astype('float32') # Fallback to 5.0 (neutral/good)
    
    # 6. Include customer state and city metadata (take first/most recent state/city)
    cust_meta = orders_cust.sort_values('order_purchase_timestamp').groupby('customer_unique_id').first()[['customer_state', 'customer_city']].reset_index()
    customer_df = pd.merge(customer_df, cust_meta, on='customer_unique_id', how='left')
    
    # 7. Aggregate geolocation coordinates to unique zip prefix to save memory
    logger.info("Aggregating geolocation coordinates...")
    geo_agg = geolocation.groupby('geolocation_zip_code_prefix').agg(
        lat=('geolocation_lat', 'mean'),
        lng=('geolocation_lng', 'mean')
    ).reset_index()
    
    # Map zip code prefix to customer state and city coordinates
    # We need to map customer coordinates for geospatial features
    cust_zip = orders_cust.sort_values('order_purchase_timestamp').groupby('customer_unique_id').first()[['customer_zip_code_prefix']].reset_index()
    customer_df = pd.merge(customer_df, cust_zip, on='customer_unique_id', how='left')
    
    customer_df = pd.merge(
        customer_df,
        geo_agg.rename(columns={'geolocation_zip_code_prefix': 'customer_zip_code_prefix', 'lat': 'customer_lat', 'lng': 'customer_lng'}),
        on='customer_zip_code_prefix',
        how='left'
    )
    
    # Downcast and clean types to save memory
    customer_df['total_orders'] = customer_df['total_orders'].astype('int32')
    customer_df['customer_lat'] = customer_df['customer_lat'].astype('float32')
    customer_df['customer_lng'] = customer_df['customer_lng'].astype('float32')
    
    # Final check
    check_usage(customer_df, threshold_gb=memory_threshold)
    diagnostics['final_customer_df_rows'] = len(customer_df)
    
    logger.info(f"Merged customer-level dataframe shape: {customer_df.shape}")
    
    return customer_df, diagnostics
