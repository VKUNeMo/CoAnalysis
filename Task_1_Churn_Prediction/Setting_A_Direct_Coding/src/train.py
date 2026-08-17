import os
import lightgbm as lgb
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
import numpy as np

def temporal_split(df, feature_cols, target_col, train_ratio=0.8):
    """
    Splits the dataframe temporally to prevent look-ahead bias.
    """
    df_sorted = df.sort_values('order_purchase_timestamp').copy()
    split_idx = int(len(df_sorted) * train_ratio)
    split_date = df_sorted.iloc[split_idx]['order_purchase_timestamp']
    print(f"Splitting data temporally at date: {split_date}")
    
    train_df = df_sorted[df_sorted['order_purchase_timestamp'] < split_date]
    test_df = df_sorted[df_sorted['order_purchase_timestamp'] >= split_date]
    
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]
    
    print(f"Train size: {X_train.shape}, Test size: {X_test.shape}")
    print(f"Train churn rate: {y_train.mean():.2%}, Test churn rate: {y_test.mean():.2%}")
    
    return X_train, y_train, X_test, y_test, test_df

def train_model(X_train, y_train, X_test, y_test):
    """
    Trains a LightGBM Classifier and evaluates it.
    """
    print("Training LightGBM model...")
    
    # Calculate scale_pos_weight for handling class imbalance if needed
    # Churn is class 1. If churn is highly dominant (e.g., 90%), class 0 is minority.
    # In Olist, most customers buy once, so churn=1 is very frequent.
    # We will balance the model training by setting scale_pos_weight
    n_neg = np.sum(y_train == 0)
    n_pos = np.sum(y_train == 1)
    scale_pos = n_neg / n_pos if n_pos > 0 else 1.0
    print(f"Class counts - Neg (No Churn): {n_neg}, Pos (Churn): {n_pos}. Scale pos weight: {scale_pos:.4f}")
    
    # Initialize LightGBM Classifier
    model = lgb.LGBMClassifier(
        objective='binary',
        metric='auc',
        scale_pos_weight=scale_pos,
        random_state=42,
        n_estimators=100,
        learning_rate=0.05,
        max_depth=6,
        num_leaves=31,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        n_jobs=-1
    )
    
    # Train
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[lgb.early_stopping(stopping_rounds=15, verbose=True)]
    )
    
    # Predict probabilities and classes
    y_pred_prob = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)
    
    # Evaluate
    roc_auc = roc_auc_score(y_test, y_pred_prob)
    
    print("\n" + "="*50)
    print("EVALUATION METRICS:")
    print("="*50)
    print(f"ROC-AUC Score: {roc_auc:.4f}")
    print("\nClassification Report:")
    report = classification_report(y_test, y_pred, target_names=['No Churn (0)', 'Churn (1)'])
    print(report)
    
    print("Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    print("="*50 + "\n")
    
    # Extract recall and f1 from sklearn classification_report metrics
    # Recall for churn (class 1)
    recall_churn = cm[1, 1] / (cm[1, 0] + cm[1, 1]) if (cm[1, 0] + cm[1, 1]) > 0 else 0.0
    # F1 score for churn
    precision_churn = cm[1, 1] / (cm[0, 1] + cm[1, 1]) if (cm[0, 1] + cm[1, 1]) > 0 else 0.0
    f1_churn = 2 * (precision_churn * recall_churn) / (precision_churn + recall_churn) if (precision_churn + recall_churn) > 0 else 0.0
    
    metrics = {
        'roc_auc': roc_auc,
        'f1_churn': f1_churn,
        'recall_churn': recall_churn,
        'confusion_matrix': cm.tolist(),
        'classification_report': report
    }
    
    return model, metrics
