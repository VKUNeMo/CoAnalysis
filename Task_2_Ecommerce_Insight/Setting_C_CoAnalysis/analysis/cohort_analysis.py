import pandas as pd
import numpy as np
from utils.logger import get_logger

logger = get_logger("analysis.cohort")

def compute_cohort_retention_matrix(customer_summary, orders_clean, customers_df):
    """
    Computes cohort retention matrix based on first purchase month.
    """
    logger.info("Computing cohort retention matrix...")
    
    # Map orders_clean to customer_unique_id
    orders_with_unique = pd.merge(
        orders_clean[['order_id', 'customer_id', 'order_purchase_timestamp']],
        customers_df[['customer_id', 'customer_unique_id']],
        on='customer_id',
        how='left'
    )
    
    # Merge with customer_summary to get first_order_date
    df = pd.merge(
        orders_with_unique,
        customer_summary[['customer_unique_id', 'first_order_date']],
        on='customer_unique_id',
        how='inner'
    )
    
    # Ensure datetimes
    df['first_order_date'] = pd.to_datetime(df['first_order_date'])
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    
    df['cohort_month'] = df['first_order_date'].dt.to_period('M')
    df['order_month'] = df['order_purchase_timestamp'].dt.to_period('M')
    
    # Calculate age in months: difference in periods
    df['age_month'] = (df['order_month'].dt.year - df['cohort_month'].dt.year) * 12 + (df['order_month'].dt.month - df['cohort_month'].dt.month)
    
    # Cohort size (total unique customers in each cohort)
    cohort_sizes = customer_summary.copy()
    cohort_sizes['cohort_month'] = pd.to_datetime(cohort_sizes['first_order_date']).dt.to_period('M')
    cohort_size_map = cohort_sizes.groupby('cohort_month')['customer_unique_id'].nunique().to_dict()
    
    # Group by cohort_month and age_month to get unique customer count
    cohort_grouped = df.groupby(['cohort_month', 'age_month'], as_index=False).agg({
        'customer_unique_id': 'nunique'
    }).rename(columns={'customer_unique_id': 'active_customers'})
    
    # Add cohort size
    cohort_grouped['cohort_size'] = cohort_grouped['cohort_month'].map(cohort_size_map)
    cohort_grouped['retention_rate'] = cohort_grouped['active_customers'] / cohort_grouped['cohort_size']
    
    # Pivot matrix
    retention_pivot = cohort_grouped.pivot(
        index='cohort_month', 
        columns='age_month', 
        values='retention_rate'
    ).fillna(0.0)
    
    # Also return details
    cohort_grouped_serializable = cohort_grouped.copy()
    cohort_grouped_serializable['cohort_month'] = cohort_grouped_serializable['cohort_month'].astype(str)
    
    retention_pivot.index = retention_pivot.index.astype(str)
    
    logger.info(f"Cohort retention matrix computed. Size: {retention_pivot.shape}")
    return retention_pivot, cohort_grouped_serializable

def compute_clv_by_cohort(customer_summary, order_revenue, orders_clean, customers_df):
    """
    Computes Customer Lifetime Value (CLV) stats grouped by cohort.
    """
    logger.info("Computing cohort CLV...")
    
    # Join orders_clean with customer unique id and order_revenue
    orders_with_unique = pd.merge(
        orders_clean[['order_id', 'customer_id']],
        customers_df[['customer_id', 'customer_unique_id']],
        on='customer_id',
        how='left'
    )
    
    orders_rev = pd.merge(
        orders_with_unique,
        order_revenue[['order_id', 'total_payment_value']],
        on='order_id',
        how='inner'
    )
    
    # Group by customer_unique_id to get total lifetime value per buyer
    customer_clv = orders_rev.groupby('customer_unique_id', as_index=False).agg({
        'total_payment_value': 'sum'
    }).rename(columns={'total_payment_value': 'lifetime_revenue'})
    
    # Merge with customer_summary to get first order cohort
    df = pd.merge(
        customer_clv,
        customer_summary[['customer_unique_id', 'first_order_date']],
        on='customer_unique_id',
        how='inner'
    )
    
    df['cohort_month'] = pd.to_datetime(df['first_order_date']).dt.to_period('M')
    
    # Group by cohort_month and compute stats
    cohort_clv_summary = df.groupby('cohort_month', as_index=False).agg(
        cohort_size=('customer_unique_id', 'count'),
        mean_clv=('lifetime_revenue', 'mean'),
        median_clv=('lifetime_revenue', 'median'),
        p90_clv=('lifetime_revenue', lambda x: np.percentile(x, 90))
    )
    
    cohort_clv_summary = cohort_clv_summary.sort_values('cohort_month').reset_index(drop=True)
    cohort_clv_summary['cohort_month'] = cohort_clv_summary['cohort_month'].astype(str)
    
    logger.info(f"Cohort CLV summary computed. Number of cohorts: {len(cohort_clv_summary)}")
    return cohort_clv_summary

def compute_customer_order_distribution(customer_summary):
    """
    Calculates the distribution of customers by their total number of orders.
    """
    logger.info("Computing customer order distribution buckets...")
    
    total_customers = len(customer_summary)
    if total_customers == 0:
        return pd.DataFrame()
        
    # Bucket order count
    def bucket_order(count):
        if count == 1:
            return "1 order"
        elif count == 2:
            return "2 orders"
        else:
            return "3+ orders"
            
    df = customer_summary.copy()
    df['order_count_bin'] = df['order_count'].apply(bucket_order)
    
    dist = df.groupby('order_count_bin', as_index=False).agg({
        'customer_unique_id': 'count'
    }).rename(columns={'customer_unique_id': 'customer_count'})
    
    # Ensure ordered categories: 1 order, 2 orders, 3+ orders
    dist['order_count_bin'] = pd.Categorical(
        dist['order_count_bin'], 
        categories=["1 order", "2 orders", "3+ orders"], 
        ordered=True
    )
    dist = dist.sort_values('order_count_bin').reset_index(drop=True)
    
    dist['percentage'] = (dist['customer_count'] / total_customers) * 100.0
    dist['cumulative_percentage'] = dist['percentage'].cumsum()
    
    logger.info("Customer order distribution computed successfully.")
    return dist

def compute_repeat_purchase_time(orders_clean, customer_summary, customers_df):
    """
    Calculates repurchase time intervals for repeat customers.
    """
    logger.info("Computing repurchase time intervals...")
    
    # Filter repeat buyers
    repeat_cust_ids = customer_summary[customer_summary['is_repeat'] == True]['customer_unique_id']
    
    # Map orders_clean to customer_unique_id
    orders_with_unique = pd.merge(
        orders_clean[['order_id', 'customer_id', 'order_purchase_timestamp']],
        customers_df[['customer_id', 'customer_unique_id']],
        on='customer_id',
        how='inner'
    )
    
    # Filter for repeat buyers only
    repeat_orders = orders_with_unique[orders_with_unique['customer_unique_id'].isin(repeat_cust_ids)].copy()
    
    # Sort by customer_unique_id and timestamp
    repeat_orders = repeat_orders.sort_values(['customer_unique_id', 'order_purchase_timestamp'])
    
    # Compute diff between consecutive orders per customer
    repeat_orders['prev_purchase'] = repeat_orders.groupby('customer_unique_id')['order_purchase_timestamp'].shift(1)
    repeat_orders['days_to_next'] = (repeat_orders['order_purchase_timestamp'] - repeat_orders['prev_purchase']).dt.days
    
    # Drop first orders (which have NaN days_to_next)
    intervals = repeat_orders.dropna(subset=['days_to_next'])
    
    # Group by customer to find their average repurchase days
    customer_intervals = intervals.groupby('customer_unique_id', as_index=False).agg({
        'days_to_next': ['mean', 'median']
    })
    customer_intervals.columns = ['customer_unique_id', 'mean_days_between_orders', 'median_days_between_orders']
    
    # Aggregate statistics
    if len(intervals) > 0:
        overall_stats = pd.DataFrame([{
            'metric': 'Repurchase Interval (Days)',
            'overall_mean': float(intervals['days_to_next'].mean()),
            'overall_median': float(intervals['days_to_next'].median()),
            'p25': float(intervals['days_to_next'].quantile(0.25)),
            'p75': float(intervals['days_to_next'].quantile(0.75))
        }])
    else:
        overall_stats = pd.DataFrame()
        
    logger.info(f"Repurchase time intervals calculated for {len(customer_intervals)} buyers.")
    return customer_intervals, overall_stats
