import os

# Base directory for the Olist dataset
DATASET_DIR = r"e:\Thạc Sĩ\Project\Platform hỗ trợ thử nghiệm\Dataset\Olist Brazilian E-Commerce"

# Output directory for charts and final notebook
OUTPUT_DIR = r"e:\Thạc Sĩ\Project\Platform hỗ trợ thử nghiệm\Evaluation\Task_2_Setting_C\output"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# File names mapping
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

# Low-cardinality columns to convert to category dtype for RAM optimization
CATEGORY_COLUMNS = {
    'orders': ['order_status'],
    'customers': ['customer_state', 'customer_city'],
    'sellers': ['seller_state', 'seller_city'],
    'order_payments': ['payment_type'],
}

# Numerical columns to downcast
NUMERICAL_DOWNCAST = {
    'order_items': {
        'price': 'float32',
        'freight_value': 'float32',
        'order_item_id': 'int16'
    },
    'order_payments': {
        'payment_value': 'float32',
        'payment_sequential': 'int8',
        'payment_installments': 'int8'
    },
    'order_reviews': {
        'review_score': 'int8'
    },
    'geolocation': {
        'geolocation_lat': 'float32',
        'geolocation_lng': 'float32'
    }
}
