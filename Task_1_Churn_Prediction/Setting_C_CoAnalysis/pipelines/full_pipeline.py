import os
import sys
import logging
import pandas as pd
from typing import Dict, Any

# Ensure project root is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.logger import setup_logger
from src.utils.config_loader import get_config
from src.utils.file_io import save_json, save_pickle
from src.data_loading.loader import load_csv_with_optimization
from src.data_splitting.temporal_splitter import temporal_train_test_split
from src.data_splitting.validator import validate_temporal_split as validate_split_dates
from src.churn_labeling.validator import validate_labels
from src.modeling.feature_engineering import compute_advanced_features
from src.modeling.imbalance_handler import compute_class_weights
from src.modeling.trainer import train_baseline_models, run_time_series_cv
from src.modeling.selector import select_top_models
from src.modeling.tuner import tune_hyperparameters
from src.evaluation.evaluator import optimize_threshold, compute_test_metrics
from src.evaluation.visualizer import plot_roc_curve, plot_precision_recall_curve, plot_confusion_matrix
from src.evaluation.report_generator import generate_metrics_report
from src.high_risk_list.generator import generate_high_risk_list
from src.high_risk_list.exporter import export_high_risk_list

# We imports from explainability
from src.explainability.feature_importance import extract_feature_importance, plot_feature_importance
from src.explainability.shap_analyzer import explain_model_shap
from src.explainability.interpreter import interpret_top_features

# We imports from documentation
from src.documentation.evaluation_report import generate_final_doc_evaluation_report
from src.documentation.explainability_report import generate_final_doc_explainability_report
from src.documentation.technical_doc import generate_final_doc_technical_doc
from src.documentation.user_guide import generate_final_doc_user_guide

def run_full_pipeline(config_path=None):
    # 1. Setup config and logger
    config = get_config(config_path)
    paths = config['paths']
    cohort_cfg = config['cohort']
    
    logger = setup_logger(
        name="full_pipeline",
        log_file=paths['log_file'],
        level=logging.INFO
    )
    
    logger.info("=" * 60)
    logger.info("STARTING FULL ADVANCED PIPELINE")
    logger.info("=" * 60)
    
    # Ensure directories exist
    os.makedirs(paths['output_dir'], exist_ok=True)
    os.makedirs(paths['model_dir'], exist_ok=True)
    os.makedirs(paths['data_dir'], exist_ok=True)
    
    # 2. Load raw datasets
    dataset_dir = paths['dataset_dir']
    
    logger.info("Loading all raw tables for advanced feature engineering...")
    orders_df, _, _ = load_csv_with_optimization(os.path.join(dataset_dir, 'olist_orders_dataset.csv'), 'orders', memory_threshold=config['memory']['threshold_gb'])
    customers_df, _, _ = load_csv_with_optimization(os.path.join(dataset_dir, 'olist_customers_dataset.csv'), 'customers', memory_threshold=config['memory']['threshold_gb'])
    items_df, _, _ = load_csv_with_optimization(os.path.join(dataset_dir, 'olist_order_items_dataset.csv'), 'order_items', memory_threshold=config['memory']['threshold_gb'])
    payments_df, _, _ = load_csv_with_optimization(os.path.join(dataset_dir, 'olist_order_payments_dataset.csv'), 'order_payments', memory_threshold=config['memory']['threshold_gb'])
    reviews_df, _, _ = load_csv_with_optimization(os.path.join(dataset_dir, 'olist_order_reviews_dataset.csv'), 'order_reviews', memory_threshold=config['memory']['threshold_gb'])
    products_df, _, _ = load_csv_with_optimization(os.path.join(dataset_dir, 'olist_products_dataset.csv'), 'products', memory_threshold=config['memory']['threshold_gb'])
    sellers_df, _, _ = load_csv_with_optimization(os.path.join(dataset_dir, 'olist_sellers_dataset.csv'), 'sellers', memory_threshold=config['memory']['threshold_gb'])
    geolocation_df, _, _ = load_csv_with_optimization(os.path.join(dataset_dir, 'olist_geolocation_dataset.csv'), 'geolocation', memory_threshold=config['memory']['threshold_gb'])
    translation_df, _, _ = load_csv_with_optimization(os.path.join(dataset_dir, 'product_category_name_translation.csv'), 'translation', memory_threshold=config['memory']['threshold_gb'])
    
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
    save_json(split_report, os.path.join(paths['output_dir'], 'advanced_split_report.json'))
    
    # Run validators
    logger.info("Validating temporal split and churn labels...")
    split_validation = validate_split_dates(
        train_cohort, test_cohort,
        cohort_cfg['train_cutoff'], cohort_cfg['test_cutoff']
    )
    save_json(split_validation, os.path.join(paths['output_dir'], 'advanced_split_validation.json'))
    
    label_validation = validate_labels(
        cohort_df=train_cohort,
        orders_df=orders_df,
        customers_df=customers_df,
        cutoff_date=cohort_cfg['train_cutoff'],
        churn_window_days=cohort_cfg['prediction_window_days'],
        sample_size=10,
        random_seed=42
    )
    save_json(label_validation, os.path.join(paths['output_dir'], 'advanced_label_validation.json'))
    
    # 4. Compute advanced features strictly respecting cutoffs
    logger.info("Computing advanced features (including RFM, behavioral, transactional, and geospatial)...")
    X_train_adv = compute_advanced_features(
        orders_df=orders_df, customers_df=customers_df, items_df=items_df,
        payments_df=payments_df, reviews_df=reviews_df, products_df=products_df,
        sellers_df=sellers_df, geolocation_df=geolocation_df,
        cutoff_date=cohort_cfg['train_cutoff']
    )
    
    X_test_adv = compute_advanced_features(
        orders_df=orders_df, customers_df=customers_df, items_df=items_df,
        payments_df=payments_df, reviews_df=reviews_df, products_df=products_df,
        sellers_df=sellers_df, geolocation_df=geolocation_df,
        cutoff_date=cohort_cfg['test_cutoff']
    )
    
    # Align labels with features
    train_final = pd.merge(X_train_adv, train_cohort[['customer_unique_id', 'churn_label']], on='customer_unique_id', how='inner')
    test_final = pd.merge(X_test_adv, test_cohort[['customer_unique_id', 'churn_label']], on='customer_unique_id', how='inner')
    
    logger.info(f"Final advanced train set size: {len(train_final)}, Churn rate: {train_final['churn_label'].mean():.4f}")
    logger.info(f"Final advanced test set size: {len(test_final)}, Churn rate: {test_final['churn_label'].mean():.4f}")
    
    # Save processed advanced matrices
    train_final.to_csv(os.path.join(paths['data_dir'], 'advanced_train_features.csv'), index=False)
    test_final.to_csv(os.path.join(paths['data_dir'], 'advanced_test_features.csv'), index=False)
    
    # Separate features and labels
    feature_cols = [c for c in train_final.columns if c not in ['customer_unique_id', 'churn_label']]
    
    X_train = train_final[feature_cols]
    y_train = train_final['churn_label']
    
    X_test = test_final[feature_cols]
    y_test = test_final['churn_label']
    
    # 5. Candidate models & Cross Validation
    logger.info("Training initial candidate models...")
    models_info = train_baseline_models(X_train, y_train, config['modeling'])
    
    # Run time series cross validation
    cv_results = run_time_series_cv(X_train, y_train, models_info, config['modeling'])
    save_json(cv_results.to_dict(orient='records'), os.path.join(paths['output_dir'], 'modeling_cv_results.json'))
    
    # Select top models
    top_model_names = select_top_models(cv_results, top_k=2)
    
    # 6. Hyperparameter tuning on top candidates
    logger.info("Tuning hyperparameters for top candidates...")
    best_candidate = tune_hyperparameters(X_train, y_train, top_model_names, models_info, config['modeling'])
    
    best_model = best_candidate['best_estimator']
    scaler = best_candidate['scaler']
    
    # Save best model artifacts
    prod_model_dir = os.path.join(paths['model_dir'], 'production')
    os.makedirs(prod_model_dir, exist_ok=True)
    save_pickle(best_model, os.path.join(prod_model_dir, 'best_model.pkl'))
    if scaler is not None:
        save_pickle(scaler, os.path.join(prod_model_dir, 'scaler.pkl'))
    logger.info("Best model artifacts serialized.")
    
    # 7. Threshold Optimization on validation fold (using final best model predictions on training data as surrogate)
    logger.info("Optimizing decision threshold...")
    X_train_clean = X_train.copy()
    if scaler is not None:
        X_train_clean = scaler.transform(X_train_clean)
    y_train_proba = best_model.predict_proba(X_train_clean)[:, 1]
    optimal_threshold = optimize_threshold(y_train, y_train_proba, metric='youden')
    
    # 8. Test Set Evaluation
    logger.info("Evaluating final best model on test set...")
    metrics = compute_test_metrics(best_model, X_test, y_test, optimal_threshold, scaler=scaler)
    
    # Generate charts
    viz_dir = os.path.join(paths['output_dir'], 'visualizations')
    os.makedirs(viz_dir, exist_ok=True)
    
    X_test_clean = X_test.copy()
    if scaler is not None:
        X_test_clean = scaler.transform(X_test_clean)
    y_test_proba = best_model.predict_proba(X_test_clean)[:, 1]
    y_test_pred = (y_test_proba >= optimal_threshold).astype(int)
    
    plot_roc_curve(y_test, y_test_proba, os.path.join(viz_dir, 'best_model_roc_curve.png'))
    plot_precision_recall_curve(y_test, y_test_proba, os.path.join(viz_dir, 'best_model_pr_curve.png'))
    plot_confusion_matrix(y_test, y_test_pred, os.path.join(viz_dir, 'best_model_confusion_matrix.png'))
    
    # Save unified metrics report
    generate_metrics_report(metrics, split_validation, os.path.join(paths['output_dir'], 'reports', 'evaluation_metrics_report.md'))
    
    # 9. High-Risk Customer List Generation
    logger.info("Generating high-risk customer list...")
    high_risk_list = generate_high_risk_list(
        model=best_model, X=X_test, customer_ids=test_final['customer_unique_id'],
        threshold=optimal_threshold, scaler=scaler
    )
    
    # Export list
    high_risk_path = os.path.join(paths['output_dir'], 'high_risk_lists', 'high_risk_customers.csv')
    export_high_risk_list(high_risk_list, high_risk_path, format_type='csv')
    
    # 10. Explainability Analysis
    logger.info("Extracting feature importance and running SHAP analysis...")
    importance_df = extract_feature_importance(best_model, feature_cols, top_k=15)
    if not importance_df.empty:
        plot_feature_importance(importance_df, os.path.join(viz_dir, 'best_model_feature_importance.png'))
        
    # SHAP Explainer
    shap_results = explain_model_shap(best_model, X_test, scaler, viz_dir)
    
    # Generate business interpretation
    feature_metadata = {} # optional dictionary for business terms
    interpretation = interpret_top_features(importance_df, feature_metadata)
    
    # Save explainability report
    save_json({
        'importance': importance_df.to_dict(orient='records') if not importance_df.empty else [],
        'interpretation': interpretation
    }, os.path.join(paths['output_dir'], 'shap_explainability_results.json'))
    
    # 11. Final Documentation Reports
    logger.info("Generating final documentations for users...")
    doc_dir = os.path.join(paths['output_dir'], 'documentation')
    os.makedirs(doc_dir, exist_ok=True)
    
    generate_final_doc_evaluation_report(metrics, os.path.join(doc_dir, 'evaluation_report.md'))
    generate_final_doc_explainability_report(importance_df, interpretation, os.path.join(doc_dir, 'explainability_report.md'))
    generate_final_doc_technical_doc(config, best_candidate, X_train.columns.tolist(), os.path.join(doc_dir, 'technical_documentation.md'))
    generate_final_doc_user_guide(optimal_threshold, os.path.join(doc_dir, 'user_guide.md'))
    
    logger.info("=" * 60)
    logger.info("FULL ADVANCED PIPELINE RUN COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)

if __name__ == '__main__':
    run_full_pipeline()
