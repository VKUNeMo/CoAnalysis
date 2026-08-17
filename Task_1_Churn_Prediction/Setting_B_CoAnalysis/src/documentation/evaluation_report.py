import os
import json
import logging

logger = logging.getLogger("churn_prediction.documentation.evaluation_report")

def generate_final_doc_evaluation_report(metrics: dict, output_path: str) -> None:
    """
    Generate final evaluation report document.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    cm = metrics.get('confusion_matrix', {})
    total = sum(cm.values()) if isinstance(cm, dict) else 1
    
    content = f"""# Churn Prediction - Final Model Evaluation Report

This report presents performance details of the optimized machine learning model trained on Olist Brazilian E-Commerce dataset.

## Model Performance Summary

| Metric | Score |
|---|---|
| **Area Under ROC (AUC-ROC)** | {metrics.get('auc_roc', 0.0):.4f} |
| **Area Under PR (AUC-PR)** | {metrics.get('auc_pr', 0.0):.4f} |
| **Optimized Threshold** | {metrics.get('threshold', 0.5):.4f} |
| **F1-Score** | {metrics.get('f1_score', 0.0):.4f} |
| **Recall (Sensitivity)** | {metrics.get('recall', 0.0):.4f} |
| **Precision** | {metrics.get('precision', 0.0):.4f} |
| **Accuracy** | {metrics.get('accuracy', 0.0):.4f} |

### Detailed Classification Matrix (Test Set)

```text
{metrics.get('classification_report', 'N/A')}
```

### Confusion Matrix Breakdown
- **True Negatives (TN)**: {cm.get('TN', 0)} ({100*cm.get('TN', 0)/total:.2f}%) - Correctly predicted active customers.
- **False Positives (FP)**: {cm.get('FP', 0)} ({100*cm.get('FP', 0)/total:.2f}%) - Active customers flagged as churn risk.
- **False Negatives (FN)**: {cm.get('FN', 0)} ({100*cm.get('FN', 0)/total:.2f}%) - Churners missed by model.
- **True Positives (TP)**: {cm.get('TP', 0)} ({100*cm.get('TP', 0)/total:.2f}%) - Correctly flagged churn risks.

---
*Evaluation conducted strictly using temporal split with test observations starting on the testing cutoff date to guarantee absence of look-ahead bias.*
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Final evaluation document generated at {output_path}")
