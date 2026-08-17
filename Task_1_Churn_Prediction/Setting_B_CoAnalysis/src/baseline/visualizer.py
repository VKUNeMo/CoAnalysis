import os
import matplotlib.pyplot as plt
import numpy as np
import logging
from typing import Dict, Tuple

logger = logging.getLogger("churn_prediction.baseline.visualizer")

def visualize_baseline_results(metrics: Dict, curves: Tuple, output_dir: str) -> None:
    """
    Generate and save ROC curve, Precision-Recall curve, and Confusion Matrix plots
    using clean and modern styles.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    fpr, tpr, _, precision_array, recall_array, _ = curves
    auc_roc = metrics['auc_roc']
    auc_pr = metrics['auc_pr']
    opt_thresh = metrics['optimal_threshold']
    
    # Set style
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    # 1. Plot ROC Curve
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot(fpr, tpr, color='#1A73E8', lw=2.5, label=f'ROC Curve (AUC = {auc_roc:.4f})')
    ax.plot([0, 1], [0, 1], color='#B0BEC5', linestyle='--', lw=1.5, label='Random Guess')
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('False Positive Rate', fontsize=11, fontweight='bold', labelpad=10)
    ax.set_ylabel('True Positive Rate', fontsize=11, fontweight='bold', labelpad=10)
    ax.set_title('Receiver Operating Characteristic (ROC) Curve', fontsize=13, fontweight='bold', pad=15)
    ax.legend(loc="lower right", frameon=True, facecolor='white', edgecolor='#CFD8DC')
    plt.tight_layout()
    roc_path = os.path.join(output_dir, 'baseline_roc_curve.png')
    plt.savefig(roc_path, dpi=300)
    plt.close()
    logger.info(f"Saved ROC curve to {roc_path}")
    
    # 2. Plot Precision-Recall Curve
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot(recall_array, precision_array, color='#E91E63', lw=2.5, label=f'PR Curve (AUC = {auc_pr:.4f})')
    
    # Draw no-skill line (which is the churn rate in test set)
    # We can infer the churn rate from confusion matrix: (TP+FN)/Total
    cm = metrics['confusion_matrix']
    total = sum(cm[0]) + sum(cm[1])
    churn_rate = sum(cm[1]) / total if total > 0 else 0.5
    ax.plot([0, 1], [churn_rate, churn_rate], color='#B0BEC5', linestyle='--', lw=1.5, label=f'No Skill (Churn Rate = {churn_rate:.4f})')
    
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('Recall', fontsize=11, fontweight='bold', labelpad=10)
    ax.set_ylabel('Precision', fontsize=11, fontweight='bold', labelpad=10)
    ax.set_title('Precision-Recall Curve', fontsize=13, fontweight='bold', pad=15)
    ax.legend(loc="lower left", frameon=True, facecolor='white', edgecolor='#CFD8DC')
    plt.tight_layout()
    pr_path = os.path.join(output_dir, 'baseline_pr_curve.png')
    plt.savefig(pr_path, dpi=300)
    plt.close()
    logger.info(f"Saved Precision-Recall curve to {pr_path}")
    
    # 3. Plot Confusion Matrix Heatmap
    # Since we want to make it look premium, we can draw it cleanly with matplotlib
    tn, fp = cm[0]
    fn, tp = cm[1]
    
    cm_matrix = np.array([[tn, fp], [fn, tp]])
    
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm_matrix, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    
    ax.set(xticks=np.arange(cm_matrix.shape[1]),
           yticks=np.arange(cm_matrix.shape[0]),
           xticklabels=['Active', 'Churned'],
           yticklabels=['Active', 'Churned'],
           title=f'Confusion Matrix (Threshold = {opt_thresh:.2f})',
           ylabel='True label',
           xlabel='Predicted label')
    
    # Adjust title font and layout
    ax.set_title(f'Confusion Matrix (Threshold = {opt_thresh:.2f})', fontsize=12, fontweight='bold', pad=15)
    ax.set_ylabel('True Label', fontsize=10, fontweight='bold')
    ax.set_xlabel('Predicted Label', fontsize=10, fontweight='bold')
    
    # Text annotations in the cells
    thresh = cm_matrix.max() / 2.
    for i in range(cm_matrix.shape[0]):
        for j in range(cm_matrix.shape[1]):
            val = cm_matrix[i, j]
            pct = 100 * val / total if total > 0 else 0
            ax.text(j, i, f"{val}\n({pct:.1f}%)",
                    ha="center", va="center",
                    color="white" if val > thresh else "black",
                    fontweight='bold', fontsize=12)
                    
    plt.tight_layout()
    cm_path = os.path.join(output_dir, 'baseline_confusion_matrix.png')
    plt.savefig(cm_path, dpi=300)
    plt.close()
    logger.info(f"Saved Confusion Matrix heatmap to {cm_path}")
