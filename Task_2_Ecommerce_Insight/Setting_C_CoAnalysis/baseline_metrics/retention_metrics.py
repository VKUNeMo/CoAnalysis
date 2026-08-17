import pandas as pd
from utils.logger import get_logger

logger = get_logger("baseline_metrics.retention")

def calculate_retention_baseline(customer_summary):
    """
    Calculates baseline customer retention metrics: repeat rate and repurchase time.
    """
    logger.info("Calculating baseline retention metrics...")
    
    total_customers = len(customer_summary)
    if total_customers == 0:
        return {
            'repeat_rate': 0.0,
            'avg_repurchase_days': 0.0,
            'one_time_count': 0,
            'repeat_count': 0
        }
        
    repeat_customers = customer_summary[customer_summary['is_repeat'] == True]
    repeat_count = len(repeat_customers)
    one_time_count = total_customers - repeat_count
    
    repeat_rate = (repeat_count / total_customers) * 100.0
    
    # Calculate average repurchase days (time between first and last order) on repeat buyers
    # (first_order_date and last_order_date are already date normalized pd.Timestamps)
    if repeat_count > 0:
        repurchase_days = (repeat_customers['last_order_date'] - repeat_customers['first_order_date']).dt.days
        avg_repurchase_days = float(repurchase_days.mean())
    else:
        avg_repurchase_days = 0.0
        
    logger.info(
        f"Retention baseline: Repeat Rate={repeat_rate:.2f}%, "
        f"Avg Repurchase Time={avg_repurchase_days:.1f} days (on repeat buyers)."
    )
    
    return {
        'repeat_rate': repeat_rate,
        'avg_repurchase_days': avg_repurchase_days,
        'one_time_count': one_time_count,
        'repeat_count': repeat_count
    }
