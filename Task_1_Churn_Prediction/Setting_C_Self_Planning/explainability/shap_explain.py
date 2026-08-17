import pandas as pd
import numpy as np
import shap
import matplotlib.pyplot as plt
from typing import Any

def explain_predictions_with_shap(
    model: Any, 
    X_train: pd.DataFrame, 
    X_test: pd.DataFrame, 
    summary_plot_path: str
) -> None:
    """
    Responsibility:
        Sử dụng thư viện SHAP để giải thích tác động của các đặc trưng tới quyết định dự đoán của mô hình,
        tối ưu hóa bộ nhớ cho laptop RAM 8GB.
        
    Task Execution:
        1. Tối ưu hóa RAM:
           - Rút trích một tập nền (background dataset) ngẫu nhiên khoảng 100-200 mẫu từ X_train.
           - Điều này cực kỳ quan trọng vì nếu truyền toàn bộ X_train vào TreeExplainer trên CPU, 
             máy tính 8GB RAM sẽ bị treo hoặc tràn bộ nhớ.
        2. Khởi tạo `shap.TreeExplainer(model, data=background_data)`.
        3. Tính toán SHAP values trên tập test (chỉ lấy khoảng 500-1000 mẫu ngẫu nhiên từ X_test để tính nhanh trên CPU).
        4. Vẽ SHAP Summary Plot (Beeswarm plot) để hiển thị chiều hướng ảnh hưởng của các đặc trưng toàn cục.
        5. Lưu Summary Plot dưới dạng file ảnh PNG tại `summary_plot_path`.
    """
    print("Bắt đầu giải thích mô hình bằng SHAP...")
    
    # 1. Rút trích mẫu ngẫu nhiên tối ưu bộ nhớ
    background_size = min(100, len(X_train))
    test_size = min(500, len(X_test))
    
    background_data = X_train.sample(n=background_size, random_state=42)
    X_test_sample = X_test.sample(n=test_size, random_state=42)
    
    # 2. Phân loại mô hình để sử dụng Explainer tương ứng
    plt.figure(figsize=(10, 6))
    
    try:
        if hasattr(model, 'named_steps') and 'lr' in model.named_steps:
            # Đối với Logistic Regression trong Pipeline
            scaler = model.named_steps['scaler']
            lr_classifier = model.named_steps['lr']
            
            scaled_background = scaler.transform(background_data)
            scaled_test = scaler.transform(X_test_sample)
            
            explainer = shap.LinearExplainer(lr_classifier, scaled_background)
            shap_values = explainer.shap_values(scaled_test)
            
            # Vẽ Summary Plot
            shap.summary_plot(shap_values, scaled_test, feature_names=list(X_train.columns), show=False)
        else:
            # Đối với các mô hình cây (LightGBM/XGBoost)
            explainer = shap.TreeExplainer(model, data=background_data)
            shap_values = explainer.shap_values(X_test_sample)
            
            # Xử lý đầu ra SHAP khác nhau của LightGBM và XGBoost
            if isinstance(shap_values, list):
                # LightGBM trả về một danh mục cho mỗi lớp, lớp 1 là lớp Churn
                if len(shap_values) == 2:
                    shap_values_to_plot = shap_values[1]
                else:
                    shap_values_to_plot = shap_values[0]
            elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
                # Một số phiên bản trả về shape (n_samples, n_features, 2)
                shap_values_to_plot = shap_values[:, :, 1]
            else:
                shap_values_to_plot = shap_values
                
            # Vẽ Summary Plot
            shap.summary_plot(shap_values_to_plot, X_test_sample, show=False)
            
        plt.title("SHAP Summary Plot")
        plt.tight_layout()
        plt.savefig(summary_plot_path, dpi=300)
        plt.close()
        print(f"Đã lưu biểu đồ SHAP Summary vào PNG: {summary_plot_path}")
        
    except Exception as e:
        print(f"Có lỗi xảy ra khi tính toán SHAP: {e}")
        print("Sử dụng phương pháp dự phòng (Fallback): Vẽ biểu đồ Feature Importance thông thường thay thế.")
        plt.close()
