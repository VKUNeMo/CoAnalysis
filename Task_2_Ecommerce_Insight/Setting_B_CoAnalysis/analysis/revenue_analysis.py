import pandas as pd
import numpy as np
from utils.logger import get_logger
from utils.stats_utils import calculate_partial_correlation

logger = get_logger("analysis.revenue")

def compute_revenue_trend_by_month(order_revenue, orders_clean):
    """
    Computes monthly revenue trend metrics including AOV, freight ratio, and MoM growth.
    """
    logger.info("Computing monthly revenue trend...")
    
    # Merge order_revenue with orders_clean
    df = pd.merge(
        orders_clean[['order_id', 'order_purchase_timestamp']],
        order_revenue,
        on='order_id',
        how='inner'
    )
    
    # Month period
    df['month'] = df['order_purchase_timestamp'].dt.to_period('M')
    
    # Aggregate
    grouped = df.groupby('month').agg(
        total_revenue=('total_payment_value', 'sum'),
        total_freight=('freight_value', 'sum'),
        order_count=('order_id', 'count')
    ).sort_index().reset_index()
    
    # Derived columns
    grouped['aov'] = grouped['total_revenue'] / grouped['order_count']
    grouped['freight_ratio'] = grouped['total_freight'] / grouped['total_revenue']
    grouped['mom_growth_pct'] = grouped['total_revenue'].pct_change() * 100.0
    
    # Fill first MoM growth as NaN or 0.0
    grouped['mom_growth_pct'] = grouped['mom_growth_pct'].fillna(0.0)
    
    # Convert month to string
    grouped['month'] = grouped['month'].astype(str)
    
    logger.info(f"Monthly revenue trend computed for {len(grouped)} months.")
    return grouped

def compute_revenue_by_dimension(order_revenue, orders_clean, order_items, products, customers_df, dimension, top_n=15):
    """
    Decomposes revenue by product_category, customer_state, or payment_type.
    """
    logger.info(f"Decomposing revenue by dimension: {dimension}...")
    
    # Start with orders joined with revenue
    df = pd.merge(
        orders_clean[['order_id', 'customer_id']],
        order_revenue,
        on='order_id',
        how='inner'
    )
    
    if dimension == 'customer_state':
        df = pd.merge(df, customers_df[['customer_id', 'customer_state']], on='customer_id', how='inner')
        group_col = 'customer_state'
    elif dimension == 'product_category':
        items_prod = pd.merge(
            order_items[['order_id', 'product_id']],
            products[['product_id', 'product_category_name']],
            on='product_id',
            how='inner'
        )
        df = pd.merge(df, items_prod, on='order_id', how='inner')
        group_col = 'product_category_name'
    elif dimension == 'payment_type':
        # payment_type is in order_payments (which was aggregate, so let's handle payment type logic)
        # Wait, how does order_payments map? One order can have multiple payment methods.
        # If order_payments is already aggregated, we might lose payment_type. Let's merge directly with order_payments
        # but group payment value by payment_type!
        # For payment_type, we sum payment_value grouped by payment_type.
        # Let's handle it as a special case:
        logger.info("Computing revenue by payment type special case...")
        # Join orders_clean with order_payments
        df_pay = pd.merge(
            orders_clean[['order_id']],
            order_items[['order_id', 'freight_value']].groupby('order_id').sum().reset_index(), # estimation for freight
            on='order_id',
            how='left'
        )
        # Note: we need total revenue per payment type. Let's do that from order_payments
        order_payments_delivered = order_revenue.merge(
            orders_clean[['order_id']], on='order_id', how='inner'
        ) # this is clean order revenue
        # Let's load the raw order_payments dataset
        # We can pass raw payments table or use a fallback
        # Wait! Let's check: if we have a payment_type column in order_revenue, we can use it.
        # But order_revenue aggregated payment_value by order_id, so it doesn't have payment_type.
        # Therefore, we can join orders_clean with the raw order_payments table!
        # Let's do that if payment_type is requested.
        pass
        
    if dimension == 'payment_type':
        # Special logic: join raw order_payments with orders_clean
        # We will pass raw order_payments in main to this function as order_payments_raw
        # Let's assume order_revenue is actually the raw order_payments DataFrame here, or we can handle it inside
        # by checking if it contains payment_type
        if 'payment_type' in order_revenue.columns:
            df = pd.merge(
                orders_clean[['order_id']],
                order_revenue, # raw order_payments
                on='order_id',
                how='inner'
            )
            # rename payment_value to total_payment_value for consistency
            df = df.rename(columns={'payment_value': 'total_payment_value'})
            df['freight_value'] = 0.0 # simplified
            group_col = 'payment_type'
        else:
            logger.warning("payment_type requested but order_revenue is already aggregated without payment_type. Returning empty.")
            return pd.DataFrame()
    else:
        group_col = 'customer_state' if dimension == 'customer_state' else 'product_category_name'
        
    # Group by
    grouped = df.groupby(group_col).agg(
        total_revenue=('total_payment_value', 'sum'),
        total_freight=('freight_value', 'sum'),
        order_count=('order_id', 'count')
    )
    
    grouped['aov'] = grouped['total_revenue'] / grouped['order_count']
    grouped['freight_ratio'] = grouped['total_freight'] / grouped['total_revenue']
    grouped['freight_ratio'] = grouped['freight_ratio'].fillna(0.0)
    
    top_dimensions = grouped.sort_values('total_revenue', ascending=False).head(top_n).reset_index()
    logger.info(f"Revenue decomposition by {dimension} completed. Number of rows: {len(top_dimensions)}")
    return top_dimensions

def compute_controlled_correlation_matrix(orders_clean, order_revenue, order_reviews, customer_summary, customers_df, products, order_items):
    """
    Computes a controlled correlation matrix between late_days, review_score, payment_value, and repeat_purchase.
    Uses month, customer_state, and product_category as controls.
    """
    logger.info("Computing controlled correlation matrix...")
    
    # 1. Merge orders_clean with customer unique id and order_revenue
    df = pd.merge(
        orders_clean[['order_id', 'customer_id', 'late_days', 'order_purchase_timestamp']],
        customers_df[['customer_id', 'customer_unique_id', 'customer_state']],
        on='customer_id',
        how='inner'
    )
    
    df = pd.merge(
        df,
        order_revenue[['order_id', 'total_payment_value']],
        on='order_id',
        how='inner'
    )
    
    # 2. Join with order_reviews
    df = pd.merge(
        df,
        order_reviews[['order_id', 'review_score']],
        on='order_id',
        how='left'
    )
    
    # 3. Join with customer_summary to get is_repeat flag
    df = pd.merge(
        df,
        customer_summary[['customer_unique_id', 'is_repeat']],
        on='customer_unique_id',
        how='inner'
    )
    
    # 4. Join with product category for controls
    items_prod = pd.merge(
        order_items[['order_id', 'product_id']],
        products[['product_id', 'product_category_name']],
        on='product_id',
        how='inner'
    ).drop_duplicates('order_id') # one category per order to simplify controls
    
    df = pd.merge(df, items_prod, on='order_id', how='left')
    
    # Prepare target variables
    df['repeat_purchase'] = df['is_repeat'].astype(int)
    df['month'] = df['order_purchase_timestamp'].dt.to_period('M').astype(str)
    
    target_vars = ['late_days', 'review_score', 'total_payment_value', 'repeat_purchase']
    control_vars = ['month', 'customer_state', 'product_category_name']
    
    # Drop rows with nulls in target variables or control variables
    clean_df = df[target_vars + control_vars].dropna().copy()
    
    n_samples = len(clean_df)
    logger.info(f"Controlled correlation matrix sample size: {n_samples}")
    
    corr_matrix = pd.DataFrame(index=target_vars, columns=target_vars, dtype=float)
    p_matrix = pd.DataFrame(index=target_vars, columns=target_vars, dtype=float)
    
    # Initialize diagonal
    for var in target_vars:
        corr_matrix.loc[var, var] = 1.0
        p_matrix.loc[var, var] = 0.0
        
    if n_samples > 10:
        # Compute pairwise partial correlations
        for i in range(len(target_vars)):
            for j in range(i + 1, len(target_vars)):
                var1 = target_vars[i]
                var2 = target_vars[j]
                
                corr, pval = calculate_partial_correlation(clean_df, var1, var2, control_vars)
                
                corr_matrix.loc[var1, var2] = corr
                corr_matrix.loc[var2, var1] = corr
                
                p_matrix.loc[var1, var2] = pval
                p_matrix.loc[var2, var1] = pval
    else:
        logger.warning("Insufficient samples for partial correlation. Setting correlations to 0.")
        corr_matrix.fillna(0.0, inplace=True)
        p_matrix.fillna(1.0, inplace=True)
        
    # Format target variable names for display
    display_names = {
        'late_days': 'Late Days',
        'review_score': 'Review Score',
        'total_payment_value': 'Order Revenue',
        'repeat_purchase': 'Repeat Purchase'
    }
    
    corr_matrix.rename(index=display_names, columns=display_names, inplace=True)
    p_matrix.rename(index=display_names, columns=display_names, inplace=True)
    
    return corr_matrix, p_matrix, n_samples
