import pandas as pd
from utils.logger import get_logger

logger = get_logger("baseline_metrics.revenue")

def calculate_revenue_baseline(order_revenue, orders_clean, order_items, products):
    """
    Calculates baseline revenue metrics: monthly revenue trend, MoM growth, top categories, and freight ratio.
    """
    logger.info("Calculating baseline revenue metrics...")
    
    # 1. Merge order_revenue with orders_clean to get order_purchase_timestamp
    orders_rev = pd.merge(
        orders_clean[['order_id', 'order_purchase_timestamp', 'order_status']],
        order_revenue,
        on='order_id',
        how='inner'
    )
    
    # Create month period column
    orders_rev['month'] = orders_rev['order_purchase_timestamp'].dt.to_period('M')
    
    # Monthly revenue aggregation
    monthly_rev = orders_rev.groupby('month', as_index=False).agg({
        'total_payment_value': 'sum',
        'order_id': 'count'
    }).rename(columns={'total_payment_value': 'revenue', 'order_id': 'order_count'})
    
    # Sort by month
    monthly_rev = monthly_rev.sort_values('month').reset_index(drop=True)
    
    # Calculate MoM growth rate
    monthly_rev['mom_growth'] = monthly_rev['revenue'].pct_change() * 100.0
    avg_growth_rate = float(monthly_rev['mom_growth'].mean()) if len(monthly_rev) > 1 else 0.0
    
    # 2. Top 5 categories
    # Merge order_items with products to get category name
    items_prod = pd.merge(
        order_items[['order_id', 'product_id', 'price', 'freight_value']],
        products[['product_id', 'product_category_name']],
        on='product_id',
        how='inner'
    )
    
    # Filter for delivered orders only
    delivered_order_ids = orders_clean['order_id']
    items_prod_delivered = items_prod[items_prod['order_id'].isin(delivered_order_ids)]
    
    # Group by product_category_name and sum prices
    # Since we want category contribution to revenue, we sum the items' price + freight_value
    items_prod_delivered['item_revenue'] = items_prod_delivered['price'] + items_prod_delivered['freight_value']
    category_rev = items_prod_delivered.groupby('product_category_name', as_index=False).agg({
        'item_revenue': 'sum'
    }).sort_values('item_revenue', ascending=False)
    
    top5_categories = category_rev.head(5).reset_index(drop=True)
    
    # Convert monthly_rev month period to string for easy JSON serialization
    monthly_rev_serializable = monthly_rev.copy()
    monthly_rev_serializable['month'] = monthly_rev_serializable['month'].astype(str)
    
    # 3. Freight ratio
    total_payment = orders_rev['total_payment_value'].sum()
    total_freight = orders_rev['freight_value'].sum()
    freight_ratio = float(total_freight / total_payment) if total_payment > 0 else 0.0
    
    logger.info(
        f"Revenue baseline calculated. Total Delivered Revenue: {total_payment:.2f} BRL. "
        f"MoM Growth: {avg_growth_rate:.2f}%, Freight Ratio: {freight_ratio:.2%}"
    )
    
    return {
        'monthly_revenue': monthly_rev_serializable,
        'avg_growth_rate': avg_growth_rate,
        'top5_categories': top5_categories,
        'freight_ratio': freight_ratio
    }
