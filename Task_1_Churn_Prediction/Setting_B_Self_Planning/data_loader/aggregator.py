import pandas as pd

def aggregate_geolocation(geo_df: pd.DataFrame) -> pd.DataFrame:
    """
    Responsibility:
        Gom nhóm bảng geolocation lớn (1M dòng, ~50MB) theo zip_code_prefix để tránh làm tràn bộ nhớ
        khi thực hiện join với bảng customer và seller.
        
    Task Execution:
        1. Groupby geolocation_df theo cột `geolocation_zip_code_prefix`.
        2. Tính giá trị trung bình (mean) cho `geolocation_lat` và `geolocation_lng` để làm đại diện.
        3. Chọn ngẫu nhiên hoặc lấy giá trị phổ biến nhất (ở đây dùng 'first' để nhanh và tiết kiệm tài nguyên)
           cho `geolocation_city` và `geolocation_state` trong mỗi zip code.
        4. Trả về DataFrame geolocation thu gọn (chỉ còn khoảng ~19k dòng duy nhất).
    """
    # Gom nhóm theo zip code prefix để giảm từ 1M dòng xuống khoảng ~19k dòng
    agg_df = geo_df.groupby('geolocation_zip_code_prefix').agg({
        'geolocation_lat': 'mean',
        'geolocation_lng': 'mean',
        'geolocation_city': 'first',
        'geolocation_state': 'first'
    }).reset_index()
    
    # Ép lại kiểu category cho các cột phân loại
    agg_df['geolocation_city'] = agg_df['geolocation_city'].astype('category')
    agg_df['geolocation_state'] = agg_df['geolocation_state'].astype('category')
    
    return agg_df
