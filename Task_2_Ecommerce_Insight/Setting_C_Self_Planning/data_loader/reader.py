import os
import gc
import pandas as pd
import numpy as np
from config import CATEGORY_COLUMNS, NUMERICAL_DOWNCAST

def load_and_optimize_csv(file_path: str, table_name: str) -> pd.DataFrame:
    """
    Reads a CSV file, parses date columns, downcasts numeric types, and 
    converts low-cardinality string columns to category dtype to optimize memory.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    print(f"Loading table '{table_name}' from {os.path.basename(file_path)}...")
    
    # Try reading with utf-8, fallback to latin-1
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='latin-1')
        
    initial_memory = df.memory_usage(deep=True).sum() / (1024 ** 2)
    
    # 1. Parse date columns
    for col in df.columns:
        if col.endswith('_timestamp') or col.endswith('_date') or col.endswith('_at'):
            df[col] = pd.to_datetime(df[col], errors='coerce')
            
    # 2. Downcast custom numerical columns configured in config.py
    if table_name in NUMERICAL_DOWNCAST:
        for col, dtype in NUMERICAL_DOWNCAST[table_name].items():
            if col in df.columns:
                try:
                    df[col] = df[col].astype(dtype)
                except Exception as e:
                    print(f"Warning: Could not convert column {col} in {table_name} to {dtype}: {e}")

    # 3. Downcast remaining numerical columns automatically
    for col in df.columns:
        # Check if already downcasted by config, skip if so
        if table_name in NUMERICAL_DOWNCAST and col in NUMERICAL_DOWNCAST[table_name]:
            continue
            
        col_type = df[col].dtype
        if col_type == 'float64':
            df[col] = pd.to_numeric(df[col], downcast='float')
        elif col_type == 'int64':
            df[col] = pd.to_numeric(df[col], downcast='integer')
            
    # 4. Convert specific low-cardinality string columns from config to category
    if table_name in CATEGORY_COLUMNS:
        for col in CATEGORY_COLUMNS[table_name]:
            if col in df.columns:
                df[col] = df[col].astype('category')
                
    # 5. Convert any other object/string columns with low cardinality (e.g. < 100 unique values) to category
    for col in df.columns:
        if df[col].dtype == 'object' and col not in ['order_id', 'customer_id', 'customer_unique_id', 'product_id', 'seller_id', 'review_id']:
            unique_count = df[col].nunique()
            # If the column has very few unique values, cast to category
            if unique_count < 150:
                df[col] = df[col].astype('category')

    final_memory = df.memory_usage(deep=True).sum() / (1024 ** 2)
    print(f"Table '{table_name}' loaded. Memory: {initial_memory:.2f} MB -> {final_memory:.2f} MB")
    
    gc.collect()
    return df
