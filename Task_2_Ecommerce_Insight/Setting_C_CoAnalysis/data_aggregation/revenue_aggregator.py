import pandas as pd
from utils.logger import get_logger

logger = get_logger("data_aggregation.revenue_aggregator")

def aggregate_revenue(order_payments, order_items=None):
    """
    Aggregates payment values by order_id, and optionally integrates product and
    freight values from order_items.
    """
    logger.info("Aggregating order payments...")
    
    # Check for negative payments
    neg_payments = (order_payments['payment_value'] < 0).sum()
    if neg_payments > 0:
        logger.warning(f"Found {neg_payments} negative payment values. Converting to 0.")
        order_payments = order_payments.copy()
        order_payments.loc[order_payments['payment_value'] < 0, 'payment_value'] = 0.0
        
    # Group by order_id and sum payment_value
    payment_agg = order_payments.groupby('order_id', as_index=False).agg({
        'payment_value': 'sum'
    }).rename(columns={'payment_value': 'total_payment_value'})
    
    # Calculate difference to ensure integrity
    diff = abs(payment_agg['total_payment_value'].sum() - order_payments['payment_value'].sum())
    if diff > 0.05:
        logger.warning(f"Payment aggregation sum delta is {diff:.4f} BRL (expected ~0).")
    else:
        logger.info("Payment aggregation verification passed.")
        
    # Add product_value and freight_value from order_items if provided
    if order_items is not None:
        logger.info("Aggregating product and freight values from order_items...")
        items_agg = order_items.groupby('order_id', as_index=False).agg({
            'price': 'sum',
            'freight_value': 'sum'
        }).rename(columns={'price': 'product_value'})
        
        # Merge payments and items
        order_revenue = pd.merge(payment_agg, items_agg, on='order_id', how='outer')
        order_revenue['total_payment_value'] = order_revenue['total_payment_value'].fillna(0.0)
        order_revenue['product_value'] = order_revenue['product_value'].fillna(0.0)
        order_revenue['freight_value'] = order_revenue['freight_value'].fillna(0.0)
    else:
        order_revenue = payment_agg
        order_revenue['product_value'] = order_revenue['total_payment_value']
        order_revenue['freight_value'] = 0.0
        
    logger.info(f"Revenue aggregated. Total orders in revenue table: {len(order_revenue)}")
    return order_revenue
