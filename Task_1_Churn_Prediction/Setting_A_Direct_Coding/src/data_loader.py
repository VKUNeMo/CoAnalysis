import os
import gc
import pandas as pd

def load_cleaned_datasets(data_dir):
    """
    Loads and preprocesses Olist datasets in a memory-efficient manner.
    """
    print("Loading datasets from:", data_dir)
    
    # 1. Load customers
    print("Loading customers...")
    customers = pd.read_csv(
        os.path.join(data_dir, 'olist_customers_dataset.csv'),
        usecols=['customer_id', 'customer_unique_id', 'customer_zip_code_prefix', 'customer_state']
    )
    
    # 2. Load orders and parse dates
    print("Loading orders...")
    date_cols = [
        'order_purchase_timestamp', 
        'order_approved_at', 
        'order_delivered_carrier_date', 
        'order_delivered_customer_date', 
        'order_estimated_delivery_date'
    ]
    orders = pd.read_csv(
        os.path.join(data_dir, 'olist_orders_dataset.csv'),
        parse_dates=date_cols
    )
    
    # 3. Load order items
    print("Loading order items...")
    order_items = pd.read_csv(
        os.path.join(data_dir, 'olist_order_items_dataset.csv'),
        usecols=['order_id', 'order_item_id', 'product_id', 'seller_id', 'price', 'freight_value']
    )
    
    # 4. Load order payments
    print("Loading order payments...")
    order_payments = pd.read_csv(
        os.path.join(data_dir, 'olist_order_payments_dataset.csv'),
        usecols=['order_id', 'payment_sequential', 'payment_type', 'payment_installments', 'payment_value']
    )
    
    # 5. Load reviews
    print("Loading reviews...")
    reviews = pd.read_csv(
        os.path.join(data_dir, 'olist_order_reviews_dataset.csv'),
        usecols=['order_id', 'review_score', 'review_comment_message']
    )
    # Deduplicate reviews if any (sometimes there are multiple reviews for one order, take average review score)
    reviews_agg = reviews.groupby('order_id').agg({
        'review_score': 'mean',
        'review_comment_message': lambda x: x.notna().any()
    }).reset_index()
    reviews_agg.rename(columns={'review_comment_message': 'has_review_comment'}, inplace=True)
    
    # 6. Load products and translation
    print("Loading products and translation...")
    products = pd.read_csv(
        os.path.join(data_dir, 'olist_products_dataset.csv'),
        usecols=['product_id', 'product_category_name']
    )
    translation = pd.read_csv(os.path.join(data_dir, 'product_category_name_translation.csv'))
    products = products.merge(translation, on='product_category_name', how='left')
    products['product_category'] = products['product_category_name_english'].fillna(products['product_category_name']).fillna('unknown')
    products.drop(columns=['product_category_name', 'product_category_name_english'], inplace=True)
    
    # 7. Load sellers
    print("Loading sellers...")
    sellers = pd.read_csv(
        os.path.join(data_dir, 'olist_sellers_dataset.csv'),
        usecols=['seller_id', 'seller_zip_code_prefix']
    )
    
    # 8. Load geolocation and aggregate immediately to save memory
    print("Loading geolocation (aggregating)...")
    geolocation = pd.read_csv(
        os.path.join(data_dir, 'olist_geolocation_dataset.csv'),
        usecols=['geolocation_zip_code_prefix', 'geolocation_lat', 'geolocation_lng']
    )
    geo_agg = geolocation.groupby('geolocation_zip_code_prefix').mean().reset_index()
    del geolocation
    gc.collect()
    
    print("Datasets loaded and basic preprocessing finished.")
    return {
        'customers': customers,
        'orders': orders,
        'order_items': order_items,
        'order_payments': order_payments,
        'reviews': reviews_agg,
        'products': products,
        'sellers': sellers,
        'geo': geo_agg
    }
