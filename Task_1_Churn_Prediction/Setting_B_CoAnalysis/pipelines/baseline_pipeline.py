import os
import sys

# Add project root to python path to resolve src imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
import logging
from src.utils.logger import setup_logger
from src.utils.config_loader import get_config
from src.utils.file_io import save_json, save_pickle
from src.data_loading.loader import load_csv_with_optimization
from src.data_splitting.temporal_splitter import temporal_train_test_split
from src.data_splitting.validator import validate_temporal_split as validate_split_dates
from src.churn_labeling.validator import validate_labels
from src.baseline.feature_engineering import compute_rfm_features
from src.baseline.trainer import train_baseline_model
from src.baseline.evaluator import evaluate_baseline
from src.baseline.visualizer import visualize_baseline_results

def run_baseline_pipeline(config_path=None):
    # 1. Setup config and logger
    config = get_config(config_path)
    paths = config['paths']
    cohort_cfg = config['cohort']
    
    logger = setup_logger(
        name="baseline_pipeline",
        log_file=paths['log_file'],
        level=logging.INFO
    )
    
    logger.info("=" * 60)
    logger.info("STARTING BASELINE PIPELINE")
    logger.info("=" * 60)
    
    # Ensure directories exist
    os.makedirs(paths['output_dir'], exist_ok=True)
    os.makedirs(paths['model_dir'], exist_ok=True)
    os.makedirs(paths['data_dir'], exist_ok=True)
    
    # 2. Load raw datasets
    dataset_dir = paths['dataset_dir']
    
    logger.info(f"Loading raw datasets from {dataset_dir}...")
    orders_df, _, _ = load_csv_with_optimization(
        os.path.join(dataset_dir, 'olist_orders_dataset.csv'), 'orders',
        memory_threshold=config['memory']['threshold_gb']
    )
    customers_df, _, _ = load_csv_with_optimization(
        os.path.join(dataset_dir, 'olist_customers_dataset.csv'), 'customers',
        memory_threshold=config['memory']['threshold_gb']
    )
    payments_df, _, _ = load_csv_with_optimization(
        os.path.join(dataset_dir, 'olist_order_payments_dataset.csv'), 'order_payments',
        memory_threshold=config['memory']['threshold_gb']
    )
    
    # 3. Create temporal cohorts and compute labels
    logger.info("Computing temporal cohorts and churn labels...")
    train_cohort, test_cohort, split_report = temporal_train_test_split(
        orders_df=orders_df,
        customers_df=customers_df,
        train_cutoff=cohort_cfg['train_cutoff'],
        test_cutoff=cohort_cfg['test_cutoff'],
        observation_window_days=cohort_cfg['observation_window_days'],
        prediction_window_days=cohort_cfg['prediction_window_days']
    )
    
    # Save split report
    save_json(split_report, os.path.join(paths['output_dir'], 'baseline_split_report.json'))
    
    # 4. Run validators
    logger.info("Validating temporal split and churn labels...")
    split_validation = validate_split_dates(
        train_cohort, test_cohort,
        cohort_cfg['train_cutoff'], cohort_cfg['test_cutoff']
    )
    save_json(split_validation, os.path.join(paths['output_dir'], 'baseline_split_validation.json'))
    
    label_validation = validate_labels(
        cohort_df=train_cohort,
        orders_df=orders_df,
        customers_df=customers_df,
        cutoff_date=cohort_cfg['train_cutoff'],
        churn_window_days=cohort_cfg['prediction_window_days'],
        sample_size=10,
        random_seed=42
    )
    save_json(label_validation, os.path.join(paths['output_dir'], 'baseline_label_validation.json'))
    
    # Save processed cohorts to disk
    train_cohort.to_csv(os.path.join(paths['data_dir'], 'train_cohort.csv'), index=False)
    test_cohort.to_csv(os.path.join(paths['data_dir'], 'test_cohort.csv'), index=False)
    logger.info("Cohorts saved as CSV.")
    
    # 5. Compute RFM features strictly respecting cutoffs
    logger.info("Computing RFM features...")
    X_train_rfm = compute_rfm_features(
        orders_df=orders_df,
        customers_df=customers_df,
        payments_df=payments_df,
        cutoff_date=cohort_cfg['train_cutoff']
    )
    
    X_test_rfm = compute_rfm_features(
        orders_df=orders_df,
        customers_df=customers_df,
        payments_df=payments_df,
        cutoff_date=cohort_cfg['test_cutoff']
    )
    
    # Align labels with RFM features
    # Ensure cohort records match features exactly
    train_final = pd.merge(X_train_rfm, train_cohort[['customer_unique_id', 'churn_label']], on='customer_unique_id', how='inner')
    test_final = pd.merge(X_test_rfm, test_cohort[['customer_unique_id', 'churn_label']], on='customer_unique_id', how='inner')
    
    logger.info(f"Final train set size: {len(train_final)}, Churn rate: {train_final['churn_label'].mean():.4f}")
    logger.info(f"Final test set size: {len(test_final)}, Churn rate: {test_final['churn_label'].mean():.4f}")
    
    # Separate features and labels
    X_train = train_final[['recency', 'frequency', 'monetary']]
    y_train = train_final['churn_label']
    
    X_test = test_final[['recency', 'frequency', 'monetary']]
    y_test = test_final['churn_label']
    
    # Save final matrices to data folder
    train_final.to_csv(os.path.join(paths['data_dir'], 'baseline_train_features.csv'), index=False)
    test_final.to_csv(os.path.join(paths['data_dir'], 'baseline_test_features.csv'), index=False)
    
    # 6. Train baseline model
    logger.info("Training baseline model...")
    model, scaler = train_baseline_model(X_train, y_train)
    
    # Save baseline model artifacts
    baseline_model_dir = os.path.join(paths['model_dir'], 'baseline')
    os.makedirs(baseline_model_dir, exist_ok=True)
    save_pickle(model, os.path.join(baseline_model_dir, 'logistic_regression.pkl'))
    save_pickle(scaler, os.path.join(baseline_model_dir, 'scaler.pkl'))
    logger.info("Baseline model and scaler serialized.")
    
    # 7. Evaluate baseline model on test set
    logger.info("Evaluating baseline model...")
    metrics, curves = evaluate_baseline(model, scaler, X_test, y_test)
    
    # Save baseline metrics
    save_json(metrics, os.path.join(paths['output_dir'], 'baseline_metrics.json'))
    
    # 8. Generate visualizations
    logger.info("Generating visualizations...")
    viz_dir = os.path.join(paths['output_dir'], 'visualizations')
    visualize_baseline_results(metrics, curves, viz_dir)
    
    logger.info("=" * 60)
    logger.info("BASELINE PIPELINE RUN COMPLETED")
    logger.info("=" * 60)

if __name__ == '__main__':
    run_baseline_pipeline()
