import pandas as pd
import logging
import os

logger = logging.getLogger("churn_prediction.explainability.shap_analyzer")

def explain_model_shap(model, X_test: pd.DataFrame, scaler=None, output_dir: str = ".") -> dict:
    """
    Compute SHAP values for tree-based or linear models and save summary plot.
    If shap is not installed, falls back to a clean mock return.
    """
    logger.info("Starting SHAP analysis...")
    os.makedirs(output_dir, exist_ok=True)
    
    X_clean = X_test.copy()
    if 'customer_unique_id' in X_clean.columns:
        X_clean = X_clean.drop(columns=['customer_unique_id'])
        
    if scaler is not None:
        X_clean = pd.DataFrame(scaler.transform(X_clean), columns=X_clean.columns)
        
    try:
        import shap
        import matplotlib.pyplot as plt
        
        # Determine appropriate explainer based on model class name
        model_class = model.__class__.__name__
        logger.info(f"Using SHAP explainer for class: {model_class}")
        
        if 'LGBMClassifier' in model_class or 'XGBClassifier' in model_class or 'RandomForestClassifier' in model_class:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_clean)
        else:
            explainer = shap.LinearExplainer(model, X_clean)
            shap_values = explainer.shap_values(X_clean)
            
        # Draw summary plot
        plt.figure(figsize=(10, 6))
        
        # LGBM binary classification shap values list contains [class_0, class_1]
        # We want to plot class_1 (churn prediction) values
        if isinstance(shap_values, list) and len(shap_values) == 2:
            shap.summary_plot(shap_values[1], X_clean, show=False)
        else:
            shap.summary_plot(shap_values, X_clean, show=False)
            
        plt.title("SHAP Feature Impact on Churn Probability", fontsize=12, fontweight='bold', pad=15)
        plt.tight_layout()
        shap_summary_path = os.path.join(output_dir, 'best_model_shap_summary.png')
        plt.savefig(shap_summary_path, dpi=300)
        plt.close()
        logger.info(f"Saved SHAP summary plot to {shap_summary_path}")
        
        return {
            'shap_status': 'success',
            'explainer_type': type(explainer).__name__,
            'shap_summary_plot': shap_summary_path
        }
        
    except ImportError:
        logger.warning("shap package is not installed. Skipping SHAP analysis and summary plotting.")
        return {
            'shap_status': 'skipped',
            'reason': 'shap package not installed'
        }
    except Exception as e:
        logger.error(f"SHAP explanation failed with error: {e}")
        return {
            'shap_status': 'failed',
            'error': str(e)
        }
