import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import logging
from sklearn.metrics import roc_curve, auc, precision_recall_curve, confusion_matrix

logger = logging.getLogger("churn_prediction.evaluation.visualizer")

def plot_roc_curve(y_true: pd.Series, y_proba: np.ndarray, output_path: str) -> None:
    """
    Generate and save ROC curve plot.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    auc_score = auc(fpr, tpr)
    
    plt.figure(figsize=(7, 6))
    plt.plot(fpr, tpr, color='#34A853', lw=2.5, label=f'ROC Curve (AUC = {auc_score:.4f})')
    plt.plot([0, 1], [0, 1], color='#B0BEC5', linestyle='--', lw=1.5)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate', fontsize=11, fontweight='bold', labelpad=10)
    plt.ylabel('True Positive Rate', fontsize=11, fontweight='bold', labelpad=10)
    plt.title('Best Model ROC Curve (Test Set)', fontsize=13, fontweight='bold', pad=15)
    plt.legend(loc="lower right", frameon=True, facecolor='white', edgecolor='#CFD8DC')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved ROC curve to {output_path}")

def plot_precision_recall_curve(y_true: pd.Series, y_proba: np.ndarray, output_path: str) -> None:
    """
    Generate and save Precision-Recall curve plot.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    precision, recall, _ = precision_recall_curve(y_true, y_proba)
    auc_pr = auc(recall, precision)
    churn_rate = y_true.mean()
    
    plt.figure(figsize=(7, 6))
    plt.plot(recall, precision, color='#FF9800', lw=2.5, label=f'PR Curve (AUC = {auc_pr:.4f})')
    plt.plot([0, 1], [churn_rate, churn_rate], color='#B0BEC5', linestyle='--', lw=1.5, label=f'No Skill (Rate = {churn_rate:.4f})')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Recall', fontsize=11, fontweight='bold', labelpad=10)
    plt.ylabel('Precision', fontsize=11, fontweight='bold', labelpad=10)
    plt.title('Best Model Precision-Recall Curve (Test Set)', fontsize=13, fontweight='bold', pad=15)
    plt.legend(loc="lower left", frameon=True, facecolor='white', edgecolor='#CFD8DC')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved Precision-Recall curve to {output_path}")

def plot_confusion_matrix(y_true: pd.Series, y_pred: np.ndarray, output_path: str) -> None:
    """
    Generate and save Confusion Matrix heatmap.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cm = confusion_matrix(y_true, y_pred)
    total = cm.sum()
    
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Greens)
    ax.figure.colorbar(im, ax=ax)
    
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           xticklabels=['Active', 'Churned'],
           yticklabels=['Active', 'Churned'],
           ylabel='True label',
           xlabel='Predicted label')
    
    ax.set_title('Confusion Matrix (%)', fontsize=12, fontweight='bold', pad=15)
    ax.set_ylabel('True Label', fontsize=10, fontweight='bold')
    ax.set_xlabel('Predicted Label', fontsize=10, fontweight='bold')
    
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            val = cm[i, j]
            pct = 100 * val / total if total > 0 else 0
            ax.text(j, i, f"{pct:.1f}%",
                    ha="center", va="center",
                    color="white" if val > thresh else "black",
                    fontweight='bold', fontsize=12)
                    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved Confusion Matrix to {output_path}")
