from .metrics_validator import (
    validate_customer_unique_id_count,
    validate_revenue_totals,
    validate_late_delivery_rate
)
from .baseline_comparator import (
    compare_cohort_retention_vs_baseline,
    compare_risk_segmentation_vs_baseline,
    compare_revenue_decomposition_vs_baseline
)
from .traceability_checker import (
    build_traceability_matrix,
    classify_recommendations
)
from utils.logger import get_logger

logger = get_logger("validation")

def run_validation(customer_summary, order_revenue, orders_clean, customers_raw, order_payments_raw,
                   retention_details, first_experience_retention, rev_by_category, monthly_rev_trend,
                   baseline_metrics, recommendations, insights):
    """
    Main entry point for pipeline validation.
    Runs all data audits, statistical significance checks, and traceability matrix builds.
    """
    logger.info("Executing comprehensive pipeline validation...")
    
    # 1. Audits (Metrics Validator)
    cust_audit = validate_customer_unique_id_count(customer_summary, customers_raw, orders_clean)
    rev_audit = validate_revenue_totals(order_revenue, order_payments_raw, orders_clean)
    delivery_audit = validate_late_delivery_rate(orders_clean)
    
    # 2. Significance Comparisons (Baseline Comparator)
    cohort_comparison = compare_cohort_retention_vs_baseline(
        retention_details, 
        baseline_metrics['retention']['repeat_rate'] / 100.0
    )
    risk_comparison = compare_risk_segmentation_vs_baseline(
        first_experience_retention, 
        baseline_metrics['delivery']['late_rate'] / 100.0
    )
    rev_comparison = compare_revenue_decomposition_vs_baseline(
        rev_by_category, 
        monthly_rev_trend
    )
    
    # 3. Traceability checker (Traceability Checker)
    traceability_matrix = build_traceability_matrix(recommendations, insights)
    recommendation_classification = classify_recommendations(traceability_matrix, recommendations)
    
    # Calculate overall pipeline status
    is_metrics_valid = cust_audit['is_valid'] and rev_audit['is_valid'] and delivery_audit['is_valid']
    
    if not is_metrics_valid:
        overall_status = 'FAIL'
    elif not recommendation_classification['qualified']:
        overall_status = 'WARNING'
    else:
        overall_status = 'PASS'
        
    logger.info(f"Pipeline validation complete. Status: {overall_status}")
    
    return {
        'overall_status': overall_status,
        'metrics_validation': {
            'customer_audit': cust_audit,
            'revenue_audit': rev_audit,
            'delivery_audit': delivery_audit
        },
        'baseline_comparison': {
            'cohort': cohort_comparison,
            'risk': risk_comparison,
            'revenue': rev_comparison
        },
        'traceability': {
            'matrix': traceability_matrix,
            'classification': recommendation_classification
        }
    }
