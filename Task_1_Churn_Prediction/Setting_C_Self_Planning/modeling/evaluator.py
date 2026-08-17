import pandas as pd
from typing import Dict, Any
from sklearn.metrics import roc_auc_score, recall_score, f1_score, confusion_matrix

def evaluate_models(models: Dict[str, Any], X_test: pd.DataFrame, y_test: pd.Series) -> pd.DataFrame:
    """
    Evaluates baseline models for Self-Planning (Setting C) on temporal test set.
    """
    results = []
    # Threshold for Self-Planning (Setting C)
    SELF_PLANNING_THRESHOLD = 0.93
    
    for name, model in models.items():
        y_prob = model.predict_proba(X_test)[:, 1]
        y_pred = (y_prob >= SELF_PLANNING_THRESHOLD).astype(int)
        
        auc = roc_auc_score(y_test, y_prob)
        rec_churn = recall_score(y_test, y_pred, pos_label=1)
        rec_active = recall_score(y_test, y_pred, pos_label=0)
        f1_macro = f1_score(y_test, y_pred, average='macro')
        
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()
        print(f"[Setting C - Self-Planning] Model: {name} (Threshold={SELF_PLANNING_THRESHOLD}) -> TN={tn}, FP={fp}, FN={fn}, TP={tp}")
        
        results.append({
            "Model": name,
            "ROC-AUC": auc,
            "Recall (Churn)": rec_churn,
            "Recall (Active)": rec_active,
            "Macro F1-Score": f1_macro
        })
        
    results_df = pd.DataFrame(results)
    
    results_df["ROC-AUC"] = results_df["ROC-AUC"].astype('float32')
    results_df["Recall (Churn)"] = results_df["Recall (Churn)"].astype('float32')
    results_df["Recall (Active)"] = results_df["Recall (Active)"].astype('float32')
    results_df["Macro F1-Score"] = results_df["Macro F1-Score"].astype('float32')
    
    return results_df
