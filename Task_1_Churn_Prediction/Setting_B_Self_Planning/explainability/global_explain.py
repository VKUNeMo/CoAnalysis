import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Any

def plot_and_save_feature_importance(model: Any, feature_names: list, output_path: str) -> None:
    """
    Responsibility:
        Trích xuất và vẽ biểu đồ tầm quan trọng toàn cục (Global Feature Importance) của mô hình tốt nhất.
        
    Task Execution:
        1. Kiểm tra loại mô hình:
           - Nếu là LightGBM/XGBoost: sử dụng thuộc tính `feature_importances_`.
           - Nếu là Logistic Regression: sử dụng trị tuyệt đối của hệ số `coef_[0]`.
        2. Tạo DataFrame lưu thông tin đặc trưng và điểm quan trọng tương ứng, sắp xếp giảm dần.
        3. Lưu danh sách này ra file CSV phục vụ kiểm tra chi tiết.
        4. Vẽ biểu đồ cột ngang (Horizontal Bar Chart) hiển thị Top 15 đặc trưng quan trọng nhất bằng matplotlib.
        5. Lưu biểu đồ dưới dạng file ảnh PNG vào `output_path`.
    """
    # 1. Trích xuất tầm quan trọng đặc trưng
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
    elif hasattr(model, 'named_steps') and 'lr' in model.named_steps:
        # Trường hợp Logistic Regression trong sklearn Pipeline
        importances = np.abs(model.named_steps['lr'].coef_[0])
    elif hasattr(model, 'coef_'):
        importances = np.abs(model.coef_[0])
    else:
        raise ValueError("Mô hình không hỗ trợ trích xuất hệ số hoặc tầm quan trọng đặc trưng.")
        
    # 2. Tạo DataFrame lưu đặc trưng và điểm quan trọng
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values(by='importance', ascending=False).reset_index(drop=True)
    
    # 3. Lưu danh sách ra file CSV
    csv_path = output_path.replace('.png', '.csv')
    importance_df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"Đã lưu bảng Feature Importance vào CSV: {csv_path}")
    
    # 4. Vẽ biểu đồ cột ngang hiển thị Top 15 đặc trưng
    top_n = min(15, len(importance_df))
    top_features = importance_df.head(top_n).sort_values(by='importance', ascending=True)
    
    plt.figure(figsize=(10, 6))
    plt.barh(top_features['feature'], top_features['importance'], color='skyblue', edgecolor='gray')
    plt.xlabel('Tầm quan trọng (Importance Score)')
    plt.ylabel('Đặc trưng (Features)')
    plt.title(f'Top {top_n} Đặc trưng Quan trọng Nhất')
    plt.tight_layout()
    
    # 5. Lưu biểu đồ dạng PNG
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Đã lưu biểu đồ Feature Importance vào PNG: {output_path}")
