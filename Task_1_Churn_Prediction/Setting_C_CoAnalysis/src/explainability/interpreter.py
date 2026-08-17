import pandas as pd
import logging

logger = logging.getLogger("churn_prediction.explainability.interpreter")

def interpret_top_features(importance_df: pd.DataFrame, feature_metadata: dict = None) -> str:
    """
    Produce business insights explaining churn risk drivers.
    """
    if importance_df.empty:
        return "No feature importance results available to interpret."
        
    interpretation_lines = []
    interpretation_lines.append("## Business Churn Drivers Interpretation\n")
    interpretation_lines.append("Analyzing the predictive factors ranking, the following behaviors most strongly indicate churn risk:\n")
    
    for idx, row in importance_df.iterrows():
        feat = row['feature_name']
        score = row['importance_score']
        
        # Simple heuristics for explaining typical features
        if feat == 'recency':
            desc = "Recency represents the days since a customer's last order. Higher recency means a customer has been inactive longer, indicating a higher probability of churn."
            action = "Target customers with high recency (e.g. >90 days) with proactive discount coupons or reactivations."
        elif feat == 'frequency':
            desc = "Frequency counts the customer's total purchases. Low frequency (single-purchase customers) are historically more likely to churn."
            action = "Introduce onboarding loyalty programs for second-purchase incentives."
        elif feat == 'monetary':
            desc = "Monetary measures total spending. Customers with high monetary values represent high-value churners."
            action = "Initiate premium retention support for high-spending customers who show initial signs of inactivity."
        elif feat == 'avg_review_score':
            desc = "Customer feedback score. Customers with low review scores have experienced delivery or quality issues, driving them to churn."
            action = "Direct negative reviews to customer support immediately for follow-up resolution."
        elif feat == 'avg_seller_distance':
            desc = "Average geographic distance from seller. Higher distances lead to longer delivery times and higher shipping fees, causing churn."
            action = "Optimize local seller recommendations and shipping subsidies."
        else:
            desc = f"Feature '{feat}' affects the churn probability calculation."
            action = "Monitor this metric in cohort reporting."
            
        interpretation_lines.append(f"### {row['rank']}. {feat} (Importance: {score:.2%})")
        interpretation_lines.append(f"- **Impact**: {desc}")
        interpretation_lines.append(f"- **CRM Action**: {action}\n")
        
    return "\n".join(interpretation_lines)
