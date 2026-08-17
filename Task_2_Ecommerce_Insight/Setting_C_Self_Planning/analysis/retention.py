import pandas as pd
import numpy as np
from typing import Dict, Any

def analyze_customer_retention(
    customer_month_df: pd.DataFrame, 
    order_fact_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Performs customer retention analysis:
    1. Repeat Purchase Rate (RPR)
    2. Cohort Retention Matrix (Month 0 to Month 6)
    """
    print("Analyzing customer retention...")
    
    # 1. Repeat Purchase Rate (RPR)
    # RPR = (number of unique customers with order_count >= 2) / (total unique customers)
    total_customers = len(customer_month_df)
    repeat_customers = (customer_month_df['order_count'] >= 2).sum()
    rpr = float(repeat_customers / total_customers) if total_customers > 0 else 0.0
    
    # 2. Cohort Analysis
    # Ensure cohort_month is joined to order_fact_df
    # In case cohort_month is not yet in order_fact_df:
    if 'cohort_month' not in order_fact_df.columns:
        order_fact_with_cohort = pd.merge(
            order_fact_df,
            customer_month_df[['customer_unique_id', 'cohort_month']],
            on='customer_unique_id',
            how='left'
        )
    else:
        order_fact_with_cohort = order_fact_df.copy()
        
    # Extract order month as Period('M')
    order_month_period = order_fact_with_cohort['order_purchase_timestamp'].dt.to_period('M')
    cohort_month_period = pd.to_datetime(order_fact_with_cohort['cohort_month']).dt.to_period('M')
    
    # Calculate difference in months (periods_active)
    order_fact_with_cohort['periods_active'] = (order_month_period - cohort_month_period).apply(
        lambda x: x.n if pd.notnull(x) else np.nan
    )
    
    # Drop rows where periods_active is negative (due to data anomalies, though shouldn't happen)
    order_fact_with_cohort = order_fact_with_cohort[order_fact_with_cohort['periods_active'] >= 0]
    
    # Group by cohort_month and periods_active to count unique customers active
    cohort_group = order_fact_with_cohort.groupby(['cohort_month', 'periods_active'])['customer_unique_id'].nunique().reset_index()
    
    # Pivot the data
    cohort_pivot = cohort_group.pivot(
        index='cohort_month', 
        columns='periods_active', 
        values='customer_unique_id'
    )
    
    # Get the cohort sizes (Month 0 size)
    cohort_sizes = cohort_pivot.iloc[:, 0]
    
    # Calculate retention rates (percentage of the cohort size)
    cohort_retention = cohort_pivot.divide(cohort_sizes, axis=0)
    
    # Restrict columns to Month 0 to Month 6 if they exist
    max_month = min(6, int(cohort_retention.columns.max())) if len(cohort_retention.columns) > 0 else 6
    columns_to_keep = [m for m in range(max_month + 1) if m in cohort_retention.columns]
    cohort_retention = cohort_retention[columns_to_keep]
    
    # Format the cohort_month index to a string if it's not
    cohort_retention.index = cohort_retention.index.astype(str)
    
    print(f"Retention analysis completed. RPR = {rpr:.4f}")
    return {
        'rpr': rpr,
        'cohort_retention': cohort_retention,
        'cohort_sizes': cohort_sizes
    }
