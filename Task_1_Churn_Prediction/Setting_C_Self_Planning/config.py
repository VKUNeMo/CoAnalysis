import os
import pandas as pd

# Thư mục chứa dữ liệu đầu vào (Dataset)
DATA_DIR = r"e:\Thạc Sĩ\Project\Platform hỗ trợ thử nghiệm\Dataset\Olist Brazilian E-Commerce"

# Thư mục đầu ra (Lưu trữ mô hình, kết quả đánh giá, đồ thị)
OUTPUT_DIR = r"e:\Thạc Sĩ\Project\Platform hỗ trợ thử nghiệm\Evaluation\Setting_C\outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Khung thời gian gán nhãn Churn
OBSERVATION_DAYS = 180
PREDICTION_DAYS = 90

# Temporal Split: Cutoff Dates
TRAIN_CUTOFF = pd.Timestamp("2018-02-01")
TEST_CUTOFF = pd.Timestamp("2018-05-15")

# Tham số cấu hình mô hình
MODEL_PARAMS = {
    "Logistic Regression": {
        "C": 1.0,
        "max_iter": 1000,
        "random_state": 42
    },
    "LightGBM": {
        "n_estimators": 100,
        "num_leaves": 31,
        "random_state": 42,
        "n_jobs": -1,
        "verbose": -1
    },
    "XGBoost": {
        "n_estimators": 100,
        "max_depth": 6,
        "tree_method": "hist",
        "random_state": 42,
        "n_jobs": -1
    }
}
