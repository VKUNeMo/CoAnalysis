import pandas as pd
import numpy as np
from typing import List

def build_order_fact(
    orders_df: pd.DataFrame, 
    payments_df: pd.DataFrame, 
    customers_df: pd.DataFrame, 
    valid_delivery_order_ids: List[str]
) -> pd.DataFrame:
    """
    Builds the order-level Fact Table (order_fact) containing order details,
    aggregated payments, customer location, and delivery delay metrics.
    """
    print("Building order_fact Table...")
    
    # 1. Group payments by order_id and calculate total payment
    pay_agg = payments_df.groupby('order_id')['payment_value'].sum().reset_index()
    pay_agg.rename(columns={'payment_value': 'total_payment'}, inplace=True)
    
    # 2. Filter orders to only keep valid delivery order IDs
    valid_set = set(valid_delivery_order_ids)
    orders_filtered = orders_df[orders_df['order_id'].isin(valid_set)].copy()
    
    # 3. Calculate delivery metrics
    # delivery_gap (timedelta) = order_delivered_customer_date - order_estimated_delivery_date
    orders_filtered['delivery_gap'] = orders_filtered['order_delivered_customer_date'] - orders_filtered['order_estimated_delivery_date']
    
    # is_late (int) = 1 if delivery_gap > 0 days, else 0
    orders_filtered['is_late'] = (orders_filtered['delivery_gap'].dt.total_seconds() > 0).astype(int)
    
    # days_late (float) = delivery_gap.dt.total_seconds() / 86400 if is_late == 1 else 0.0
    orders_filtered['days_late'] = np.where(
        orders_filtered['is_late'] == 1,
        orders_filtered['delivery_gap'].dt.total_seconds() / 86400.0,
        0.0
    ).astype('float32')
    
    # actual_delivery_days (float) = (order_delivered_customer_date - order_purchase_timestamp).dt.total_seconds() / 86400
    orders_filtered['actual_delivery_days'] = (
        (orders_filtered['order_delivered_customer_date'] - orders_filtered['order_purchase_timestamp']).dt.total_seconds() / 86400.0
    ).astype('float32')
    
    # 4. Join orders with total_payment and customer details (customer_unique_id and customer_state)
    order_fact = pd.merge(orders_filtered, pay_agg, on='order_id', how='left')
    
    # Fill missing payments with 0.0 (in case there are order_ids with no payments in payments_df)
    order_fact['total_payment'] = order_fact['total_payment'].fillna(0.0).astype('float32')
    
    cust_subset = customers_df[['customer_id', 'customer_unique_id', 'customer_state']]
    order_fact = pd.merge(order_fact, cust_subset, on='customer_id', how='left')
    
    # Keep only relevant columns and ensure 1 row per order_id
    order_fact = order_fact[[
        'order_id', 'customer_id', 'customer_unique_id', 'customer_state',
        'order_status', 'order_purchase_timestamp', 'order_approved_at',
        'order_delivered_carrier_date', 'order_delivered_customer_date',
        'order_estimated_delivery_date', 'delivery_gap', 'is_late',
        'days_late', 'actual_delivery_days', 'total_payment'
    ]].drop_duplicates(subset=['order_id'])
    
    print(f"order_fact built with {len(order_fact)} rows.")
    return order_fact


def build_order_item_fact(
    items_df: pd.DataFrame, 
    products_df: pd.DataFrame, 
    translation_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Builds the item-level Fact Table (order_item_fact) with English category names.
    """
    print("Building order_item_fact Table...")
    
    # 1. Join products with translation to get English category names
    prod_translated = pd.merge(
        products_df[['product_id', 'product_category_name']],
        translation_df[['product_category_name', 'product_category_name_english']],
        on='product_category_name',
        how='left'
    )
    
    # 2. Fill missing or untranslated categories with 'Unknown'
    prod_translated['product_category_name_english'] = prod_translated['product_category_name_english'].fillna('Unknown')
    
    # 3. Join with items details
    order_item_fact = pd.merge(
        items_df[['order_id', 'product_id', 'price', 'freight_value']],
        prod_translated[['product_id', 'product_category_name_english']],
        on='product_id',
        how='left'
    )
    
    # Fill missing product category with 'Unknown' if product is not in products table
    order_item_fact['product_category_name_english'] = order_item_fact['product_category_name_english'].fillna('Unknown')
    
    # Ensure optimal dtypes
    order_item_fact['price'] = order_item_fact['price'].astype('float32')
    order_item_fact['freight_value'] = order_item_fact['freight_value'].astype('float32')
    order_item_fact['product_category_name_english'] = order_item_fact['product_category_name_english'].astype('category')
    
    print(f"order_item_fact built with {len(order_item_fact)} rows.")
    return order_item_fact


def build_customer_month_fact(order_fact_df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the customer-level Fact Table (customer_month_fact) for retention and cohort analysis.
    """
    print("Building customer_month_fact Table...")
    
    # Group by customer_unique_id
    grouped = order_fact_df.groupby('customer_unique_id')
    
    # Aggregate fields
    customer_month_fact = grouped.agg({
        'order_purchase_timestamp': 'min',
        'order_id': 'nunique',
        'total_payment': 'sum'
    }).reset_index()
    
    # Rename columns
    customer_month_fact.rename(columns={
        'order_purchase_timestamp': 'first_order_date',
        'order_id': 'order_count',
        'total_payment': 'total_spend'
    }, inplace=True)
    
    # Calculate cohort month (format 'YYYY-MM')
    customer_month_fact['cohort_month'] = customer_month_fact['first_order_date'].dt.strftime('%Y-%m')
    
    # Calculate is_repeat_customer (1 if order_count >= 2, else 0)
    customer_month_fact['is_repeat_customer'] = (customer_month_fact['order_count'] >= 2).astype(int)
    
    # Downcast and type optimization
    customer_month_fact['order_count'] = customer_month_fact['order_count'].astype('int16')
    customer_month_fact['is_repeat_customer'] = customer_month_fact['is_repeat_customer'].astype('int8')
    customer_month_fact['total_spend'] = customer_month_fact['total_spend'].astype('float32')
    customer_month_fact['cohort_month'] = customer_month_fact['cohort_month'].astype('category')
    
    print(f"customer_month_fact built with {len(customer_month_fact)} rows.")
    return customer_month_fact
