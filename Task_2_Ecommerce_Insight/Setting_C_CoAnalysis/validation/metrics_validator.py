import pandas as pd
from utils.logger import get_logger

logger = get_logger("validation.metrics")

def validate_customer_unique_id_count(customer_summary, customers_raw, orders_clean):
    """
    Validates that the unique customer_unique_id count in customer_summary matches
    the count of customer_unique_ids in the clean orders dataset.
    """
    logger.info("Validating customer unique ID counts...")
    
    # Expected: unique customer_unique_ids from orders_clean merged with customers_raw
    clean_mapped = pd.merge(
        orders_clean[['customer_id']],
        customers_raw[['customer_id', 'customer_unique_id']],
        on='customer_id',
        how='inner'
    )
    expected_count = clean_mapped['customer_unique_id'].nunique()
    actual_count = customer_summary['customer_unique_id'].nunique()
    
    delta = expected_count - actual_count
    is_valid = (delta == 0)
    
    if is_valid:
        logger.info(f"Customer unique ID validation passed: {actual_count} unique customers.")
    else:
        logger.error(f"Customer unique ID validation failed! Expected: {expected_count}, Actual: {actual_count}, Delta: {delta}")
        
    return {
        'expected_count': int(expected_count),
        'actual_count': int(actual_count),
        'delta': int(delta),
        'is_valid': bool(is_valid)
    }

def validate_revenue_totals(order_revenue, order_payments_raw, orders_clean):
    """
    Validates that total revenue matches between the aggregated order_revenue table and the raw order_payments table.
    Only concerns orders present in orders_clean.
    """
    logger.info("Validating revenue totals...")
    
    # Focus on clean delivered orders
    clean_order_ids = orders_clean['order_id']
    
    # Expected: sum of payments in raw order_payments for delivered orders
    raw_payments_delivered = order_payments_raw[order_payments_raw['order_id'].isin(clean_order_ids)]
    # Convert negatives if any were converted in aggregation
    raw_vals = raw_payments_delivered['payment_value'].copy()
    raw_vals[raw_vals < 0] = 0.0
    expected_revenue = float(raw_vals.sum())
    
    # Actual: sum of total_payment_value in order_revenue for delivered orders
    actual_revenue = float(order_revenue[order_revenue['order_id'].isin(clean_order_ids)]['total_payment_value'].sum())
    
    delta_abs = abs(expected_revenue - actual_revenue)
    delta_pct = (delta_abs / expected_revenue * 100.0) if expected_revenue > 0 else 0.0
    is_valid = (delta_abs < 0.05)  # Tolerance of 5 cents due to float precision
    
    if is_valid:
        logger.info(f"Revenue validation passed: Total Revenue = {actual_revenue:.2f} BRL.")
    else:
        logger.error(
            f"Revenue validation failed! Expected: {expected_revenue:.2f}, Actual: {actual_revenue:.2f}, "
            f"Delta Abs: {delta_abs:.4f}, Delta Pct: {delta_pct:.4%}"
        )
        
    return {
        'expected_revenue': expected_revenue,
        'actual_revenue': actual_revenue,
        'delta_abs': delta_abs,
        'delta_pct': delta_pct,
        'is_valid': bool(is_valid)
    }

def validate_late_delivery_rate(orders_clean):
    """
    Validates that the late delivery rate calculation matches logic invariants.
    """
    logger.info("Validating late delivery rate calculation...")
    
    # Invariant: all clean orders must be 'delivered' and have both delivery actual and estimated timestamps
    total_clean = len(orders_clean)
    
    # Count of late orders
    late_count = int(orders_clean['is_late'].sum())
    late_rate = (late_count / total_clean) if total_clean > 0 else 0.0
    
    # Verify is_late logic: actual date > estimated date
    actual_date = orders_clean['order_delivered_customer_date'].dt.normalize()
    estimated_date = orders_clean['order_estimated_delivery_date'].dt.normalize()
    incorrect_labels = ((orders_clean['is_late'] == True) & (actual_date <= estimated_date)).sum()
    incorrect_labels += ((orders_clean['is_late'] == False) & (actual_date > estimated_date)).sum()
    
    is_valid = (incorrect_labels == 0)
    
    if is_valid:
        logger.info(f"Late delivery rate validation passed. Rate: {late_rate:.2%}.")
    else:
        logger.error(f"Late delivery rate validation failed! Found {incorrect_labels} incorrectly labeled orders.")
        
    return {
        'total_delivered_with_timestamps': int(total_clean),
        'late_count': int(late_count),
        'late_rate': float(late_rate),
        'incorrect_labels': int(incorrect_labels),
        'is_valid': bool(is_valid)
    }
