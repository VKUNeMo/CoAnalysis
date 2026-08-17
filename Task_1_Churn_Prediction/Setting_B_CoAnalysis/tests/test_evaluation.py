import os
import sys
import numpy as np

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
from sklearn.linear_model import LogisticRegression
from src.evaluation.evaluator import optimize_threshold, compute_test_metrics

def test_evaluation_metrics():
    # Mock data
    y_true = pd.Series([1, 1, 0, 0, 1, 0, 1, 0])
    y_proba = np.array([0.9, 0.8, 0.1, 0.2, 0.75, 0.3, 0.85, 0.4])
    
    # Threshold optimization
    thresh = optimize_threshold(y_true, y_proba, metric='f1')
    assert 0.3 < thresh < 0.8
    
    # Test metrics computation
    # We fit a dummy model to call predict_proba
    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=50, n_features=3, random_state=42)
    model = LogisticRegression().fit(X, y)
    
    X_test = pd.DataFrame(X[:10])
    y_test = pd.Series(y[:10])
    
    metrics = compute_test_metrics(model, X_test, y_test, threshold=0.5)
    assert 'auc_roc' in metrics
    assert 'f1_score' in metrics
    assert 'confusion_matrix' in metrics
