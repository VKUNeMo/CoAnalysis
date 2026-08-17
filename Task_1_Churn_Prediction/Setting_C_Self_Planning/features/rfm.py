import pandas as pd

def compute_rfm_features(obs_orders_df: pd.DataFrame, items_df: pd.DataFrame, cutoff_date: pd.Timestamp) -> pd.DataFrame:
    """
    Responsibility:
        Tính toán các đặc trưng RFM truyền thống từ dữ liệu lịch sử mua hàng của khách hàng trong Observation Window.
        
    Task Execution:
        1. Kết nối obs_orders_df với items_df qua `order_id` để lấy thông tin giá sản phẩm (`price`).
        2. Nhóm dữ liệu theo `customer_unique_id`.
        3. Tính toán:
           - Recency (R): Số ngày từ ngày đặt hàng cuối cùng (`order_purchase_timestamp`) đến mốc `cutoff_date`.
           - Frequency (F): Tổng số đơn hàng duy nhất (`order_id`) mà khách hàng đã thực hiện.
           - Monetary (M): Tổng giá trị chi tiêu (tổng `price` của toàn bộ các sản phẩm đã mua).
           - Average Monetary: Trung bình giá trị của mỗi đơn hàng.
        4. Trả về DataFrame chứa [customer_unique_id, recency, frequency, monetary, avg_monetary].
    """
    # 1. Kết nối obs_orders_df với items_df để có thông tin giá sản phẩm
    # Chỉ giữ các cột cần thiết để tiết kiệm RAM
    merged = pd.merge(
        obs_orders_df[['order_id', 'customer_unique_id', 'order_purchase_timestamp']],
        items_df[['order_id', 'price']],
        on='order_id',
        how='left'
    )
    
    # Điền giá trị 0 cho giá nếu không tìm thấy item tương ứng
    merged['price'] = merged['price'].fillna(0.0)
    
    # 2. Gom nhóm theo customer_unique_id
    grouped = merged.groupby('customer_unique_id')
    
    # 3. Tính toán các giá trị RFM
    # Recency: Số ngày từ ngày đặt hàng cuối cùng đến cutoff_date
    max_purchase_date = grouped['order_purchase_timestamp'].max()
    recency = (cutoff_date - max_purchase_date).dt.total_seconds() / 86400.0
    
    # Frequency: Tổng số đơn hàng duy nhất
    frequency = grouped['order_id'].nunique()
    
    # Monetary: Tổng giá trị chi tiêu (tổng price)
    monetary = grouped['price'].sum()
    
    # Average Monetary: Monetary / Frequency
    avg_monetary = monetary / frequency
    
    # Tạo DataFrame kết quả
    rfm_df = pd.DataFrame({
        'recency': recency,
        'frequency': frequency,
        'monetary': monetary,
        'avg_monetary': avg_monetary
    }).reset_index()
    
    # Tối ưu hóa kiểu dữ liệu
    rfm_df['recency'] = rfm_df['recency'].astype('float32')
    rfm_df['frequency'] = rfm_df['frequency'].astype('int32')
    rfm_df['monetary'] = rfm_df['monetary'].astype('float32')
    rfm_df['avg_monetary'] = rfm_df['avg_monetary'].astype('float32')
    
    return rfm_df
