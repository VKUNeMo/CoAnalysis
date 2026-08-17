import pandas as pd
import logging

logger = logging.getLogger("churn_prediction.high_risk_list.generator")

def generate_high_risk_list(model, X: pd.DataFrame, customer_ids: pd.Series, threshold: float, scaler=None) -> pd.DataFrame:
    """
    Generate high-risk customer list sorted by churn probability descending.
    """
    X_clean = X.copy()
    if 'customer_unique_id' in X_clean.columns:
        X_clean = X_clean.drop(columns=['customer_unique_id'])
        
    if scaler is not None:
        X_clean = scaler.transform(X_clean)
        
    # Get probabilities
    y_proba = model.predict_proba(X_clean)[:, 1]
    
    # Build dataframe
    pred_df = pd.DataFrame({
        'customer_unique_id': customer_ids,
        'churn_probability': y_proba,
        'churn_prediction': (y_proba >= threshold).astype(int)
    })
    
    # Filter high risk (probability > threshold)
    high_risk_df = pred_df[pred_df['churn_probability'] >= threshold].copy()
    
    # Sort descending
    high_risk_df = high_risk_df.sort_values(by='churn_probability', ascending=False).reset_index(drop=True)
    
    # Add rank column
    high_risk_df.insert(0, 'rank', high_risk_df.index + 1)
    
    logger.info(f"Generated high-risk list with {len(high_risk_df)} customers (threshold: {threshold:.4f})")
    
    return high_risk_df
