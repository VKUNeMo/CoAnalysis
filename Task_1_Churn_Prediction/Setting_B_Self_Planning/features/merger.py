import pandas as pd
import numpy as np

def merge_all_features(
    labels_df: pd.DataFrame, 
    rfm_df: pd.DataFrame, 
    behavioral_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Responsibility:
        Ghép nhãn và tất cả các đặc trưng đã tính toán thành một bảng master duy nhất cho mô hình học máy.
        
    Task Execution:
        1. Thực hiện left join labels_df với rfm_df theo `customer_unique_id`.
        2. Tiếp tục left join với behavioral_df theo `customer_unique_id`.
        3. Xử lý các giá trị khuyết (Missing Values):
           - Điền `0` cho các đặc trưng tần suất, giá trị giao dịch nếu thiếu.
           - Điền giá trị trung vị (median) cho các cột như `avg_review_score` hoặc thời gian giao hàng.
           - Tạo thêm các cờ báo hiệu giá trị bị thiếu nếu tỷ lệ thiếu lớn (ví dụ: `is_review_missing`).
        4. Trả về bảng Master Feature DataFrame hoàn chỉnh.
    """
    # 1. Hợp nhất các DataFrame theo customer_unique_id
    master_df = pd.merge(labels_df, rfm_df, on='customer_unique_id', how='left')
    master_df = pd.merge(master_df, behavioral_df, on='customer_unique_id', how='left')
    
    # 2. Tạo cờ báo hiệu giá trị khuyết thiếu (như review_score bị thiếu hoặc thông tin giao nhận thiếu)
    master_df['is_review_missing'] = master_df['avg_review_score'].isna().astype('float32')
    master_df['is_delivery_missing'] = master_df['avg_delivery_time'].isna().astype('float32')
    
    # 3. Điền giá trị khuyết thiếu (Imputation)
    # RFM features
    master_df['recency'] = master_df['recency'].fillna(master_df['recency'].median())
    master_df['frequency'] = master_df['frequency'].fillna(1).astype('int32')
    master_df['monetary'] = master_df['monetary'].fillna(0.0)
    master_df['avg_monetary'] = master_df['avg_monetary'].fillna(0.0)
    
    # Delivery performance
    master_df['avg_delivery_time'] = master_df['avg_delivery_time'].fillna(master_df['avg_delivery_time'].median() if not master_df['avg_delivery_time'].isna().all() else 12.0)
    master_df['avg_delivery_delay'] = master_df['avg_delivery_delay'].fillna(master_df['avg_delivery_delay'].median() if not master_df['avg_delivery_delay'].isna().all() else 0.0)
    master_df['late_rate'] = master_df['late_rate'].fillna(0.0)
    master_df['canceled_rate'] = master_df['canceled_rate'].fillna(0.0)
    
    # Payment metrics
    master_df['payment_installments'] = master_df['payment_installments'].fillna(master_df['payment_installments'].median() if not master_df['payment_installments'].isna().all() else 1.0)
    pay_prop_cols = [col for col in master_df.columns if col.startswith('pay_prop_')]
    for col in pay_prop_cols:
        master_df[col] = master_df[col].fillna(0.0)
        
    # Satisfaction reviews
    master_df['avg_review_score'] = master_df['avg_review_score'].fillna(master_df['avg_review_score'].median() if not master_df['avg_review_score'].isna().all() else 5.0)
    
    # Product categories
    master_df['category_diversity'] = master_df['category_diversity'].fillna(1.0)
    
    # Tối ưu hóa bộ nhớ
    for col in master_df.columns:
        if col == 'customer_unique_id':
            continue
        elif col == 'label' or col == 'frequency':
            master_df[col] = master_df[col].astype('int32')
        else:
            master_df[col] = master_df[col].astype('float32')
            
    return master_df
