import os

DATA_DIR = r"e:\Thạc Sĩ\Project\Platform hỗ trợ thử nghiệm\Dataset\Olist Brazilian E-Commerce"

CSV_FILES = {
    'orders': 'olist_orders_dataset.csv',
    'customers': 'olist_customers_dataset.csv',
    'order_payments': 'olist_order_payments_dataset.csv',
    'order_items': 'olist_order_items_dataset.csv',
    'sellers': 'olist_sellers_dataset.csv',
    'products': 'olist_products_dataset.csv',
    'geolocation': 'olist_geolocation_dataset.csv',
    'order_reviews': 'olist_order_reviews_dataset.csv',
    'product_category_name_translation': 'product_category_name_translation.csv'
}

REQUIRED_COLUMNS = {
    'orders': [
        'order_id', 'customer_id', 'order_status', 
        'order_purchase_timestamp', 'order_estimated_delivery_date', 
        'order_delivered_customer_date'
    ],
    'customers': [
        'customer_id', 'customer_unique_id', 'customer_city', 'customer_state'
    ],
    'order_payments': [
        'order_id', 'payment_value', 'payment_type'
    ],
    'order_items': [
        'order_id', 'product_id', 'seller_id', 'price', 'freight_value'
    ],
    'sellers': [
        'seller_id', 'seller_city', 'seller_state'
    ],
    'products': [
        'product_id', 'product_category_name'
    ],
    'order_reviews': [
        'order_id', 'review_score'
    ],
    'product_category_name_translation': [
        'product_category_name', 'product_category_name_english'
    ]
}

VALIDATION_THRESHOLDS = {
    'missing_rate_threshold': 0.1,  # Warn if missing rate exceeds this for key columns
    'late_rate_threshold': 0.2     # Normal late rate threshold reference
}
