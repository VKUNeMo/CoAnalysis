import numpy as np
import pandas as pd
import gc

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula 
    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 
    r = 6371.0 # Radius of earth in kilometers
    return c * r

def build_features_and_labels(datasets):
    """
    Builds the feature matrix and target label for churn prediction.
    """
    print("Building features...")
    
    customers = datasets['customers']
    orders = datasets['orders']
    order_items = datasets['order_items']
    order_payments = datasets['order_payments']
    reviews = datasets['reviews']
    products = datasets['products']
    sellers = datasets['sellers']
    geo = datasets['geo']

    # 1. Merge orders with customer_unique_id and customer geolocations
    print("Merging orders with customers...")
    orders_df = orders.merge(customers, on='customer_id', how='left')
    orders_df = orders_df.merge(
        geo.rename(columns={'geolocation_zip_code_prefix': 'customer_zip_code_prefix', 
                            'geolocation_lat': 'customer_lat', 
                            'geolocation_lng': 'customer_lng'}),
        on='customer_zip_code_prefix', how='left'
    )

    # 2. Process order items to get prices, freights, categories, and seller locations
    print("Processing items and calculating seller distances...")
    items_df = order_items.merge(products, on='product_id', how='left')
    items_df = items_df.merge(sellers, on='seller_id', how='left')
    items_df = items_df.merge(
        geo.rename(columns={'geolocation_zip_code_prefix': 'seller_zip_code_prefix', 
                            'geolocation_lat': 'seller_lat', 
                            'geolocation_lng': 'seller_lng'}),
        on='seller_zip_code_prefix', how='left'
    )
    
    # Merge customer coordinates to items to compute distance
    cust_coords = orders_df[['order_id', 'customer_lat', 'customer_lng']]
    items_df = items_df.merge(cust_coords, on='order_id', how='left')
    items_df['distance_km'] = haversine_distance(
        items_df['customer_lat'], items_df['customer_lng'],
        items_df['seller_lat'], items_df['seller_lng']
    )
    
    # Aggregate items by order
    items_agg = items_df.groupby('order_id').agg(
        order_item_count=('order_item_id', 'count'),
        order_unique_products=('product_id', 'nunique'),
        order_total_price=('price', 'sum'),
        order_total_freight=('freight_value', 'sum'),
        order_avg_seller_distance=('distance_km', 'mean')
    ).reset_index()
    items_agg['order_total_value'] = items_agg['order_total_price'] + items_agg['order_total_freight']
    
    # Extract top 10 product categories to create flags
    top_categories = items_df['product_category'].value_counts().head(10).index.tolist()
    for i, cat in enumerate(top_categories):
        items_df[f'cat_{i}_{cat}'] = (items_df['product_category'] == cat).astype(int)
    
    cat_flags = items_df.groupby('order_id')[[f'cat_{i}_{cat}' for i, cat in enumerate(top_categories)]].max().reset_index()
    items_agg = items_agg.merge(cat_flags, on='order_id', how='left')

    del items_df, cust_coords
    gc.collect()

    # 3. Process payments by order
    print("Processing payments...")
    # Get max payment installment and flag payment types
    payment_types = ['credit_card', 'boleto', 'voucher', 'debit_card']
    for pt in payment_types:
        order_payments[f'pay_{pt}'] = (order_payments['payment_type'] == pt).astype(int)
        
    payments_agg = order_payments.groupby('order_id').agg(
        payment_installments_max=('payment_installments', 'max'),
        pay_credit_card=('pay_credit_card', 'sum'),
        pay_boleto=('pay_boleto', 'sum'),
        pay_voucher=('pay_voucher', 'sum'),
        pay_debit_card=('pay_debit_card', 'sum'),
        total_payment_value=('payment_value', 'sum')
    ).reset_index()

    # 4. Combine all components into orders_df
    print("Combining orders, items, payments, and reviews...")
    orders_df = orders_df.merge(items_agg, on='order_id', how='left')
    orders_df = orders_df.merge(payments_agg, on='order_id', how='left')
    orders_df = orders_df.merge(reviews, on='order_id', how='left')

    # Fill NaNs for numerical fields where appropriate
    orders_df['order_item_count'] = orders_df['order_item_count'].fillna(0)
    orders_df['order_unique_products'] = orders_df['order_unique_products'].fillna(0)
    orders_df['order_total_price'] = orders_df['order_total_price'].fillna(0)
    orders_df['order_total_freight'] = orders_df['order_total_freight'].fillna(0)
    orders_df['order_total_value'] = orders_df['order_total_value'].fillna(0)
    
    for pt in payment_types:
        orders_df[f'pay_{pt}'] = orders_df[f'pay_{pt}'].fillna(0)
    orders_df['payment_installments_max'] = orders_df['payment_installments_max'].fillna(1)
    
    # 5. Post-purchase satisfaction features
    print("Engineering satisfaction features...")
    # Calculate days for delivery
    orders_df['delivery_time_days'] = (orders_df['order_delivered_customer_date'] - orders_df['order_purchase_timestamp']).dt.total_seconds() / 86400.0
    orders_df['estimated_delivery_time_days'] = (orders_df['order_estimated_delivery_date'] - orders_df['order_purchase_timestamp']).dt.total_seconds() / 86400.0
    orders_df['delivery_delay_days'] = (orders_df['order_delivered_customer_date'] - orders_df['order_estimated_delivery_date']).dt.total_seconds() / 86400.0
    orders_df['is_late_delivery'] = (orders_df['delivery_delay_days'] > 0).astype(int)
    orders_df['has_review_comment'] = orders_df['has_review_comment'].fillna(False).astype(int)

    # 6. Target Labeling & Censoring Check
    print("Sorting and generating target labels...")
    orders_df.sort_values(by=['customer_unique_id', 'order_purchase_timestamp'], inplace=True)
    
    # Compute next purchase timestamp
    orders_df['next_order_purchase_timestamp'] = orders_df.groupby('customer_unique_id')['order_purchase_timestamp'].shift(-1)
    orders_df['days_to_next_order'] = (orders_df['next_order_purchase_timestamp'] - orders_df['order_purchase_timestamp']).dt.total_seconds() / 86400.0
    
    T_max = orders['order_purchase_timestamp'].max()
    
    # Compute label and censor flag
    orders_df['churn_label'] = np.where(
        orders_df['days_to_next_order'] <= 90.0, 
        0, 
        1
    )
    # Mark censored rows (where customer has not repurchased, but the time between purchase and T_max is < 90 days)
    orders_df['is_censored'] = (orders_df['days_to_next_order'].isna()) & ((T_max - orders_df['order_purchase_timestamp']).dt.total_seconds() / 86400.0 < 90.0)
    
    # 7. Customer Historical Features (calculated chronologically up to, but not including, the current order)
    print("Engineering customer historical features...")
    
    # Historical order count (excluding current order)
    orders_df['hist_order_count'] = orders_df.groupby('customer_unique_id').cumcount()
    
    # Historical cumulative spending (excluding current order)
    orders_df['hist_total_spent'] = orders_df.groupby('customer_unique_id')['order_total_value'].cumsum() - orders_df['order_total_value']
    orders_df['hist_avg_spent'] = np.where(orders_df['hist_order_count'] > 0, orders_df['hist_total_spent'] / orders_df['hist_order_count'], 0.0)
    
    # Historical average review score (excluding current order)
    orders_df['has_review'] = orders_df['review_score'].notna().astype(int)
    orders_df['hist_review_count'] = orders_df.groupby('customer_unique_id')['has_review'].cumsum() - orders_df['has_review']
    orders_df['temp_review_score'] = orders_df['review_score'].fillna(0)
    orders_df['hist_total_review_score'] = orders_df.groupby('customer_unique_id')['temp_review_score'].cumsum() - orders_df['temp_review_score']
    orders_df.drop(columns=['has_review', 'temp_review_score'], inplace=True)
    orders_df['hist_avg_review_score'] = np.where(orders_df['hist_review_count'] > 0, orders_df['hist_total_review_score'] / orders_df['hist_review_count'], np.nan)
    # Fill missing historical review scores with dataset average (e.g. 4.0)
    orders_df['hist_avg_review_score'] = orders_df['hist_avg_review_score'].fillna(4.0)

    # Time since first order
    first_order_timestamp = orders_df.groupby('customer_unique_id')['order_purchase_timestamp'].transform('first')
    orders_df['hist_days_since_first_order'] = (orders_df['order_purchase_timestamp'] - first_order_timestamp).dt.total_seconds() / 86400.0
    
    # Time since previous order
    prev_order_timestamp = orders_df.groupby('customer_unique_id')['order_purchase_timestamp'].shift(1)
    orders_df['hist_days_since_prev_order'] = (orders_df['order_purchase_timestamp'] - prev_order_timestamp).dt.total_seconds() / 86400.0
    orders_df['hist_days_since_prev_order'] = orders_df['hist_days_since_prev_order'].fillna(-1.0) # -1 represents first order

    # Time/Date current order features
    orders_df['order_purchase_month'] = orders_df['order_purchase_timestamp'].dt.month
    orders_df['order_purchase_dayofweek'] = orders_df['order_purchase_timestamp'].dt.dayofweek
    orders_df['order_purchase_hour'] = orders_df['order_purchase_timestamp'].dt.hour

    # Filter out censored rows
    final_df = orders_df[~orders_df['is_censored']].copy()
    
    print(f"Feature engineering completed. Original orders: {len(orders_df)}, Uncensored orders: {len(final_df)}")
    
    # Free memory
    del orders_df
    gc.collect()
    
    # List features
    feature_cols = [
        'order_item_count', 'order_unique_products', 'order_total_price', 'order_total_freight', 
        'order_total_value', 'order_avg_seller_distance',
        'payment_installments_max', 'pay_credit_card', 'pay_boleto', 'pay_voucher', 'pay_debit_card',
        'delivery_time_days', 'estimated_delivery_time_days', 'delivery_delay_days', 'is_late_delivery',
        'review_score', 'has_review_comment',
        'hist_order_count', 'hist_total_spent', 'hist_avg_spent', 'hist_avg_review_score',
        'hist_days_since_first_order', 'hist_days_since_prev_order',
        'order_purchase_month', 'order_purchase_dayofweek', 'order_purchase_hour'
    ]
    # Add top category flags
    feature_cols.extend([f'cat_{i}_{cat}' for i, cat in enumerate(top_categories)])
    
    return final_df, feature_cols
