import pandas as pd
import logging
from typing import Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger("churn_prediction.baseline.trainer")

def train_baseline_model(X_train: pd.DataFrame, y_train: pd.Series) -> Tuple[LogisticRegression, StandardScaler]:
    """
    Train a simple Logistic Regression model using StandardScaler and balanced class weights.
    """
    logger.info(f"Scaling features for training baseline model (shape: {X_train.shape})...")
    
    # Drop identifier if present
    X_train_clean = X_train.copy()
    if 'customer_unique_id' in X_train_clean.columns:
        X_train_clean = X_train_clean.drop(columns=['customer_unique_id'])
        
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_clean)
    
    logger.info("Fitting Logistic Regression model...")
    model = LogisticRegression(class_weight='balanced', random_state=42, max_iter=500)
    model.fit(X_train_scaled, y_train)
    
    logger.info("Baseline model training completed successfully.")
    
    return model, scaler
