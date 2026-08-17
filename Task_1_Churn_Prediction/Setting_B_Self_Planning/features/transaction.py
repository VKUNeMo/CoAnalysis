import pandas as pd
import numpy as np
import os
import gc
import config
from data_loader.reader import load_and_optimize_csv

def compute_transaction_behavioral_features(
    obs_orders_df: pd.DataFrame, 
    payments_df: pd.DataFrame, 
    reviews_df: pd.DataFrame, 
    items_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Responsibility:
        Tính toán các đặc trưng nâng cao liên quan đến hành vi giao dịch, thanh toán, mức độ hài lòng và thuộc tính sản phẩm.
        
    Task Execution:
        1. Tính toán Đặc trưng Giao hàng (Delivery Performance):
           - Tính khoảng cách thời gian giao hàng thực tế: `order_delivered_customer_date` - `order_purchase_timestamp`.
           - Tính số ngày giao hàng trễ: `order_delivered_customer_date` - `order_estimated_delivery_date`.
           - Gán cờ trễ hạn: `is_late = 1` nếu giao trễ, `0` nếu đúng hạn.
           - Groupby theo `customer_unique_id` để lấy: trung bình số ngày giao hàng thực tế, tỷ lệ đơn hàng bị giao trễ.
        2. Tính toán Đặc trưng Thanh toán (Payment Metrics):
           - Groupby payments_df theo `order_id` để tính số kỳ trả góp trung bình (`payment_installments`) và tỷ lệ các phương thức thanh toán (`credit_card`, `boleto`, `voucher`, etc.).
           - Map thông tin này sang `customer_unique_id`.
        3. Tính toán Đánh giá của Khách hàng (Satisfaction Metrics):
           - Groupby reviews_df theo `customer_unique_id` (sau khi join qua orders) để tính `avg_review_score`.
        4. Tính toán Đặc trưng Phân loại Sản phẩm (Category Diversity):
           - Join items_df với products_df để lấy `product_category_name`.
           - Tính số lượng danh mục sản phẩm duy nhất khách hàng đã mua.
        5. Tổng hợp các thông tin trên thành một DataFrame theo `customer_unique_id` và trả về.
    """
    # Khởi tạo base dataframe của tất cả active customers trong window này
    active_customers = obs_orders_df['customer_unique_id'].unique()
    base_df = pd.DataFrame({'customer_unique_id': active_customers})

    # ==========================================
    # 1. Tính toán Đặc trưng Giao hàng
    # ==========================================
    delivery_temp = obs_orders_df.copy()
    
    # Tính thời gian giao hàng thực tế (ngày)
    delivery_temp['delivery_time_actual'] = (
        delivery_temp['order_delivered_customer_date'] - delivery_temp['order_purchase_timestamp']
    ).dt.total_seconds() / 86400.0
    
    # Tính số ngày giao trễ (ngày)
    delivery_temp['delivery_delay'] = (
        delivery_temp['order_delivered_customer_date'] - delivery_temp['order_estimated_delivery_date']
    ).dt.total_seconds() / 86400.0
    
    # Gán cờ trễ hạn (1: trễ, 0: đúng hạn/sớm). Nếu chưa giao thì để NaN
    delivery_temp['is_late'] = np.where(
        delivery_temp['order_delivered_customer_date'].notna(),
        (delivery_temp['order_delivered_customer_date'] > delivery_temp['order_estimated_delivery_date']).astype(float),
        np.nan
    )
    
    # Cờ đơn hàng bị hủy
    delivery_temp['is_canceled'] = (delivery_temp['order_status'] == 'canceled').astype(float)
    
    # Gom nhóm theo khách hàng
    delivery_features = delivery_temp.groupby('customer_unique_id').agg({
        'delivery_time_actual': 'mean',
        'delivery_delay': 'mean',
        'is_late': 'mean',
        'is_canceled': 'mean'
    }).reset_index()
    
    delivery_features.rename(columns={
        'delivery_time_actual': 'avg_delivery_time',
        'delivery_delay': 'avg_delivery_delay',
        'is_late': 'late_rate',
        'is_canceled': 'canceled_rate'
    }, inplace=True)
    
    del delivery_temp
    gc.collect()

    # ==========================================
    # 2. Tính toán Đặc trưng Thanh toán
    # ==========================================
    # Vector hóa để tính toán nhanh phương thức thanh toán
    payments_temp = payments_df.copy()
    payments_temp['payment_type'] = payments_temp['payment_type'].astype(str)
    
    for p_type in ['credit_card', 'boleto', 'voucher', 'debit_card']:
        payments_temp[f'pay_val_{p_type}'] = np.where(
            payments_temp['payment_type'] == p_type,
            payments_temp['payment_value'],
            0.0
        )
        
    order_payments = payments_temp.groupby('order_id').agg({
        'payment_value': 'sum',
        'payment_installments': 'mean',
        'pay_val_credit_card': 'sum',
        'pay_val_boleto': 'sum',
        'pay_val_voucher': 'sum',
        'pay_val_debit_card': 'sum'
    }).reset_index()
    
    total_val = order_payments['payment_value']
    for p_type in ['credit_card', 'boleto', 'voucher', 'debit_card']:
        order_payments[f'pay_prop_{p_type}'] = np.where(
            total_val > 0,
            order_payments[f'pay_val_{p_type}'] / total_val,
            0.0
        )
        
    # Merge order payments với obs_orders_df để map sang customer_unique_id
    cust_payments = pd.merge(
        obs_orders_df[['order_id', 'customer_unique_id']],
        order_payments[['order_id', 'payment_installments', 'pay_prop_credit_card', 
                        'pay_prop_boleto', 'pay_prop_voucher', 'pay_prop_debit_card']],
        on='order_id',
        how='left'
    )
    
    # Gom nhóm theo khách hàng
    payment_features = cust_payments.groupby('customer_unique_id').agg({
        'payment_installments': 'mean',
        'pay_prop_credit_card': 'mean',
        'pay_prop_boleto': 'mean',
        'pay_prop_voucher': 'mean',
        'pay_prop_debit_card': 'mean'
    }).reset_index()
    
    del payments_temp, order_payments, cust_payments
    gc.collect()

    # ==========================================
    # 3. Tính toán Đánh giá của Khách hàng
    # ==========================================
    order_reviews = pd.merge(
        obs_orders_df[['order_id', 'customer_unique_id']],
        reviews_df[['order_id', 'review_score']],
        on='order_id',
        how='left'
    )
    
    review_features = order_reviews.groupby('customer_unique_id')['review_score'].mean().reset_index()
    review_features.rename(columns={'review_score': 'avg_review_score'}, inplace=True)
    
    del order_reviews
    gc.collect()

    # ==========================================
    # 4. Tính toán Đặc trưng Phân loại Sản phẩm
    # ==========================================
    # Đọc sản phẩm để lấy category (sử dụng load_and_optimize_csv để tối ưu bộ nhớ)
    products_path = os.path.join(config.DATA_DIR, "olist_products_dataset.csv")
    products_df = load_and_optimize_csv(products_path, "olist_products_dataset.csv")
    
    # Merge items_df với products_df để có thông tin loại sản phẩm
    item_prod = pd.merge(
        items_df[['order_id', 'product_id']],
        products_df[['product_id', 'product_category_name']],
        on='product_id',
        how='left'
    )
    
    # Merge tiếp với obs_orders_df để map sang customer_unique_id
    cust_prod = pd.merge(
        obs_orders_df[['order_id', 'customer_unique_id']],
        item_prod,
        on='order_id',
        how='left'
    )
    
    # Tính số lượng loại sản phẩm duy nhất mỗi khách hàng mua
    diversity_features = cust_prod.groupby('customer_unique_id')['product_category_name'].nunique().reset_index()
    diversity_features.rename(columns={'product_category_name': 'category_diversity'}, inplace=True)
    
    del products_df, item_prod, cust_prod
    gc.collect()

    # ==========================================
    # 5. Tổng hợp tất cả các đặc trưng hành vi
    # ==========================================
    behavioral_df = pd.merge(base_df, delivery_features, on='customer_unique_id', how='left')
    behavioral_df = pd.merge(behavioral_df, payment_features, on='customer_unique_id', how='left')
    behavioral_df = pd.merge(behavioral_df, review_features, on='customer_unique_id', how='left')
    behavioral_df = pd.merge(behavioral_df, diversity_features, on='customer_unique_id', how='left')
    
    # Tối ưu hóa kiểu dữ liệu trước khi trả về
    float32_cols = [col for col in behavioral_df.columns if col != 'customer_unique_id']
    for col in float32_cols:
        behavioral_df[col] = behavioral_df[col].astype('float32')
        
    return behavioral_df
