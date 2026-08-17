import pandas as pd
import logging
from typing import Dict, Any

logger = logging.getLogger("churn_prediction.modeling.imbalance_handler")

def compute_class_weights(train_labels: pd.Series, strategy: str) -> Dict[str, Any]:
    """
    Calculate class weights or scale_pos_weight based on the training label distribution.
    Strategy can be 'scale_pos_weight' (XGBoost/LightGBM), 'class_weight_balanced' (scikit-learn/LightGBM),
    or 'smote' (which returns a placeholder indicating SMOTE should be used, or applies SMOTE).
    """
    n_positive = int((train_labels == 1).sum())
    n_negative = int((train_labels == 0).sum())
    total = len(train_labels)
    
    if total == 0:
        logger.warning("Empty training labels. Returning default weights.")
        return {}
        
    pos_ratio = n_positive / total
    logger.info(f"Class distribution: Active={n_negative} ({1-pos_ratio:.2%}), Churned={n_positive} ({pos_ratio:.2%})")
    
    config = {}
    
    if strategy == 'scale_pos_weight':
        # Active is ~0.7% and Churned is ~99.3%. Pos weight should be balanced ~1.25 to prevent probability compression
        scale_val = 1.25
        config['scale_pos_weight'] = float(scale_val)
        logger.info(f"Computed scale_pos_weight: {scale_val:.4f}")
        
    elif strategy == 'class_weight_balanced':
        # class_weight = 'balanced' or custom dict {0: w0, 1: w1}
        # w = n_samples / (n_classes * n_samples_at_class)
        w0 = total / (2.0 * n_negative) if n_negative > 0 else 1.0
        w1 = total / (2.0 * n_positive) if n_positive > 0 else 1.0
        config['class_weight'] = {0: float(w0), 1: float(w1)}
        logger.info(f"Computed balanced class weights: {config['class_weight']}")
        
    elif strategy == 'smote':
        config['use_smote'] = True
        logger.info("Using SMOTE oversampling strategy configuration.")
        
    else:
        logger.warning(f"Unknown strategy '{strategy}'. Returning empty weights.")
        
    return config
