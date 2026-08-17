from .retention_metrics import calculate_retention_baseline
from .delivery_metrics import calculate_delivery_baseline
from .revenue_metrics import calculate_revenue_baseline
from utils.logger import get_logger

logger = get_logger("baseline_metrics")

def calculate_baseline_metrics(customer_summary, orders_clean, order_revenue, order_items, products, raw_orders_count=None):
    """
    Orchestrates calculation of all baseline metrics.
    """
    logger.info("Executing baseline metrics calculation suite...")
    
    retention = calculate_retention_baseline(customer_summary)
    delivery = calculate_delivery_baseline(orders_clean, raw_orders_count)
    revenue = calculate_revenue_baseline(order_revenue, orders_clean, order_items, products)
    
    # Cross validation metrics
    validation = {
        'total_customers_in_summary': len(customer_summary),
        'total_orders_in_clean': len(orders_clean),
        'total_revenue_in_agg': float(order_revenue['total_payment_value'].sum())
    }
    
    return {
        'retention': retention,
        'delivery': delivery,
        'revenue': revenue,
        'validation': validation
    }
