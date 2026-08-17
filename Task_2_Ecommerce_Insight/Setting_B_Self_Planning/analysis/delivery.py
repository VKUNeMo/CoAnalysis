import pandas as pd
import numpy as np
from typing import Dict, Any

def analyze_delivery_performance(order_fact_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyzes Olist delivery performance:
    1. Overall late delivery rate
    2. Delivery metrics by customer state (total orders, late rate, median & P90 days late)
    3. Monthly trend of late delivery rates
    """
    print("Analyzing delivery performance...")
    
    total_orders = len(order_fact_df)
    late_orders_count = int(order_fact_df['is_late'].sum())
    overall_late_rate = float(late_orders_count / total_orders) if total_orders > 0 else 0.0
    
    # 2. Performance by customer state
    state_grouped = order_fact_df.groupby('customer_state').agg(
        total_orders=('order_id', 'count'),
        late_orders=('is_late', 'sum')
    ).reset_index()
    
    state_grouped['late_rate'] = (state_grouped['late_orders'] / state_grouped['total_orders']).astype('float32')
    
    # Calculate median and p90 days_late for late orders (is_late == 1) to get the delay severity
    late_orders_only = order_fact_df[order_fact_df['is_late'] == 1]
    state_delay_stats = late_orders_only.groupby('customer_state')['days_late'].agg(
        median_days_late='median',
        p90_days_late=lambda x: x.quantile(0.9)
    ).reset_index()
    
    # Join the stats back to state_grouped
    state_metrics = pd.merge(state_grouped, state_delay_stats, on='customer_state', how='left')
    state_metrics['median_days_late'] = state_metrics['median_days_late'].fillna(0.0).astype('float32')
    state_metrics['p90_days_late'] = state_metrics['p90_days_late'].fillna(0.0).astype('float32')
    
    # Sort states by late rate descending
    state_metrics = state_metrics.sort_values(by='late_rate', ascending=False).reset_index(drop=True)
    
    # 3. Monthly late delivery rate trend
    # Extract purchase month
    order_fact_df = order_fact_df.copy()
    order_fact_df['purchase_month'] = order_fact_df['order_purchase_timestamp'].dt.strftime('%Y-%m')
    
    monthly_grouped = order_fact_df.groupby('purchase_month').agg(
        total_orders=('order_id', 'count'),
        late_orders=('is_late', 'sum')
    ).reset_index()
    
    monthly_grouped['late_rate'] = (monthly_grouped['late_orders'] / monthly_grouped['total_orders']).astype('float32')
    
    # Sort chronologically
    monthly_grouped = monthly_grouped.sort_values(by='purchase_month').reset_index(drop=True)
    
    print(f"Delivery analysis completed. Overall late rate = {overall_late_rate:.4f}")
    return {
        'overall_late_rate': overall_late_rate,
        'state_metrics': state_metrics,
        'monthly_metrics': monthly_grouped
    }
