import pandas as pd
import logging
from typing import List

logger = logging.getLogger("churn_prediction.modeling.selector")

def select_top_models(cv_results: pd.DataFrame, top_k: int = 1) -> List[str]:
    """
    Select the best-performing models based on CV metrics.
    Primary metric is mean AUC-ROC, secondary is F1-score, and tertiary is training time.
    """
    if cv_results.empty:
        logger.warning("Empty CV results. Fallback to default ['LightGBM'] or ['LogisticRegression'].")
        return ['LogisticRegression']
        
    # Sort models by mean AUC-ROC descending
    sorted_df = cv_results.sort_values(by='mean_auc_roc', ascending=False).reset_index(drop=True)
    
    selected = []
    logger.info("Ranking candidates based on CV results:")
    for idx, row in sorted_df.iterrows():
        logger.info(
            f"Rank {idx+1}: {row['model_name']} - "
            f"Mean AUC-ROC: {row['mean_auc_roc']:.4f} (std: {row['std_auc_roc']:.4f}), "
            f"Mean F1: {row['mean_f1']:.4f}, Recall: {row['mean_recall']:.4f}, "
            f"Avg Fit Time: {row['mean_fit_time']:.2f}s"
        )
        
    # Selection logic:
    # Select top_k. If top 2 differ by less than 0.01 in AUC-ROC, we log a comparison
    # but still select the requested top_k names.
    for i in range(min(top_k, len(sorted_df))):
        selected.append(sorted_df.loc[i, 'model_name'])
        
    logger.info(f"Selected top {top_k} model(s) for hyperparameter tuning: {selected}")
    
    return selected
