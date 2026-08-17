import numpy as np
import pandas as pd
import logging
from src.baseline.feature_engineering import compute_rfm_features

logger = logging.getLogger("churn_prediction.modeling.feature_engineering")

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees) in kilometers.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2.0 * np.arcsin(np.sqrt(a))
    r = 6371.0  # Radius of earth in kilometers
    return c * r

def compute_advanced_features(orders_df: pd.DataFrame, customers_df: pd.DataFrame,
                              items_df: pd.DataFrame, payments_df: pd.DataFrame,
                              reviews_df: pd.DataFrame, products_df: pd.DataFrame,
                              sellers_df: pd.DataFrame, geolocation_df: pd.DataFrame,
                              cutoff_date: str) -> pd.DataFrame:
    """
    Compute full feature matrix including RFM, behavioral, transactional, and geospatial features.
    Strictly uses data before or at cutoff_date to prevent data leakage.
    """
    cutoff_dt = pd.to_datetime(cutoff_date)
    
    # 1. Filter orders and dependencies before cutoff
    orders_filtered = orders_df[orders_df['order_purchase_timestamp'] <= cutoff_dt].copy()
    
    # Merge orders with customers to map to customer_unique_id
    orders_cust = pd.merge(orders_filtered, customers_df[['customer_id', 'customer_unique_id', 'customer_zip_code_prefix']], on='customer_id', how='inner')
    
    if orders_cust.empty:
        logger.warning(f"No orders found before cutoff {cutoff_date}. Returning empty feature matrix.")
        return pd.DataFrame()
        
    # Get active cohort list
    cohort_customers = orders_cust['customer_unique_id'].unique()
    
    # 2. Baseline RFM features
    rfm_df = compute_rfm_features(orders_df, customers_df, payments_df, cutoff_date)
    rfm_df['recency_log'] = np.log1p(rfm_df['recency']).astype('float32')
    
    # Order span & velocity features
    cust_order_dates = orders_cust.groupby('customer_unique_id').agg(
        first_order_date=('order_purchase_timestamp', 'min'),
        last_order_date=('order_purchase_timestamp', 'max'),
        orders_30d=('order_purchase_timestamp', lambda x: (x >= cutoff_dt - pd.Timedelta(days=30)).sum()),
        orders_60d=('order_purchase_timestamp', lambda x: (x >= cutoff_dt - pd.Timedelta(days=60)).sum())
    ).reset_index()
    cust_order_dates_clean = cust_order_dates[['customer_unique_id', 'orders_30d', 'orders_60d']]
    
    # Late delivery ratio
    orders_filtered_late = orders_filtered.copy()
    orders_filtered_late['is_late'] = (orders_filtered_late['order_delivered_customer_date'] > orders_filtered_late['order_estimated_delivery_date']).astype('float32')
    cust_late = pd.merge(orders_filtered_late[['order_id', 'is_late']], orders_cust[['order_id', 'customer_unique_id']], on='order_id', how='inner')
    late_agg = cust_late.groupby('customer_unique_id').agg(
        late_delivery_ratio=('is_late', 'mean')
    ).reset_index()
    late_agg['late_delivery_ratio'] = late_agg['late_delivery_ratio'].astype('float32')
    
    # 3. Behavioral Features
    # - avg_order_value
    # - product_diversity (unique product categories)
    # - avg_review_score
    
    # average order value: monetary / frequency
    rfm_df['avg_order_value'] = (rfm_df['monetary'] / rfm_df['frequency']).astype('float32')
    
    # product diversity
    items_filtered = items_df[items_df['order_id'].isin(orders_filtered['order_id'])].copy()
    items_cust = pd.merge(items_filtered, orders_cust[['order_id', 'customer_unique_id']], on='order_id', how='inner')
    items_prod = pd.merge(items_cust, products_df[['product_id', 'product_category_name']], on='product_id', how='left')
    items_prod['product_category_name'] = items_prod['product_category_name'].fillna('unknown')
    
    prod_diversity = items_prod.groupby('customer_unique_id').agg(
        product_diversity=('product_category_name', 'nunique')
    ).reset_index()
    prod_diversity['product_diversity'] = prod_diversity['product_diversity'].astype('int16')
    
    # average review score
    reviews_filtered = reviews_df[reviews_df['order_id'].isin(orders_filtered['order_id'])].copy()
    reviews_cust = pd.merge(reviews_filtered, orders_cust[['order_id', 'customer_unique_id']], on='order_id', how='inner')
    reviews_agg = reviews_cust.groupby('customer_unique_id').agg(
        avg_review_score=('review_score', 'mean')
    ).reset_index()
    reviews_agg['avg_review_score'] = reviews_agg['avg_review_score'].astype('float32')
    
    # 4. Transactional Features
    # - preferred payment method (credit card, boleto, voucher, debit_card)
    # - avg payment installments
    payments_filtered = payments_df[payments_df['order_id'].isin(orders_filtered['order_id'])].copy()
    payments_cust = pd.merge(payments_filtered, orders_cust[['order_id', 'customer_unique_id']], on='order_id', how='inner')
    
    # average installments
    installments_agg = payments_cust.groupby('customer_unique_id').agg(
        payment_installments_avg=('payment_installments', 'mean')
    ).reset_index()
    installments_agg['payment_installments_avg'] = installments_agg['payment_installments_avg'].astype('float32')
    
    # payment type ratios
    pay_dummies = pd.get_dummies(payments_cust['payment_type'], prefix='pay_type')
    pay_cust_dummies = pd.concat([payments_cust[['customer_unique_id']], pay_dummies], axis=1)
    pay_ratios = pay_cust_dummies.groupby('customer_unique_id').mean().reset_index()
    
    # 5. Geospatial Features
    # - mean customer-seller distance
    # Aggregation of geolocation
    logger.info("Computing geospatial distance features...")
    geo_agg = geolocation_df.groupby('geolocation_zip_code_prefix').agg(
        lat=('geolocation_lat', 'mean'),
        lng=('geolocation_lng', 'mean')
    ).reset_index()
    
    # Merge items_cust with sellers and zip code coordinates
    items_seller = pd.merge(items_cust, sellers_df[['seller_id', 'seller_zip_code_prefix']], on='seller_id', how='left')
    
    # Join customer zip code coordinates
    cust_zip_coords = pd.merge(
        orders_cust[['customer_unique_id', 'customer_zip_code_prefix']],
        geo_agg.rename(columns={'geolocation_zip_code_prefix': 'customer_zip_code_prefix', 'lat': 'cust_lat', 'lng': 'cust_lng'}),
        on='customer_zip_code_prefix',
        how='left'
    )
    
    # Join seller zip code coordinates
    items_seller_coords = pd.merge(
        items_seller,
        geo_agg.rename(columns={'geolocation_zip_code_prefix': 'seller_zip_code_prefix', 'lat': 'sel_lat', 'lng': 'sel_lng'}),
        on='seller_zip_code_prefix',
        how='left'
    )
    
    # Combine customer and seller coordinates
    dist_df = pd.merge(
        items_seller_coords[['customer_unique_id', 'sel_lat', 'sel_lng']],
        cust_zip_coords[['customer_unique_id', 'cust_lat', 'cust_lng']],
        on='customer_unique_id',
        how='inner'
    )
    
    # Calculate Haversine distance
    dist_df['distance_km'] = haversine_distance(
        dist_df['cust_lat'], dist_df['cust_lng'],
        dist_df['sel_lat'], dist_df['sel_lng']
    )
    
    # Group by customer_unique_id
    cust_dist = dist_df.groupby('customer_unique_id').agg(
        avg_seller_distance=('distance_km', 'mean')
    ).reset_index()
    cust_dist['avg_seller_distance'] = cust_dist['avg_seller_distance'].astype('float32')
    
    # 6. Sequential left joins to combine all groups of features
    feature_df = rfm_df
    feature_df = pd.merge(feature_df, cust_order_dates_clean, on='customer_unique_id', how='left')
    feature_df = pd.merge(feature_df, late_agg, on='customer_unique_id', how='left')
    feature_df = pd.merge(feature_df, prod_diversity, on='customer_unique_id', how='left')
    feature_df = pd.merge(feature_df, reviews_agg, on='customer_unique_id', how='left')
    feature_df = pd.merge(feature_df, installments_agg, on='customer_unique_id', how='left')
    feature_df = pd.merge(feature_df, pay_ratios, on='customer_unique_id', how='left')
    feature_df = pd.merge(feature_df, cust_dist, on='customer_unique_id', how='left')
    
    # Impute missing values with defaults
    feature_df['orders_30d'] = feature_df['orders_30d'].fillna(0).astype('int16')
    feature_df['orders_60d'] = feature_df['orders_60d'].fillna(0).astype('int16')
    feature_df['late_delivery_ratio'] = feature_df['late_delivery_ratio'].fillna(0.0).astype('float32')
    feature_df['product_diversity'] = feature_df['product_diversity'].fillna(1).astype('int16')
    feature_df['avg_review_score'] = feature_df['avg_review_score'].fillna(4.0).astype('float32')
    feature_df['payment_installments_avg'] = feature_df['payment_installments_avg'].fillna(1.0).astype('float32')
    
    # Fill dynamic payment ratios with 0.0
    pay_cols = [col for col in feature_df.columns if col.startswith('pay_type_')]
    for col in pay_cols:
        feature_df[col] = feature_df[col].fillna(0.0).astype('float32')
        
    # Fill distance with average distance of all customers
    mean_dist = feature_df['avg_seller_distance'].mean()
    if pd.isna(mean_dist):
        mean_dist = 600.0 # Default value in km (average Brazil parcel transit distance)
    feature_df['avg_seller_distance'] = feature_df['avg_seller_distance'].fillna(mean_dist).astype('float32')
    
    # Remove features with correlation > 0.95 to reduce redundancy
    logger.info("Performing multicollinearity check...")
    numeric_cols = feature_df.select_dtypes(include=[np.number]).columns
    corr_matrix = feature_df[numeric_cols].corr().abs()
    upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop = [column for column in upper_tri.columns if any(upper_tri[column] > 0.95)]
    
    if to_drop:
        logger.info(f"Dropping redundant features due to high correlation (>0.95): {to_drop}")
        feature_df = feature_df.drop(columns=to_drop)
        
    logger.info(f"Full feature engineering completed. Feature matrix shape: {feature_df.shape}")
    
    return feature_df
