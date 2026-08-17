import pandas as pd
import numpy as np
from typing import Dict, Any

def correlate_delivery_and_customer_behavior(
    order_fact_df: pd.DataFrame, 
    customer_month_df: pd.DataFrame,
    reviews_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Correlates operational delivery performance with customer satisfaction and loyalty.
    1. First order delivery status (on-time vs late) vs Repeat Purchase Rate (RPR).
    2. Delivery lateness groups (on_time, late_light, late_heavy) vs Average Review Score.
    3. Revenue impact by delay group (on_time, late_light, late_heavy).
    4. CLV (Customer Lifetime Value) by first order delivery status.
    """
    print("Correlating delivery and customer behavior...")
    
    # --- 1. First order delivery status vs customer loyalty ---
    # Find the index of the first order for each customer_unique_id
    # Sort order_fact_df by order_purchase_timestamp to make sure the first occurrence is the earliest
    sorted_orders = order_fact_df.sort_values(by='order_purchase_timestamp')
    first_orders_idx = sorted_orders.groupby('customer_unique_id')['order_purchase_timestamp'].idxmin()
    first_orders = order_fact_df.loc[first_orders_idx][['customer_unique_id', 'is_late']].copy()
    first_orders.rename(columns={'is_late': 'first_order_is_late'}, inplace=True)
    
    # Merge with customer_month_df to get is_repeat_customer
    merged_retention = pd.merge(
        first_orders,
        customer_month_df[['customer_unique_id', 'is_repeat_customer']],
        on='customer_unique_id',
        how='inner'
    )
    
    # Compute RPR for each group (first order on-time vs first order late)
    rpr_by_delivery = merged_retention.groupby('first_order_is_late')['is_repeat_customer'].mean().reset_index()
    rpr_by_delivery.rename(columns={'is_repeat_customer': 'rpr'}, inplace=True)
    rpr_by_delivery['rpr'] = rpr_by_delivery['rpr'].astype('float32')
    
    # Map group labels for readability
    rpr_by_delivery['first_order_status'] = np.where(
        rpr_by_delivery['first_order_is_late'] == 0,
        'On Time',
        'Late'
    )
    
    # --- 2. Lateness severity vs Review Score ---
    # Classify lateness of orders into 3 categories:
    # 'on_time': is_late == 0
    # 'late_light': 0 < days_late <= 7
    # 'late_heavy': days_late > 7
    df_temp = order_fact_df.copy()
    conditions = [
        df_temp['is_late'] == 0,
        (df_temp['is_late'] == 1) & (df_temp['days_late'] <= 7.0),
        (df_temp['is_late'] == 1) & (df_temp['days_late'] > 7.0)
    ]
    choices = ['on_time', 'late_light', 'late_heavy']
    df_temp['delay_group'] = np.select(conditions, choices, default='unknown')
    
    # Prepare reviews data: aggregate review scores per order_id to handle duplicates
    rev_agg = reviews_df.groupby('order_id')['review_score'].mean().reset_index()
    rev_agg['review_score'] = rev_agg['review_score'].astype('float32')
    
    # Merge order delay categories with review scores
    order_reviews = pd.merge(
        df_temp[['order_id', 'delay_group']],
        rev_agg,
        on='order_id',
        how='inner'
    )
    
    # Calculate average review score and order count for each delay group
    review_by_delay = order_reviews.groupby('delay_group')['review_score'].agg(
        avg_review_score='mean',
        order_count='count'
    ).reset_index()
    
    # Cast and format Categories for ordering in output/charts
    review_by_delay['delay_group'] = pd.Categorical(
        review_by_delay['delay_group'], 
        categories=['on_time', 'late_light', 'late_heavy'], 
        ordered=True
    )
    review_by_delay = review_by_delay.sort_values('delay_group').reset_index(drop=True)
    review_by_delay['avg_review_score'] = review_by_delay['avg_review_score'].astype('float32')
    
    # --- 3. Revenue impact by delay group ---
    # Link delay group back to total_payment to show revenue dimension
    delay_revenue = pd.merge(
        df_temp[['order_id', 'delay_group', 'total_payment']],
        rev_agg,
        on='order_id',
        how='inner'
    )
    
    delay_revenue_impact = delay_revenue.groupby('delay_group').agg(
        total_revenue=('total_payment', 'sum'),
        avg_order_value=('total_payment', 'mean'),
        order_count=('order_id', 'count'),
        avg_review=('review_score', 'mean')
    ).reset_index()
    
    delay_revenue_impact['delay_group'] = pd.Categorical(
        delay_revenue_impact['delay_group'],
        categories=['on_time', 'late_light', 'late_heavy'],
        ordered=True
    )
    delay_revenue_impact = delay_revenue_impact.sort_values('delay_group').reset_index(drop=True)

    # Calculate % low-rating (1-2 stars) per delay group
    delay_revenue['is_low_rating'] = (delay_revenue['review_score'] <= 2).astype(int)
    low_rating_by_group = delay_revenue.groupby('delay_group')['is_low_rating'].mean().reset_index()
    low_rating_by_group.rename(columns={'is_low_rating': 'low_rating_rate'}, inplace=True)
    delay_revenue_impact = pd.merge(delay_revenue_impact, low_rating_by_group, on='delay_group', how='left')
    
    # --- 4. CLV by first order delivery status ---
    # Merge first order delivery status with customer lifetime value
    clv_merged = pd.merge(
        first_orders,
        customer_month_df[['customer_unique_id', 'total_spend', 'order_count']],
        on='customer_unique_id',
        how='inner'
    )
    
    clv_by_first_delivery = clv_merged.groupby('first_order_is_late').agg(
        customer_count=('customer_unique_id', 'count'),
        mean_clv=('total_spend', 'mean'),
        median_clv=('total_spend', 'median'),
        p90_clv=('total_spend', lambda x: x.quantile(0.9)),
        mean_orders=('order_count', 'mean')
    ).reset_index()
    
    clv_by_first_delivery['first_order_status'] = np.where(
        clv_by_first_delivery['first_order_is_late'] == 0,
        'On Time',
        'Late'
    )
    
    print("Correlation analysis completed.")
    return {
        'rpr_by_delivery': rpr_by_delivery,
        'review_by_delay': review_by_delay,
        'delay_revenue_impact': delay_revenue_impact,
        'clv_by_first_delivery': clv_by_first_delivery
    }

