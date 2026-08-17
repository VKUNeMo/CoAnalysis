import numpy as np
import pandas as pd
import logging
from typing import Dict
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, roc_curve, confusion_matrix, classification_report

logger = logging.getLogger("churn_prediction.evaluation.evaluator")

def optimize_threshold(y_true: pd.Series, y_proba: np.ndarray, metric: str = 'youden') -> float:
    """
    Optimize decision threshold based on a validation set metric.
    Default uses Youden's J statistic (TPR - FPR) to balance Active (0) and Churned (1) predictions.
    """
    if metric == 'youden':
        fpr, tpr, thresholds = roc_curve(y_true, y_proba)
        j_scores = tpr - fpr
        best_idx = np.argmax(j_scores)
        optimal_threshold = thresholds[best_idx]
        logger.info(f"Optimized threshold (Youden's J): {optimal_threshold:.4f} (Max J-Score: {j_scores[best_idx]:.4f})")
        return float(optimal_threshold)
    elif metric == 'f1':
        precision_array, recall_array, pr_thresholds = precision_recall_curve(y_true, y_proba)
        f1_scores = []
        for p, r in zip(precision_array[:-1], recall_array[:-1]):
            if p + r > 0:
                f1_scores.append(2 * p * r / (p + r))
            else:
                f1_scores.append(0.0)
        best_idx = np.argmax(f1_scores)
        optimal_threshold = pr_thresholds[best_idx]
        logger.info(f"Optimized threshold for F1: {optimal_threshold:.4f} (F1-Score: {f1_scores[best_idx]:.4f})")
        return float(optimal_threshold)
    else:
        return 0.5

def compute_test_metrics(model, X_test: pd.DataFrame, y_test: pd.Series, threshold: float, scaler=None) -> Dict:
    """
    Compute AUC-ROC, AUC-PR, F1-Score, Recall, Precision, Accuracy on the test set,
    generating confusion matrix and classification report.
    """
    logger.info("Evaluating tuned model on test set...")
    X_test_clean = X_test.copy()
    if 'customer_unique_id' in X_test_clean.columns:
        X_test_clean = X_test_clean.drop(columns=['customer_unique_id'])
        
    if scaler is not None:
        X_test_clean = scaler.transform(X_test_clean)
        
    y_proba = model.predict_proba(X_test_clean)[:, 1]
    
    auc_roc = roc_auc_score(y_test, y_proba)
    
    precision_array, recall_array, pr_thresholds = precision_recall_curve(y_test, y_proba)
    auc_pr = auc(recall_array, precision_array)
    
    # Binary predictions at threshold
    y_pred = (y_proba >= threshold).astype(int)
    
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    
    precision_val = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall_val = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_val = 2 * precision_val * recall_val / (precision_val + recall_val) if (precision_val + recall_val) > 0 else 0.0
    accuracy_val = (tp + tn) / (tp + tn + fp + fn)
    
    metrics = {
        'auc_roc': float(auc_roc),
        'auc_pr': float(auc_pr),
        'threshold': float(threshold),
        'f1_score': float(f1_val),
        'precision': float(precision_val),
        'recall': float(recall_val),
        'accuracy': float(accuracy_val),
        'confusion_matrix': {
            'TN': int(tn),
            'FP': int(fp),
            'FN': int(fn),
            'TP': int(tp)
        }
    }
    
    logger.info(f"Test metrics: {metrics}")
    
    # Save classification report as a string for logs/documentation
    report_str = classification_report(y_test, y_pred, target_names=['Active', 'Churned'])
    metrics['classification_report'] = report_str
    
    return metrics
