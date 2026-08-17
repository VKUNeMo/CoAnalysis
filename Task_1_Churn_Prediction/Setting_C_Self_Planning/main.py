import os
import gc
import sys
import psutil
import pandas as pd
import numpy as np

# Reconfigure stdout to use UTF-8 just in case
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

import config
from data_loader.reader import load_and_optimize_csv
from data_loader.aggregator import aggregate_geolocation
from features.labeler import generate_customer_churn_labels
from features.rfm import compute_rfm_features
from features.transaction import compute_transaction_behavioral_features
from features.merger import merge_all_features
from modeling.trainer import train_all_models
from modeling.evaluator import evaluate_models
from explainability.global_explain import plot_and_save_feature_importance
from explainability.shap_explain import explain_predictions_with_shap

def log_memory(phase_name: str):
    """Su dung psutil de ghi nhan dung luong RAM hien tai dang su dung."""
    process = psutil.Process()
    mem_info = process.memory_info()
    ram_mb = mem_info.rss / (1024 * 1024)
    print(f"==> [RAM Monitor] {phase_name} | RAM tieu thu: {ram_mb:.2f} MB")
    return ram_mb

def main():
    print("=========================================================================")
    print("BAT DAU PIPELINE DU DOAN CUSTOMER CHURN (SETTING C)")
    print("=========================================================================")
    log_memory("Khoi dong he thong")

    # ==========================================
    # PHASE 1: Doc & Toi uu hoa Bo nho
    # ==========================================
    print("\n--- PHASE 1: Doc & Toi uu hoa Bo nho ---")
    
    # Doc các bang CSV
    customers_df = load_and_optimize_csv(os.path.join(config.DATA_DIR, "olist_customers_dataset.csv"), "olist_customers_dataset.csv")
    orders_df = load_and_optimize_csv(os.path.join(config.DATA_DIR, "olist_orders_dataset.csv"), "olist_orders_dataset.csv")
    items_df = load_and_optimize_csv(os.path.join(config.DATA_DIR, "olist_order_items_dataset.csv"), "olist_order_items_dataset.csv")
    payments_df = load_and_optimize_csv(os.path.join(config.DATA_DIR, "olist_order_payments_dataset.csv"), "olist_order_payments_dataset.csv")
    reviews_df = load_and_optimize_csv(os.path.join(config.DATA_DIR, "olist_order_reviews_dataset.csv"), "olist_order_reviews_dataset.csv")
    
    # Xu ly bang geolocation lon
    geo_df = load_and_optimize_csv(os.path.join(config.DATA_DIR, "olist_geolocation_dataset.csv"), "olist_geolocation_dataset.csv")
    geo_agg_df = aggregate_geolocation(geo_df)
    del geo_df
    gc.collect()
    
    # Join customer voi du lieu geolocation
    customers_df = pd.merge(
        customers_df, 
        geo_agg_df, 
        left_on='customer_zip_code_prefix', 
        right_on='geolocation_zip_code_prefix', 
        how='left'
    )
    if 'geolocation_zip_code_prefix' in customers_df.columns:
        customers_df.drop(columns=['geolocation_zip_code_prefix'], inplace=True)
        
    # Tao bang thong tin dia ly khach hang de merge sau nay
    customer_demographics = customers_df.groupby('customer_unique_id').agg({
        'geolocation_lat': 'first',
        'geolocation_lng': 'first'
    }).reset_index()
    
    log_memory("Hoan thanh Phase 1")

    # ==========================================
    # PHASE 2: Thiet lap Khung Thoi gian & Gan Nhan Churn
    # ==========================================
    print("\n--- PHASE 2: Thiet lap Khung Thoi gian & Gan Nhan Churn ---")
    
    # Tao nhan va don hang trong observation window cho tap TRAIN
    print(f"Gan nhan Churn tap TRAIN tai moc {config.TRAIN_CUTOFF.date()}")
    train_labels, train_obs_orders = generate_customer_churn_labels(
        orders_df=orders_df,
        customers_df=customers_df,
        cutoff_date=config.TRAIN_CUTOFF,
        observation_days=config.OBSERVATION_DAYS,
        prediction_days=config.PREDICTION_DAYS
    )
    
    # Tao nhan va don hang trong observation window cho tap TEST
    print(f"Gan nhan Churn tap TEST tai moc {config.TEST_CUTOFF.date()}")
    test_labels, test_obs_orders = generate_customer_churn_labels(
        orders_df=orders_df,
        customers_df=customers_df,
        cutoff_date=config.TEST_CUTOFF,
        observation_days=config.OBSERVATION_DAYS,
        prediction_days=config.PREDICTION_DAYS
    )
    
    log_memory("Hoan thanh Phase 2")

    # ==========================================
    # PHASE 3: Trich xuat Dac trung (Feature Engineering)
    # ==========================================
    print("\n--- PHASE 3: Trich xuat Dac trung ---")
    
    # 3.1 Tinh dac trung tap TRAIN
    print("Tinh toan dac trung RFM tap TRAIN...")
    train_rfm = compute_rfm_features(train_obs_orders, items_df, config.TRAIN_CUTOFF)
    print("Tinh toan dac trung giao dich hanh vi tap TRAIN...")
    train_behavioral = compute_transaction_behavioral_features(train_obs_orders, payments_df, reviews_df, items_df)
    
    # 3.2 Tinh dac trung tap TEST
    print("Tinh toan dac trung RFM tap TEST...")
    test_rfm = compute_rfm_features(test_obs_orders, items_df, config.TEST_CUTOFF)
    print("Tinh toan dac trung giao dich hanh vi tap TEST...")
    test_behavioral = compute_transaction_behavioral_features(test_obs_orders, payments_df, reviews_df, items_df)
    
    # Giai phong cac bang goc khong dung toi nua
    del orders_df, customers_df, items_df, payments_df, reviews_df, geo_agg_df
    gc.collect()
    
    log_memory("Hoan thanh Phase 3")

    # ==========================================
    # PHASE 4: Hop nhat & Xu ly Mat can bang Lop
    # ==========================================
    print("\n--- PHASE 4: Hop nhat & Xu ly Mat can bang Lop ---")
    
    # Hop nhat cac tap dac trung
    print("Hop nhat cac dac trung tap TRAIN...")
    train_master = merge_all_features(train_labels, train_rfm, train_behavioral)
    train_master = pd.merge(train_master, customer_demographics, on='customer_unique_id', how='left')
    
    # Dien gia tri thieu cho lat/lng
    mean_lat = train_master['geolocation_lat'].mean()
    mean_lng = train_master['geolocation_lng'].mean()
    train_master['geolocation_lat'] = train_master['geolocation_lat'].fillna(mean_lat if not pd.isna(mean_lat) else 0.0)
    train_master['geolocation_lng'] = train_master['geolocation_lng'].fillna(mean_lng if not pd.isna(mean_lng) else 0.0)
    
    print("Hop nhat cac dac trung tap TEST...")
    test_master = merge_all_features(test_labels, test_rfm, test_behavioral)
    test_master = pd.merge(test_master, customer_demographics, on='customer_unique_id', how='left')
    test_master['geolocation_lat'] = test_master['geolocation_lat'].fillna(mean_lat if not pd.isna(mean_lat) else 0.0)
    test_master['geolocation_lng'] = test_master['geolocation_lng'].fillna(mean_lng if not pd.isna(mean_lng) else 0.0)
    
    # Chia tach X, y
    X_train = train_master.drop(columns=['customer_unique_id', 'label'])
    y_train = train_master['label']
    X_test = test_master.drop(columns=['customer_unique_id', 'label'])
    y_test = test_master['label']
    
    # Tinh scale_pos_weight
    num_neg = (y_train == 0).sum()
    num_pos = (y_train == 1).sum()
    scale_pos_weight = num_neg / num_pos if num_pos > 0 else 1.0
    
    print(f"Ty le phan phoi lop tap TRAIN: Active (0)={num_neg}, Churn (1)={num_pos}")
    print(f"Trong so can bang lop (scale_pos_weight): {scale_pos_weight:.4f}")
    
    del train_master, test_master, train_rfm, train_behavioral, test_rfm, test_behavioral, customer_demographics
    gc.collect()
    
    log_memory("Hoan thanh Phase 4")

    # ==========================================
    # PHASE 5: Huan luyen & Danh gia Mo hinh tren CPU
    # ==========================================
    print("\n--- PHASE 5: Huan luyen & Danh gia Mo hinh ---")
    
    # Huan luyen mo hinh
    models = train_all_models(X_train, y_train, scale_pos_weight)
    
    # Danh gia mo hinh
    metrics_df = evaluate_models(models, X_test, y_test)
    
    print("\nKET QUA DANH GIA TREN TAP TEST TEMPORAL:")
    print(metrics_df.to_string(index=False))
    
    # Luu bang ket qua ra file CSV
    metrics_df.to_csv(os.path.join(config.OUTPUT_DIR, "model_evaluation_metrics.csv"), index=False)
    
    log_memory("Hoan thanh Phase 5")

    # ==========================================
    # PHASE 6: Giai thich Mo hinh
    # ==========================================
    print("\n--- PHASE 6: Giai thich Mo hinh ---")
    
    # Chon mo hinh tot nhat theo ROC-AUC de tien hanh giai thich
    best_row = metrics_df.loc[metrics_df['ROC-AUC'].idxmax()]
    best_model_name = best_row['Model']
    best_model = models[best_model_name]
    
    print(f"Mo hinh tot nhat duoc chon de giai thich: {best_model_name} (ROC-AUC={best_row['ROC-AUC']:.4f})")
    
    # 6.1 Giai thich toan cuc (Global Feature Importance)
    fi_png_path = os.path.join(config.OUTPUT_DIR, "feature_importance.png")
    plot_and_save_feature_importance(
        model=best_model,
        feature_names=list(X_train.columns),
        output_path=fi_png_path
    )
    
    # 6.2 Giai thich SHAP
    shap_png_path = os.path.join(config.OUTPUT_DIR, "shap_summary.png")
    explain_predictions_with_shap(
        model=best_model,
        X_train=X_train,
        X_test=X_test,
        summary_plot_path=shap_png_path
    )
    
    log_memory("Hoan thanh Phase 6")
    
    print("\n=========================================================================")
    print("PIPELINE DA HOAN THANH THANH CONG!")
    print(f"Tat ca ket qua, bieu do da duoc luu trong: {config.OUTPUT_DIR}")
    print("=========================================================================")

if __name__ == "__main__":
    main()
