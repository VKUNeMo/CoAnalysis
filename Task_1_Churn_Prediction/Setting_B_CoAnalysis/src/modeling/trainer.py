import time
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score, f1_score, recall_score
from src.modeling.imbalance_handler import compute_class_weights

logger = logging.getLogger("churn_prediction.modeling.trainer")

def train_baseline_models(X_train: pd.DataFrame, y_train: pd.Series, cv_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Train 3 initial models (LightGBM, XGBoost, Logistic Regression) with default configs
    and class imbalance handling.
    """
    models = {}
    
    # Drop identifier if present
    X_train_clean = X_train.copy()
    if 'customer_unique_id' in X_train_clean.columns:
        X_train_clean = X_train_clean.drop(columns=['customer_unique_id'])
        
    # Scale for Logistic Regression
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_clean)
    
    # Compute class weights for models
    weights_lr = compute_class_weights(y_train, 'class_weight_balanced')
    weights_gb = compute_class_weights(y_train, 'scale_pos_weight')
    
    # 1. Logistic Regression
    logger.info("Initializing Logistic Regression model...")
    lr_model = LogisticRegression(
        class_weight=weights_lr.get('class_weight'),
        random_state=cv_config.get('random_state', 42),
        max_iter=500
    )
    models['LogisticRegression'] = {
        'model': lr_model,
        'scaler': scaler,
        'type': 'linear'
    }
    
    # 2. LightGBM
    try:
        import lightgbm as lgb
        logger.info("Initializing LightGBM model...")
        lgb_model = lgb.LGBMClassifier(
            scale_pos_weight=weights_gb.get('scale_pos_weight', 1.0),
            random_state=cv_config.get('random_state', 42),
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            verbosity=-1
        )
        models['LightGBM'] = {
            'model': lgb_model,
            'scaler': None,
            'type': 'tree'
        }
    except ImportError:
        logger.warning("lightgbm is not installed. Skipping LightGBM candidate.")
        
    # 3. XGBoost
    try:
        import xgboost as xgb
        logger.info("Initializing XGBoost model...")
        xgb_model = xgb.XGBClassifier(
            scale_pos_weight=weights_gb.get('scale_pos_weight', 1.0),
            random_state=cv_config.get('random_state', 42),
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            eval_metric='logloss'
        )
        models['XGBoost'] = {
            'model': xgb_model,
            'scaler': None,
            'type': 'tree'
        }
    except ImportError:
        logger.warning("xgboost is not installed. Skipping XGBoost candidate.")
        
    return models

def run_time_series_cv(X: pd.DataFrame, y: pd.Series, models: Dict[str, Any], cv_config: Dict[str, Any]) -> pd.DataFrame:
    """
    Perform TimeSeriesSplit cross-validation across models, sorting data by date if applicable.
    """
    logger.info("Starting TimeSeriesSplit Cross Validation...")
    
    # Drop identifier if present
    X_clean = X.copy()
    if 'customer_unique_id' in X_clean.columns:
        X_clean = X_clean.drop(columns=['customer_unique_id'])
        
    n_splits = cv_config.get('cv_folds', 3)
    
    # We estimate gap size in samples: e.g. 5% of total dataset size approximately corresponding to 30 days
    total_samples = len(X_clean)
    gap_samples = int(total_samples * (cv_config.get('cv_gap_days', 30) / 180.0 * 0.15))
    gap_samples = max(10, min(gap_samples, int(total_samples * 0.1)))
    
    logger.info(f"Using TimeSeriesSplit with n_splits={n_splits}, gap_samples={gap_samples}")
    tscv = TimeSeriesSplit(n_splits=n_splits, gap=gap_samples)
    
    results = []
    
    for model_name, m_info in models.items():
        logger.info(f"Running CV for model: {model_name}")
        
        auc_scores = []
        f1_scores = []
        recall_scores = []
        fit_times = []
        
        fold = 0
        for train_idx, val_idx in tscv.split(X_clean):
            fold += 1
            t0 = time.time()
            
            X_tr, y_tr = X_clean.iloc[train_idx], y.iloc[train_idx]
            X_val, y_val = X_clean.iloc[val_idx], y.iloc[val_idx]
            
            # Skip if only 1 class in validation fold
            if len(np.unique(y_val)) < 2:
                logger.warning(f"Fold {fold} has only one class in validation set. Skipping.")
                continue
                
            # Copy model base instance
            from sklearn.base import clone
            model_instance = clone(m_info['model'])
            
            # Dynamic class weighting for each fold's training labels
            if m_info['type'] == 'linear':
                weights = compute_class_weights(y_tr, 'class_weight_balanced')
                model_instance.set_params(class_weight=weights.get('class_weight'))
                
                # Apply scaler fitted only on fold train data
                scaler = StandardScaler()
                X_tr_scaled = scaler.fit_transform(X_tr)
                X_val_scaled = scaler.transform(X_val)
                
                model_instance.fit(X_tr_scaled, y_tr)
                y_proba = model_instance.predict_proba(X_val_scaled)[:, 1]
            else:
                # Tree-based GBDT model
                weights = compute_class_weights(y_tr, 'scale_pos_weight')
                model_instance.set_params(scale_pos_weight=weights.get('scale_pos_weight', 1.0))
                
                model_instance.fit(X_tr, y_tr)
                y_proba = model_instance.predict_proba(X_val)[:, 1]
                
            fit_time = time.time() - t0
            
            # Compute fold metrics (default 0.5 threshold for CV ranking)
            y_pred = (y_proba >= 0.5).astype(int)
            
            auc_val = roc_auc_score(y_val, y_proba)
            f1_val = f1_score(y_val, y_pred, zero_division=0)
            recall_val = recall_score(y_val, y_pred, zero_division=0)
            
            auc_scores.append(auc_val)
            f1_scores.append(f1_val)
            recall_scores.append(recall_val)
            fit_times.append(fit_time)
            
            logger.info(f"Fold {fold} - AUC-ROC: {auc_val:.4f}, F1: {f1_val:.4f}, Recall: {recall_val:.4f}, Time: {fit_time:.2f}s")
            
        if auc_scores:
            results.append({
                'model_name': model_name,
                'mean_auc_roc': float(np.mean(auc_scores)),
                'std_auc_roc': float(np.std(auc_scores)),
                'mean_f1': float(np.mean(f1_scores)),
                'mean_recall': float(np.mean(recall_scores)),
                'mean_fit_time': float(np.mean(fit_times))
            })
            
    results_df = pd.DataFrame(results)
    logger.info(f"Cross-validation results:\n{results_df.to_string()}")
    
    return results_df
