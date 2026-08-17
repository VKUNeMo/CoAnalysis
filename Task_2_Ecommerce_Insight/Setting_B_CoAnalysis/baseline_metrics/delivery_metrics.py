import pandas as pd
from utils.logger import get_logger

logger = get_logger("baseline_metrics.delivery")

def calculate_delivery_baseline(orders_clean, raw_orders_count=None):
    """
    Calculates overall logistics metrics on clean delivered orders.
    """
    logger.info("Calculating baseline delivery metrics...")
    
    total_delivered = len(orders_clean)
    if total_delivered == 0:
        return {
            'late_rate': 0.0,
            'avg_late_days': 0.0,
            'late_count': 0,
            'on_time_count': 0,
            'excluded_count': 0
        }
        
    late_orders = orders_clean[orders_clean['is_late'] == True]
    late_count = len(late_orders)
    on_time_count = total_delivered - late_count
    
    late_rate = (late_count / total_delivered) * 100.0
    
    # Calculate avg late days on late orders
    # We normalized dates previously, so we use actual_date - estimated_date
    actual_date = late_orders['order_delivered_customer_date'].dt.normalize()
    estimated_date = late_orders['order_estimated_delivery_date'].dt.normalize()
    late_days = (actual_date - estimated_date).dt.days
    avg_late_days = float(late_days.mean()) if late_count > 0 else 0.0
    
    excluded_count = (raw_orders_count - total_delivered) if raw_orders_count is not None else 0
    
    logger.info(
        f"Delivery baseline: Late Rate={late_rate:.2f}%, "
        f"Avg Late Days={avg_late_days:.1f} days (on late orders)."
    )
    
    return {
        'late_rate': late_rate,
        'avg_late_days': avg_late_days,
        'late_count': late_count,
        'on_time_count': on_time_count,
        'excluded_count': excluded_count
    }
