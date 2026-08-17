import pandas as pd
from typing import Dict, Any
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import lightgbm as lgb
import xgboost as xgb
import config

def train_all_models(X_train: pd.DataFrame, y_train: pd.Series, scale_pos_weight: float) -> Dict[str, Any]:
    """
    Responsibility:
        Huấn luyện đồng thời 3 mô hình (Logistic Regression baseline, LightGBM, XGBoost) trên CPU,
        áp dụng các cơ chế kiểm soát tài nguyên để tránh tràn bộ nhớ RAM 8GB.
        
    Task Execution:
        1. Logistic Regression (Baseline):
           - Xây dựng Pipeline gồm `StandardScaler` và `LogisticRegression`.
           - Sử dụng tham số `class_weight='balanced'` để tự động xử lý mất cân bằng lớp.
           - Huấn luyện trên CPU.
        2. LightGBM:
           - Khởi tạo `LGBMClassifier` với:
             * `n_estimators=100` (giới hạn để tiết kiệm tài nguyên).
             * `num_leaves=31` (tránh overfitting và tiết kiệm RAM).
             * `scale_pos_weight=scale_pos_weight` (xử lý mất cân bằng lớp).
             * `n_jobs=-1` (tận dụng tối đa lõi CPU).
           - Huấn luyện mô hình.
        3. XGBoost:
           - Khởi tạo `XGBClassifier` với:
             * `n_estimators=100`
             * `max_depth=6`
             * `tree_method='hist'` (BẮT BUỘC: thuật toán chia bin histogram giúp tiết kiệm RAM và CPU tối đa).
             * `scale_pos_weight=scale_pos_weight`
             * `n_jobs=-1`
           - Huấn luyện mô hình.
        4. Trả về dict chứa 3 mô hình đã được huấn luyện thành công.
    """
    models = {}
    
    # 1. Logistic Regression Baseline
    print("Huấn luyện Logistic Regression...")
    lr_params = config.MODEL_PARAMS["Logistic Regression"]
    lr_model = LogisticRegression(class_weight='balanced', **lr_params)
    lr_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('lr', lr_model)
    ])
    lr_pipeline.fit(X_train, y_train)
    models["Logistic Regression"] = lr_pipeline
    
    # 2. LightGBM
    print("Huấn luyện LightGBM...")
    lgb_params = config.MODEL_PARAMS["LightGBM"].copy()
    lgb_params["scale_pos_weight"] = 1.0
    lgb_model = lgb.LGBMClassifier(**lgb_params)
    lgb_model.fit(X_train, y_train)
    models["LightGBM"] = lgb_model
    
    # 3. XGBoost
    print("Huấn luyện XGBoost...")
    xgb_params = config.MODEL_PARAMS["XGBoost"].copy()
    xgb_params["scale_pos_weight"] = 1.0
    xgb_model = xgb.XGBClassifier(**xgb_params)
    xgb_model.fit(X_train, y_train)
    models["XGBoost"] = xgb_model
    
    return models
