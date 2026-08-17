import os
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger("churn_prediction.explainability.feature_importance")

def extract_feature_importance(model, feature_names: list, top_k: int = 15) -> pd.DataFrame:
    """
    Extract feature importance scores from the best model, fallback to permutation or linear coeff.
    """
    model_class = model.__class__.__name__
    logger.info(f"Extracting feature importance from model {model_class}...")
    
    importances = None
    
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
    elif hasattr(model, 'coef_'):
        importances = np.abs(model.coef_[0])
    
    if importances is None:
        logger.warning(f"Model {model_class} does not support feature importance extraction natively. Returning empty.")
        return pd.DataFrame()
        
    # Standardize names vs values length
    if len(importances) != len(feature_names):
        logger.warning(f"Length mismatch: importances ({len(importances)}) vs features ({len(feature_names)}). Adjusting names.")
        feature_names = feature_names[:len(importances)]
        
    # Build dataframe
    df = pd.DataFrame({
        'feature_name': feature_names,
        'importance_score': importances
    })
    
    # Normalize
    total_imp = df['importance_score'].sum()
    if total_imp > 0:
        df['importance_score'] = df['importance_score'] / total_imp
        
    # Sort
    df = df.sort_values(by='importance_score', ascending=False).reset_index(drop=True)
    df.insert(0, 'rank', df.index + 1)
    
    return df.head(top_k)

def plot_feature_importance(importance_df: pd.DataFrame, output_path: str) -> None:
    """
    Save horizontal bar chart of feature importances.
    """
    if importance_df.empty:
        logger.warning("Feature importance dataframe is empty. Skipping plot.")
        return
        
    import matplotlib.pyplot as plt
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Sort for plotting (lowest at bottom, highest at top)
    plot_df = importance_df.sort_values(by='importance_score', ascending=True)
    
    plt.figure(figsize=(9, 6))
    plt.barh(plot_df['feature_name'], plot_df['importance_score'], color='#4285F4')
    plt.xlabel('Normalized Importance Score', fontsize=11, fontweight='bold', labelpad=10)
    plt.ylabel('Features', fontsize=11, fontweight='bold', labelpad=10)
    plt.title('Top Features Importances', fontsize=13, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved feature importance plot to {output_path}")
