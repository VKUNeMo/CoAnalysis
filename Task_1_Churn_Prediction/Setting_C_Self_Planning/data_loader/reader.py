import pandas as pd
import gc
import os
from typing import Dict

def load_and_optimize_csv(file_path: str, table_name: str) -> pd.DataFrame:
    """
    Responsibility:
        Đọc file CSV của Olist với encoding phù hợp (mặc định UTF-8 hoặc Latin-1 nếu lỗi),
        thực hiện ép kiểu dữ liệu ngay lập tức để tiết kiệm bộ nhớ RAM.
    
    Task Execution:
        1. Đọc file CSV bằng pd.read_csv.
        2. Dựa vào table_name, tự động ép kiểu các cột datetime (ví dụ: các cột chứa '_timestamp', '_date', '_at').
        3. Tối ưu kiểu dữ liệu số:
           - Chuyển float64 sang float32.
           - Chuyển int64 sang int32 hoặc int16 (tùy thuộc vào max_value của cột).
        4. Tối ưu kiểu phân loại:
           - Chuyển các cột string có số lượng giá trị duy nhất ít (như order_status, payment_type, state, city) thành category.
        5. Gọi gc.collect() để thu hồi bộ nhớ trống.
        6. Trả về DataFrame đã tối ưu.
    """
    # 1. Đọc file CSV (thử UTF-8 trước, nếu lỗi chuyển sang Latin-1)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} không tồn tại.")
        
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='latin-1')

    # 2. Ép kiểu cột datetime
    datetime_cols = [col for col in df.columns if any(x in col for x in ['_timestamp', '_date', '_at'])]
    for col in datetime_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # 3. Tối ưu kiểu số và kiểu chuỗi phân loại
    for col in df.columns:
        if col in datetime_cols:
            continue
        
        col_type = df[col].dtype
        
        # Tối ưu số nguyên
        if col_type == 'int64':
            c_min = df[col].min()
            c_max = df[col].max()
            if c_min > -128 and c_max < 127:
                df[col] = df[col].astype('int8')
            elif c_min > -32768 and c_max < 32767:
                df[col] = df[col].astype('int16')
            elif c_min > -2147483648 and c_max < 2147483647:
                df[col] = df[col].astype('int32')
            else:
                df[col] = df[col].astype('int64')
                
        # Tối ưu số thực
        elif col_type == 'float64':
            df[col] = df[col].astype('float32')
            
        # Tối ưu chuỗi phân loại
        elif col_type == 'object':
            # Các cột phân loại có cardinality thấp được ép kiểu category để tiết kiệm RAM
            categorical_keywords = ['status', 'type', 'state', 'city', 'category', 'prefix']
            if any(kw in col for kw in categorical_keywords) or df[col].nunique() < 5000:
                df[col] = df[col].astype('category')

    # 5. Giải phóng bộ nhớ thừa
    gc.collect()
    
    return df
