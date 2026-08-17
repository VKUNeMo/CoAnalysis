import os
import sys
import gc
import json
import joblib

# Reconfigure stdout to use UTF-8 to prevent encoding issues with Vietnamese paths
sys.stdout.reconfigure(encoding='utf-8')

# Add the current directory to sys.path to allow imports when running directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_loader import load_cleaned_datasets
from features import build_features_and_labels
from train import temporal_split, train_model
from explain import explain_model

def run_pipeline(data_dir, output_dir):
    """
    Runs the complete customer churn prediction pipeline.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Load data
    datasets = load_cleaned_datasets(data_dir)
    
    # 2. Feature engineering
    final_df, feature_cols = build_features_and_labels(datasets)
    
    # Clean memory by deleting intermediate raw datasets
    del datasets
    gc.collect()
    
    # 3. Train-test split (Temporal)
    target_col = 'churn_label'
    X_train, y_train, X_test, y_test, test_df = temporal_split(
        final_df, feature_cols, target_col, train_ratio=0.8
    )
    
    # 4. Model training and evaluation
    model, metrics = train_model(X_train, y_train, X_test, y_test)
    
    # Save model and feature names list
    model_path = os.path.join(output_dir, "lightgbm_churn_model.pkl")
    joblib.dump({
        'model': model,
        'features': feature_cols
    }, model_path)
    print(f"Saved model checkpoint to {model_path}")
    
    # 5. Explanations (Feature Importance and SHAP)
    explain_model(model, X_test, feature_cols, output_dir)
    
    # 6. Save text summary of metrics
    summary_path = os.path.join(output_dir, "metrics_report.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=4, ensure_ascii=False)
    print(f"Saved metric report to {summary_path}")
    
    # Print summary
    print("\n" + "="*50)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*50)
    print(f"ROC-AUC: {metrics['roc_auc']:.4f}")
    print(f"F1 Churn Score: {metrics['f1_churn']:.4f}")
    print(f"Recall Churn Score: {metrics['recall_churn']:.4f}")
    print("="*50)

if __name__ == "__main__":
    # Define paths
    DATA_DIR = r"e:\Thạc Sĩ\Project\Platform hỗ trợ thử nghiệm\Dataset\Olist Brazilian E-Commerce"
    OUTPUT_DIR = r"e:\Thạc Sĩ\Project\Platform hỗ trợ thử nghiệm\Evaluation\Setting_A\reports"
    
    run_pipeline(DATA_DIR, OUTPUT_DIR)
