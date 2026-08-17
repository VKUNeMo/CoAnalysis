import pandas as pd
import numpy as np
from typing import Dict, Any

def analyze_revenue_trends(
    order_fact_df: pd.DataFrame, 
    item_fact_df: pd.DataFrame,
    payments_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Analyzes Olist revenue trends across multiple dimensions:
    1. Monthly revenue and MoM growth rate
    2. Revenue contribution by product category (Top 10)
    3. Revenue contribution by customer state
    4. Revenue and installment stats by payment type
    """
    print("Analyzing revenue trends...")
    
    # 1. Monthly revenue trend
    order_fact_df = order_fact_df.copy()
    order_fact_df['purchase_month'] = order_fact_df['order_purchase_timestamp'].dt.strftime('%Y-%m')
    
    monthly_rev = order_fact_df.groupby('purchase_month')['total_payment'].sum().reset_index()
    monthly_rev.rename(columns={'total_payment': 'monthly_revenue'}, inplace=True)
    monthly_rev = monthly_rev.sort_values(by='purchase_month').reset_index(drop=True)
    
    # MoM growth rate
    monthly_rev['mom_growth'] = monthly_rev['monthly_revenue'].pct_change().astype('float32')
    
    # 2. Product Category contribution
    cat_rev = item_fact_df.groupby('product_category_name_english')['price'].sum().reset_index()
    cat_rev.rename(columns={'price': 'category_revenue'}, inplace=True)
    total_cat_rev = cat_rev['category_revenue'].sum()
    cat_rev['contribution_share'] = (cat_rev['category_revenue'] / total_cat_rev).astype('float32')
    
    # Sort and get Top 10
    top_categories = cat_rev.sort_values(by='category_revenue', ascending=False).head(10).reset_index(drop=True)
    
    # 3. Customer State contribution
    state_rev = order_fact_df.groupby('customer_state')['total_payment'].sum().reset_index()
    state_rev.rename(columns={'total_payment': 'state_revenue'}, inplace=True)
    total_state_rev = state_rev['state_revenue'].sum()
    state_rev['contribution_share'] = (state_rev['state_revenue'] / total_state_rev).astype('float32')
    state_rev = state_rev.sort_values(by='state_revenue', ascending=False).reset_index(drop=True)
    
    # 4. Payment Type analysis
    # Group payments_df by payment_type
    # We want: total payment value, count of unique orders, and mean installments
    pay_grouped = payments_df.groupby('payment_type').agg(
        total_payment_value=('payment_value', 'sum'),
        order_count=('order_id', 'nunique'),
        avg_installments=('payment_installments', 'mean')
    ).reset_index()
    
    # Cast dtypes
    pay_grouped['total_payment_value'] = pay_grouped['total_payment_value'].astype('float32')
    pay_grouped['avg_installments'] = pay_grouped['avg_installments'].astype('float32')
    pay_grouped = pay_grouped.sort_values(by='total_payment_value', ascending=False).reset_index(drop=True)
    
    print("Revenue analysis completed.")
    return {
        'monthly_revenue': monthly_rev,
        'top_categories': top_categories,
        'state_revenue': state_rev,
        'payment_metrics': pay_grouped
    }
