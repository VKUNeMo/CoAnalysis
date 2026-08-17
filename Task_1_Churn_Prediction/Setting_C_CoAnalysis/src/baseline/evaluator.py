import numpy as np
import pandas as pd
import logging
from typing import Dict, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, roc_curve, confusion_matrix, classification_report

logger = logging.getLogger("churn_prediction.baseline.evaluator")

def evaluate_baseline(model: LogisticRegression, scaler: StandardScaler, X_test: pd.DataFrame, y_test: pd.Series) -> Tuple[Dict, Tuple]:
    """
    Evaluate the baseline model on the test set, including threshold optimization to maximize F1-score.
    """
    logger.info("Preparing test features and scaling...")
    
    # Drop identifier if present
    X_test_clean = X_test.copy()
    if 'customer_unique_id' in X_test_clean.columns:
        X_test_clean = X_test_clean.drop(columns=['customer_unique_id'])
        
    X_test_scaled = scaler.transform(X_test_clean)
    
    # Predict probabilities (positive class churn=1)
    y_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    # Compute AUC-ROC and curves
    auc_roc = roc_auc_score(y_test, y_proba)
    fpr, tpr, roc_thresholds = roc_curve(y_test, y_proba)
    
    # Compute Precision-Recall curve & AUC-PR
    precision_array, recall_array, pr_thresholds = precision_recall_curve(y_test, y_proba)
    auc_pr = auc(recall_array, precision_array)
    
    # Optimize threshold: maximize F1-score
    # F1 = 2 * (Precision * Recall) / (Precision + Recall)
    f1_scores = []
    for p, r in zip(precision_array[:-1], recall_array[:-1]):
        if p + r > 0:
            f1_scores.append(2 * p * r / (p + r))
        else:
            f1_scores.append(0.0)
            
    best_idx = np.argmax(f1_scores)
    optimal_threshold = pr_thresholds[best_idx]
    best_f1 = f1_scores[best_idx]
    
    logger.info(f"Optimal decision threshold found: {optimal_threshold:.4f} with F1-Score: {best_f1:.4f}")
    
    # Make binary predictions at optimal threshold
    y_pred = (y_proba >= optimal_threshold).astype(int)
    
    # Compute other metrics at optimal threshold
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    
    # Precision, Recall, Accuracy
    precision_val = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall_val = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    accuracy_val = (tp + tn) / (tp + tn + fp + fn)
    
    metrics = {
        'auc_roc': float(auc_roc),
        'auc_pr': float(auc_pr),
        'optimal_threshold': float(optimal_threshold),
        'f1': float(best_f1),
        'precision': float(precision_val),
        'recall': float(recall_val),
        'accuracy': float(accuracy_val),
        'confusion_matrix': [[int(tn), int(fp)], [int(fn), int(tp)]]
    }
    
    curves = (fpr, tpr, roc_thresholds, precision_array, recall_array, pr_thresholds)
    
    logger.info(f"Evaluation metrics: {metrics}")
    
    return metrics, curves
