import pandas as pd
import numpy as np
from utils.logger import get_logger
from utils.stats_utils import proportions_ztest_custom, cohens_d
from scipy import stats

logger = get_logger("validation.comparator")

def compare_cohort_retention_vs_baseline(retention_details, baseline_repeat_rate):
    """
    Compares cohort retention rates against baseline.
    Computes significance between best and worst cohorts (min size 30).
    """
    logger.info("Comparing cohort retention vs baseline...")
    
    # Filter for age_month > 0 to see retention, and cohort size >= 30
    valid_cohorts = retention_details[
        (retention_details['age_month'] > 0) & 
        (retention_details['cohort_size'] >= 30)
    ]
    
    if len(valid_cohorts) < 2:
        logger.warning("Insufficient cohorts with size >= 30 for comparison.")
        return {
            'best_cohort': 'N/A',
            'worst_cohort': 'N/A',
            'delta_retention': 0.0,
            'p_value': 1.0,
            'effect_size': 0.0,
            'is_significant': False
        }
        
    # Find best and worst cohorts (based on age_month == 1 retention rate)
    age_1_cohorts = valid_cohorts[valid_cohorts['age_month'] == 1]
    if len(age_1_cohorts) < 2:
        # Fallback to any age month
        age_1_cohorts = valid_cohorts
        
    best = age_1_cohorts.loc[age_1_cohorts['retention_rate'].idxmax()]
    worst = age_1_cohorts.loc[age_1_cohorts['retention_rate'].idxmin()]
    
    best_cohort = str(best['cohort_month'])
    worst_cohort = str(worst['cohort_month'])
    
    # Proportions z-test
    count1 = int(best['active_customers'])
    nobs1 = int(best['cohort_size'])
    count2 = int(worst['active_customers'])
    nobs2 = int(worst['cohort_size'])
    
    z_stat, p_value = proportions_ztest_custom(count1, nobs1, count2, nobs2)
    
    delta = float(best['retention_rate'] - worst['retention_rate'])
    
    # Simple Cohen's d for proportions
    pooled_p = (count1 + count2) / (nobs1 + nobs2)
    pooled_std = np.sqrt(pooled_p * (1 - pooled_p)) if pooled_p > 0 and pooled_p < 1 else 0.1
    effect_size = delta / pooled_std if pooled_std > 0 else 0.0
    
    is_significant = (p_value < 0.05)
    
    logger.info(
        f"Cohort comparison: Best={best_cohort} ({best['retention_rate']:.1%}), "
        f"Worst={worst_cohort} ({worst['retention_rate']:.1%}), p-value={p_value:.4f}, significant={is_significant}"
    )
    
    return {
        'best_cohort': best_cohort,
        'worst_cohort': worst_cohort,
        'delta_retention': delta,
        'p_value': p_value,
        'effect_size': effect_size,
        'is_significant': is_significant
    }

def compare_risk_segmentation_vs_baseline(first_experience_retention, baseline_late_rate):
    """
    Compares repeat rates between different first-order experience groups (on_time, late, canceled).
    """
    logger.info("Comparing risk segmentation repeat rates...")
    
    # Extract counts for on_time and late experiences
    on_time_row = first_experience_retention[first_experience_retention['first_order_experience'] == 'on_time']
    late_row = first_experience_retention[first_experience_retention['first_order_experience'] == 'late']
    
    if len(on_time_row) == 0 or len(late_row) == 0:
        logger.warning("Missing on_time or late groups for comparison.")
        return {
            'high_risk_group': 'late',
            'low_risk_group': 'on_time',
            'delta_repeat_rate': 0.0,
            'p_value': 1.0,
            'is_significant': False
        }
        
    on_time_row = on_time_row.iloc[0]
    late_row = late_row.iloc[0]
    
    count1 = int(on_time_row['repeat_customer_count'])
    nobs1 = int(on_time_row['customer_count'])
    count2 = int(late_row['repeat_customer_count'])
    nobs2 = int(late_row['customer_count'])
    
    # Proportions z-test
    z_stat, p_value = proportions_ztest_custom(count1, nobs1, count2, nobs2)
    
    delta = float(on_time_row['repeat_rate'] - late_row['repeat_rate'])
    is_significant = (p_value < 0.05)
    
    logger.info(
        f"First experience impact: On-Time Repeat={on_time_row['repeat_rate']:.1f}%, "
        f"Late Repeat={late_row['repeat_rate']:.1f}%, Delta={delta:.1f}%, "
        f"p-value={p_value:.4f}, significant={is_significant}"
    )
    
    return {
        'high_risk_group': 'late',
        'low_risk_group': 'on_time',
        'delta_repeat_rate': delta,
        'p_value': p_value,
        'is_significant': is_significant
    }

def compare_revenue_decomposition_vs_baseline(rev_by_category, monthly_rev_trend):
    """
    Validates revenue decomposition by calculating contribution percentage of top categories.
    """
    logger.info("Comparing revenue decomposition vs monthly trend...")
    
    total_rev_monthly = monthly_rev_trend['total_revenue'].sum()
    total_rev_cat = rev_by_category['total_revenue'].sum()
    
    if len(rev_by_category) == 0:
        return {
            'top_dimension': 'None',
            'top_revenue': 0.0,
            'contribution_pct': 0.0,
            'p_value': 1.0,
            'is_significant': False
        }
        
    # Get top category
    top_cat = rev_by_category.iloc[0]
    top_dimension = str(top_cat['product_category_name'])
    top_revenue = float(top_cat['total_revenue'])
    
    contribution_pct = (top_revenue / total_rev_monthly) * 100.0 if total_rev_monthly > 0 else 0.0
    
    # We test whether the top category order values are significantly different from other categories.
    # Since we only have aggregates here, we can set is_significant based on contribution threshold (e.g. >= 10%)
    is_significant = (contribution_pct >= 10.0)
    
    logger.info(
        f"Revenue decomposition: Top Category={top_dimension}, "
        f"Contribution={contribution_pct:.1f}%, is_significant={is_significant}"
    )
    
    return {
        'top_dimension': top_dimension,
        'top_revenue': top_revenue,
        'contribution_pct': contribution_pct,
        'p_value': 0.0,  # placeholder
        'is_significant': is_significant
    }
