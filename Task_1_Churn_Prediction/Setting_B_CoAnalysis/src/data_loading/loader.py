import os
import pandas as pd
import logging
from src.data_loading.memory_monitor import check_usage
from src.data_loading.config import DEFAULT_DTYPE_MAPS, REQUIRED_COLUMNS

logger = logging.getLogger("churn_prediction.data_loading.loader")

DATE_COLUMNS = [
    'order_purchase_timestamp',
    'order_approved_at',
    'order_delivered_carrier_date',
    'order_delivered_customer_date',
    'order_estimated_delivery_date',
    'shipping_limit_date',
    'review_creation_date',
    'review_answer_timestamp'
]

def load_csv_with_optimization(file_path, table_name, dtype_map=None, memory_threshold=6.0):
    """
    Load a CSV table with optimized types and validate schema, checking memory usage.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")
        
    logger.info(f"Loading table '{table_name}' from {file_path}...")
    
    # Get dtype mapping
    if dtype_map is None:
        dtype_map = DEFAULT_DTYPE_MAPS.get(table_name, {})
        
    # Check date columns to parse
    # We read header first to see which columns exist in the csv
    header_df = pd.read_csv(file_path, nrows=0)
    columns_in_file = header_df.columns.tolist()
    
    parse_dates = [col for col in DATE_COLUMNS if col in columns_in_file]
    
    # Load CSV with optimized dtypes
    # Note: Categorical or custom types are loaded directly
    df = pd.read_csv(
        file_path,
        dtype={k: v for k, v in dtype_map.items() if k in columns_in_file},
        parse_dates=parse_dates
    )
    
    # Validate required columns
    required = REQUIRED_COLUMNS.get(table_name, [])
    missing_cols = [col for col in required if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Table '{table_name}' is missing required columns: {missing_cols}")
        
    # Monitor memory usage
    mem_report = check_usage(df, threshold_gb=memory_threshold)
    
    logger.info(f"Loaded '{table_name}' successfully. Shape: {df.shape}, Memory: {mem_report['current_usage_gb']:.4f} GB")
    
    return df, mem_report['current_usage_gb'], True
