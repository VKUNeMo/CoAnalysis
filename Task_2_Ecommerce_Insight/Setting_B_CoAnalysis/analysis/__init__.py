from .cohort_analysis import (
    compute_cohort_retention_matrix,
    compute_clv_by_cohort,
    compute_customer_order_distribution,
    compute_repeat_purchase_time
)
from .delivery_analysis import (
    compute_late_rate_by_dimension,
    segment_by_late_severity,
    compare_repeat_rate_by_first_order_experience
)
from .revenue_analysis import (
    compute_revenue_trend_by_month,
    compute_revenue_by_dimension,
    compute_controlled_correlation_matrix
)
from utils.logger import get_logger

logger = get_logger("analysis")

def run_multidimensional_analysis(customer_summary, orders_clean, order_revenue, order_items, products, customers_df, sellers, order_reviews, orders_raw, order_payments_raw):
    """
    Executes all multi-dimensional analysis functions.
    """
    logger.info("Executing multi-dimensional analysis suite...")
    
    # 1. Cohort and Retention axis
    retention_matrix, retention_details = compute_cohort_retention_matrix(customer_summary, orders_clean, customers_df)
    cohort_clv = compute_clv_by_cohort(customer_summary, order_revenue, orders_clean, customers_df)
    customer_dist = compute_customer_order_distribution(customer_summary)
    repurchase_intervals, repurchase_stats = compute_repeat_purchase_time(orders_clean, customer_summary, customers_df)
    
    # 2. Logistics/Delivery axis
    late_by_state = compute_late_rate_by_dimension(orders_clean, order_items, products, customers_df, sellers, 'customer_state')
    late_by_category = compute_late_rate_by_dimension(orders_clean, order_items, products, customers_df, sellers, 'product_category')
    late_by_seller = compute_late_rate_by_dimension(orders_clean, order_items, products, customers_df, sellers, 'seller_id')
    late_severity_reviews = segment_by_late_severity(orders_clean, order_reviews)
    first_experience_retention = compare_repeat_rate_by_first_order_experience(orders_raw, customers_df, customer_summary)
    
    # 3. Revenue axis
    monthly_rev_trend = compute_revenue_trend_by_month(order_revenue, orders_clean)
    rev_by_state = compute_revenue_by_dimension(order_revenue, orders_clean, order_items, products, customers_df, 'customer_state')
    rev_by_category = compute_revenue_by_dimension(order_revenue, orders_clean, order_items, products, customers_df, 'product_category')
    rev_by_payment_type = compute_revenue_by_dimension(order_payments_raw, orders_clean, order_items, products, customers_df, 'payment_type')
    
    # 4. Controlled Correlation Analysis
    corr_matrix, p_matrix, correlation_sample_size = compute_controlled_correlation_matrix(
        orders_clean, order_revenue, order_reviews, customer_summary, customers_df, products, order_items
    )
    
    logger.info("Multi-dimensional analysis suite complete.")
    
    return {
        'retention_matrix': retention_matrix,
        'retention_details': retention_details,
        'cohort_clv': cohort_clv,
        'customer_dist': customer_dist,
        'repurchase_intervals': repurchase_intervals,
        'repurchase_stats': repurchase_stats,
        'late_by_state': late_by_state,
        'late_by_category': late_by_category,
        'late_by_seller': late_by_seller,
        'late_severity_reviews': late_severity_reviews,
        'first_experience_retention': first_experience_retention,
        'monthly_rev_trend': monthly_rev_trend,
        'rev_by_state': rev_by_state,
        'rev_by_category': rev_by_category,
        'rev_by_payment_type': rev_by_payment_type,
        'corr_matrix': corr_matrix,
        'p_matrix': p_matrix,
        'correlation_sample_size': correlation_sample_size
    }
