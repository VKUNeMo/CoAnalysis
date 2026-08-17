import pandas as pd
from utils.logger import get_logger

logger = get_logger("data_aggregation.customer_aggregator")

def aggregate_customers(orders_clean, customers_df, order_revenue):
    """
    Creates customer_summary by mapping orders to customer_unique_id and grouping.
    """
    logger.info("Aggregating customer metrics by customer_unique_id...")
    
    # Merge orders_clean with customers to map customer_id to customer_unique_id
    orders_with_cust = pd.merge(
        orders_clean,
        customers_df[['customer_id', 'customer_unique_id']],
        on='customer_id',
        how='left'
    )
    
    # Check for missing customer mappings
    missing_cust = orders_with_cust['customer_unique_id'].isna().sum()
    if missing_cust > 0:
        logger.warning(f"Found {missing_cust} orders without mapping to customer_unique_id.")
        
    # Merge with order_revenue
    orders_full = pd.merge(
        orders_with_cust,
        order_revenue[['order_id', 'total_payment_value']],
        on='order_id',
        how='left'
    )
    orders_full['total_payment_value'] = orders_full['total_payment_value'].fillna(0.0)
    
    # Group by customer_unique_id
    cust_group = orders_full.groupby('customer_unique_id', as_index=False)
    
    customer_summary = cust_group.agg(
        order_count=('order_id', 'count'),
        total_revenue=('total_payment_value', 'sum'),
        first_order_date=('order_purchase_timestamp', 'min'),
        last_order_date=('order_purchase_timestamp', 'max')
    )
    
    customer_summary['is_repeat'] = customer_summary['order_count'] >= 2
    
    # Normalize dates to date-level for safety
    customer_summary['first_order_date'] = customer_summary['first_order_date'].dt.normalize()
    customer_summary['last_order_date'] = customer_summary['last_order_date'].dt.normalize()
    
    logger.info(
        f"Customer aggregation complete. Unique customers: {len(customer_summary)}, "
        f"Repeat customer count: {customer_summary['is_repeat'].sum()} "
        f"({customer_summary['is_repeat'].mean():.2%})"
    )
    return customer_summary
