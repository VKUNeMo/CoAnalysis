import pandas as pd
import numpy as np
from utils.logger import get_logger

logger = get_logger("analysis.delivery")

def compute_late_rate_by_dimension(orders_clean, order_items, products, customers_df, sellers, dimension, top_n=15):
    """
    Computes late rate and average late days grouped by customer_state, product_category, or seller_id.
    """
    logger.info(f"Computing logistics metrics by dimension: {dimension}...")
    
    # 1. Start with clean delivered orders
    df = orders_clean[['order_id', 'customer_id', 'is_late', 'late_days', 'order_delivered_customer_date', 'order_estimated_delivery_date']].copy()
    
    # 2. Join depending on the dimension
    if dimension == 'customer_state':
        # Join with customers to get customer_state
        df = pd.merge(df, customers_df[['customer_id', 'customer_state']], on='customer_id', how='inner')
        group_col = 'customer_state'
    elif dimension == 'product_category':
        # Join orders with order_items, products to get product_category_name
        items_prod = pd.merge(
            order_items[['order_id', 'product_id']],
            products[['product_id', 'product_category_name']],
            on='product_id',
            how='inner'
        )
        df = pd.merge(df, items_prod, on='order_id', how='inner')
        group_col = 'product_category_name'
    elif dimension == 'seller_id':
        # Join with order_items to get seller_id
        df = pd.merge(df, order_items[['order_id', 'seller_id']].drop_duplicates(), on='order_id', how='inner')
        group_col = 'seller_id'
    else:
        raise ValueError(f"Unsupported dimension: {dimension}")
        
    # Group by the dimension
    # Filter for is_late == True only for calculating avg_late_days
    # But compute late_rate based on total delivered orders in each group
    grouped = df.groupby(group_col).agg(
        order_count=('order_id', 'count'),
        late_count=('is_late', lambda x: int(x.sum()))
    )
    
    # Calculate late rate
    grouped['late_rate'] = grouped['late_count'] / grouped['order_count']
    
    # Calculate avg late days on late orders only
    late_orders_only = df[df['is_late'] == True]
    avg_late_days_series = late_orders_only.groupby(group_col)['late_days'].mean()
    grouped['avg_late_days'] = avg_late_days_series
    grouped['avg_late_days'] = grouped['avg_late_days'].fillna(0.0)
    
    # Filter out groups with small samples to avoid statistical noise
    min_sample_size = 10
    filtered_grouped = grouped[grouped['order_count'] >= min_sample_size]
    
    # Sort by late_rate descending and take top N
    top_dimensions = filtered_grouped.sort_values('late_rate', ascending=False).head(top_n).reset_index()
    
    logger.info(f"Computed top N late rates by {dimension}. Retained {len(top_dimensions)} rows.")
    return top_dimensions

def segment_by_late_severity(orders_clean, order_reviews):
    """
    Segments delivered orders by delivery delay severity and evaluates review scores.
    """
    logger.info("Segmenting orders by late severity...")
    
    df = orders_clean[['order_id', 'late_days']].copy()
    
    # Define late severity bins
    # Note: late_days is actual - estimated
    # on_time: <= 0 days
    # late_1_7: 1 to 7 days
    # late_8_30: 8 to 30 days
    # late_30+: > 30 days
    def get_severity(days):
        if pd.isna(days):
            return 'on_time'
        if days <= 0:
            return 'on_time'
        elif days <= 7:
            return 'late_1_7'
        elif days <= 30:
            return 'late_8_30'
        else:
            return 'late_30+'
            
    df['late_severity_bin'] = df['late_days'].apply(get_severity)
    
    # Left join with order_reviews to get review_score
    df_reviews = pd.merge(df, order_reviews[['order_id', 'review_score']], on='order_id', how='left')
    
    # Group by severity bin
    grouped = df_reviews.groupby('late_severity_bin', as_index=False).agg(
        order_count=('order_id', 'count'),
        avg_review_score=('review_score', 'mean'),
        low_rating_count=('review_score', lambda x: int((x <= 3).sum())),
        total_reviews=('review_score', 'count')
    )
    
    # Calculate low rating rate (review score <= 3) on non-null reviews
    grouped['low_rating_rate'] = grouped['low_rating_count'] / grouped['total_reviews']
    grouped['low_rating_rate'] = grouped['low_rating_rate'].fillna(0.0)
    
    # Order the bins logically
    severity_order = ['on_time', 'late_1_7', 'late_8_30', 'late_30+']
    grouped['late_severity_bin'] = pd.Categorical(
        grouped['late_severity_bin'],
        categories=severity_order,
        ordered=True
    )
    grouped = grouped.sort_values('late_severity_bin').reset_index(drop=True)
    
    # Cleanup intermediate columns
    grouped = grouped.drop(columns=['low_rating_count', 'total_reviews'])
    
    logger.info("Segmentation by late severity complete.")
    return grouped

def compare_repeat_rate_by_first_order_experience(orders_raw, customers_df, customer_summary):
    """
    Evaluates repeat purchase rate based on the experience of the first order.
    """
    logger.info("Comparing repeat purchase rates based on first-order experience...")
    
    # 1. Map all raw orders to customer_unique_id
    orders_mapped = pd.merge(
        orders_raw[['order_id', 'customer_id', 'order_status', 'order_purchase_timestamp', 
                    'order_delivered_customer_date', 'order_estimated_delivery_date']],
        customers_df[['customer_id', 'customer_unique_id']],
        on='customer_id',
        how='inner'
    )
    
    orders_mapped['order_purchase_timestamp'] = pd.to_datetime(orders_mapped['order_purchase_timestamp'])
    orders_mapped['order_delivered_customer_date'] = pd.to_datetime(orders_mapped['order_delivered_customer_date'])
    orders_mapped['order_estimated_delivery_date'] = pd.to_datetime(orders_mapped['order_estimated_delivery_date'])
    
    # Find first order for each unique customer
    first_orders = orders_mapped.loc[orders_mapped.groupby('customer_unique_id')['order_purchase_timestamp'].idxmin()].copy()
    
    # Determine experience of the first order
    # canceled: status is canceled
    # late: status delivered, and actual > estimated
    # on_time: default on-time experience
    def determine_experience(row):
        if row['order_status'] == 'canceled':
            return 'canceled'
        # Check if actual date and estimated date are valid for late evaluation
        if pd.notna(row['order_delivered_customer_date']) and pd.notna(row['order_estimated_delivery_date']):
            # Compare at date level
            if row['order_delivered_customer_date'].date() > row['order_estimated_delivery_date'].date():
                return 'late'
        return 'on_time'
        
    first_orders['first_order_experience'] = first_orders.apply(determine_experience, axis=1)
    
    # Merge first order experience with customer_summary to get repeat purchase flag
    comparison_df = pd.merge(
        customer_summary[['customer_unique_id', 'is_repeat']],
        first_orders[['customer_unique_id', 'first_order_experience']],
        on='customer_unique_id',
        how='inner'
    )
    
    # Group by first_order_experience
    grouped = comparison_df.groupby('first_order_experience', as_index=False).agg(
        customer_count=('customer_unique_id', 'count'),
        repeat_customer_count=('is_repeat', lambda x: int(x.sum()))
    )
    
    grouped['repeat_rate'] = (grouped['repeat_customer_count'] / grouped['customer_count']) * 100.0
    
    logger.info("First-order experience repeat rate comparison computed.")
    return grouped
