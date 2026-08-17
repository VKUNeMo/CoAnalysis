import pandas as pd
from typing import Tuple

def generate_customer_churn_labels(
    orders_df: pd.DataFrame, 
    customers_df: pd.DataFrame, 
    cutoff_date: pd.Timestamp, 
    observation_days: int = 180, 
    prediction_days: int = 90
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Responsibility:
        Xác định danh sách khách hàng hoạt động (Active) trong Observation Window và gán nhãn Churn (0/1)
        dựa trên sự xuất hiện của đơn hàng trong Prediction Window.
        
    Task Execution:
        1. Join orders_df với customers_df theo `customer_id` để lấy `customer_unique_id`.
        2. Xác định Observation Window: [cutoff_date - observation_days, cutoff_date].
        3. Xác định Prediction Window: (cutoff_date, cutoff_date + prediction_days].
        4. Lọc tất cả các đơn hàng thuộc Observation Window. Những khách hàng có ít nhất 1 đơn hàng trong khoảng này
           sẽ được giữ lại làm tập mẫu nghiên cứu (Active Customers).
        5. Lọc tất cả các đơn hàng thuộc Prediction Window.
        6. Gán nhãn:
           - Churn (1): Nếu customer_unique_id có trong tập Active nhưng KHÔNG có đơn hàng nào trong Prediction Window.
           - Active (0): Nếu customer_unique_id có trong tập Active và CÓ ít nhất 1 đơn hàng trong Prediction Window.
        7. Trả về:
           - df_labels: DataFrame chứa [customer_unique_id, label (0 hoặc 1)]
           - df_obs_orders: DataFrame chứa các đơn hàng trong Observation Window của các khách hàng này để tính features.
    """
    # 1. Join orders với customers để lấy customer_unique_id
    merged_orders = pd.merge(
        orders_df[['order_id', 'customer_id', 'order_status', 'order_purchase_timestamp', 
                   'order_delivered_customer_date', 'order_estimated_delivery_date']],
        customers_df[['customer_id', 'customer_unique_id']],
        on='customer_id',
        how='inner'
    )
    
    # Định nghĩa các mốc thời gian
    obs_start = cutoff_date - pd.Timedelta(days=observation_days)
    obs_end = cutoff_date
    pred_start = cutoff_date
    pred_end = cutoff_date + pd.Timedelta(days=prediction_days)
    
    # 4. Lọc đơn hàng trong Observation Window
    df_obs_orders = merged_orders[
        (merged_orders['order_purchase_timestamp'] >= obs_start) & 
        (merged_orders['order_purchase_timestamp'] <= obs_end)
    ].copy()
    
    # Danh sách các khách hàng Active trong Observation Window
    active_customers = df_obs_orders['customer_unique_id'].unique()
    
    # Lọc lại df_obs_orders để chắc chắn chỉ chứa các active_customers (bản thân nó đã đúng, nhưng đảm bảo an toàn)
    df_obs_orders = df_obs_orders[df_obs_orders['customer_unique_id'].isin(active_customers)]
    
    # 5. Lọc đơn hàng trong Prediction Window
    df_pred_orders = merged_orders[
        (merged_orders['order_purchase_timestamp'] > pred_start) & 
        (merged_orders['order_purchase_timestamp'] <= pred_end)
    ].copy()
    
    # Danh sách các khách hàng có đơn hàng trong Prediction Window
    pred_customers = set(df_pred_orders['customer_unique_id'].unique())
    
    # 6. Gán nhãn Churn (1) hoặc Active (0)
    labels = []
    for cust_id in active_customers:
        # Nếu không mua hàng trong Prediction Window -> Churn (1), ngược lại -> Active (0)
        label = 0 if cust_id in pred_customers else 1
        labels.append({
            'customer_unique_id': cust_id,
            'label': label
        })
        
    df_labels = pd.DataFrame(labels)
    
    return df_labels, df_obs_orders
