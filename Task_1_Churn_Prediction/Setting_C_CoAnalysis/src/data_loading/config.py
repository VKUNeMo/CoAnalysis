import os

# Base directory for the Olist dataset
DATASET_DIR = r"e:\Thạc Sĩ\Project\Platform hỗ trợ thử nghiệm\Dataset\Olist Brazilian E-Commerce"

# Default file names mapping
DATA_FILES = {
    'customers': os.path.join(DATASET_DIR, 'olist_customers_dataset.csv'),
    'geolocation': os.path.join(DATASET_DIR, 'olist_geolocation_dataset.csv'),
    'order_items': os.path.join(DATASET_DIR, 'olist_order_items_dataset.csv'),
    'order_payments': os.path.join(DATASET_DIR, 'olist_order_payments_dataset.csv'),
    'order_reviews': os.path.join(DATASET_DIR, 'olist_order_reviews_dataset.csv'),
    'orders': os.path.join(DATASET_DIR, 'olist_orders_dataset.csv'),
    'products': os.path.join(DATASET_DIR, 'olist_products_dataset.csv'),
    'sellers': os.path.join(DATASET_DIR, 'olist_sellers_dataset.csv'),
    'translation': os.path.join(DATASET_DIR, 'product_category_name_translation.csv')
}

# Type mappings for optimized memory load
DEFAULT_DTYPE_MAPS = {
    'orders': {
        'order_status': 'category'
    },
    'customers': {
        'customer_state': 'category',
        'customer_city': 'category'
    },
    'sellers': {
        'seller_state': 'category',
        'seller_city': 'category'
    },
    'order_payments': {
        'payment_type': 'category',
        'payment_sequential': 'int8',
        'payment_installments': 'int8',
        'payment_value': 'float32'
    },
    'order_items': {
        'price': 'float32',
        'freight_value': 'float32',
        'order_item_id': 'int16'
    },
    'order_reviews': {
        'review_score': 'int8'
    },
    'geolocation': {
        'geolocation_lat': 'float32',
        'geolocation_lng': 'float32'
    }
}

# Columns that must exist for each table to be valid
REQUIRED_COLUMNS = {
    'orders': ['order_id', 'customer_id', 'order_status', 'order_purchase_timestamp'],
    'customers': ['customer_id', 'customer_unique_id', 'customer_state', 'customer_city'],
    'order_items': ['order_id', 'order_item_id', 'product_id', 'seller_id', 'price', 'freight_value'],
    'order_payments': ['order_id', 'payment_sequential', 'payment_type', 'payment_installments', 'payment_value'],
    'order_reviews': ['review_id', 'order_id', 'review_score'],
    'products': ['product_id', 'product_category_name'],
    'sellers': ['seller_id', 'seller_zip_code_prefix', 'seller_city', 'seller_state'],
    'geolocation': ['geolocation_zip_code_prefix', 'geolocation_lat', 'geolocation_lng']
}
