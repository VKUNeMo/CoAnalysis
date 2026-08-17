import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from scipy.stats import uniform, randint
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from src.modeling.imbalance_handler import compute_class_weights

logger = logging.getLogger("churn_prediction.modeling.tuner")

def define_search_space(model_name: str) -> Dict[str, Any]:
    """
    Define hyperparameter search distributions for the models,
    appropriate for CPU training and RAM constraint.
    """
    if model_name == 'LightGBM':
        return {
            'n_estimators': randint(50, 300),
            'learning_rate': uniform(0.01, 0.15),
            'num_leaves': randint(15, 60),
            'max_depth': randint(3, 10),
            'min_child_samples': randint(10, 50),
            'subsample': uniform(0.6, 0.4) # range [0.6, 1.0]
        }
    elif model_name == 'XGBoost':
        return {
            'n_estimators': randint(50, 300),
            'learning_rate': uniform(0.01, 0.15),
            'max_depth': randint(3, 10),
            'min_child_weight': randint(1, 10),
            'subsample': uniform(0.6, 0.4),
            'colsample_bytree': uniform(0.6, 0.4)
        }
    elif model_name == 'LogisticRegression':
        return {
            'C': uniform(0.01, 10.0),
            'penalty': ['l2']
        }
    else:
        return {}

def tune_hyperparameters(X: pd.DataFrame, y: pd.Series, model_names: List[str],
                         models_info: Dict[str, Any], cv_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform RandomizedSearchCV with TimeSeriesSplit CV for top selected models.
    """
    logger.info(f"Tuning hyperparameters for: {model_names}")
    
    # Drop identifier if present
    X_clean = X.copy()
    if 'customer_unique_id' in X_clean.columns:
        X_clean = X_clean.drop(columns=['customer_unique_id'])
        
    n_splits = cv_config.get('cv_folds', 3)
    n_iter = cv_config.get('tuner_iter', 20)
    
    # Estimate gap samples
    total_samples = len(X_clean)
    gap_samples = int(total_samples * (cv_config.get('cv_gap_days', 30) / 180.0 * 0.15))
    gap_samples = max(10, min(gap_samples, int(total_samples * 0.1)))
    
    tscv = TimeSeriesSplit(n_splits=n_splits, gap=gap_samples)
    
    best_models_report = []
    
    for name in model_names:
        if name not in models_info:
            logger.warning(f"Model '{name}' not found in candidate models info.")
            continue
            
        m_info = models_info[name]
        model_instance = m_info['model']
        search_space = define_search_space(name)
        
        logger.info(f"Tuning {name} with {n_iter} iterations...")
        
        # Scaling if LogisticRegression
        X_tune = X_clean
        if m_info['type'] == 'linear':
            scaler = StandardScaler()
            X_tune = scaler.fit_transform(X_clean)
            
        # Initialize RandomizedSearchCV
        rs = RandomizedSearchCV(
            estimator=model_instance,
            param_distributions=search_space,
            n_iter=n_iter,
            scoring='roc_auc',
            cv=tscv,
            random_state=cv_config.get('random_state', 42),
            n_jobs=-1,
            verbose=1
        )
        
        rs.fit(X_tune, y)
        
        best_score = rs.best_score_
        best_params = rs.best_params_
        best_estimator = rs.best_estimator_
        
        logger.info(f"Best CV AUC-ROC for {name}: {best_score:.4f} with params: {best_params}")
        
        report_entry = {
            'model_name': name,
            'best_score': float(best_score),
            'best_params': best_params,
            'best_estimator': best_estimator,
            'scaler': scaler if m_info['type'] == 'linear' else None,
            'type': m_info['type']
        }
        best_models_report.append(report_entry)
        
    # Compare and select absolute best model
    best_models_report.sort(key=lambda x: x['best_score'], reverse=True)
    best_candidate = best_models_report[0]
    
    logger.info(f"Final best model selected: {best_candidate['model_name']} with validation AUC-ROC: {best_candidate['best_score']:.4f}")
    
    return best_candidate
