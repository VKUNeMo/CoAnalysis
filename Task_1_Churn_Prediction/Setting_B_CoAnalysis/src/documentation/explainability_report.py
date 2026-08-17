import os
import pandas as pd
import logging

logger = logging.getLogger("churn_prediction.documentation.explainability_report")

def generate_final_doc_explainability_report(importance_df: pd.DataFrame, interpretation: str, output_path: str) -> None:
    """
    Generate final explainability report document.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    table_rows = []
    if not importance_df.empty:
        for idx, row in importance_df.iterrows():
            table_rows.append(f"| {row['rank']} | `{row['feature_name']}` | {row['importance_score']:.4%} |")
    table_str = "\n".join(table_rows)
    
    content = f"""# Model Explainability & Interpretability Report

This document details the core drivers of customer churn based on model feature importances and SHAP impact analysis.

## Feature Importance Rankings

| Rank | Feature | Importance Score |
|---|---|---|
{table_str}

{interpretation}

---
*Actionable CRM guidelines are designed based on expectation value optimizations matching typical e-commerce operations.*
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Final explainability document generated at {output_path}")
