import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

def explain_model(model, X_test, feature_names, output_dir):
    """
    Generates explanations for the trained LightGBM model,
    including tree-based feature importances and SHAP values.
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"Generating explanations and saving to: {output_dir}")
    
    # Ensure X_test is a DataFrame with proper feature names
    if not isinstance(X_test, pd.DataFrame):
        X_test_df = pd.DataFrame(X_test, columns=feature_names)
    else:
        X_test_df = X_test[feature_names].copy()

    # 1. Tree-based Feature Importance
    print("Generating tree-based feature importances...")
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    plt.figure(figsize=(12, 8))
    plt.title("LightGBM Feature Importance (Gain/Split)", fontsize=14)
    plt.barh(range(len(indices)), importances[indices], align="center", color="royalblue")
    plt.yticks(range(len(indices)), [feature_names[i] for i in indices])
    plt.gca().invert_yaxis()  # top-down ordering
    plt.xlabel("Importance Score")
    plt.tight_layout()
    importance_path = os.path.join(output_dir, "feature_importance.png")
    plt.savefig(importance_path, dpi=150)
    plt.close()
    print(f"Saved feature importance plot to {importance_path}")
    
    # Save importance scores to CSV
    imp_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values('importance', ascending=False)
    imp_csv_path = os.path.join(output_dir, "feature_importance.csv")
    imp_df.to_csv(imp_csv_path, index=False)
    print(f"Saved feature importance CSV to {imp_csv_path}")

    # 2. SHAP Values Analysis
    print("Calculating SHAP values...")
    # Use a sample of test data to keep calculations fast and RAM-friendly
    sample_size = min(1000, len(X_test_df))
    X_sample = X_test_df.sample(sample_size, random_state=42) if len(X_test_df) > sample_size else X_test_df
    
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    
    # Handle multi-class / binary output shape differences in SHAP versions
    # For LightGBM classifier, shap_values might be a list of [shap_vals_class0, shap_vals_class1]
    if isinstance(shap_values, list) and len(shap_values) == 2:
        shap_val_pos = shap_values[1]
    else:
        shap_val_pos = shap_values

    # Plot SHAP summary plot (dot plot)
    print("Generating SHAP summary plot...")
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_val_pos, X_sample, show=False)
    plt.title("SHAP Summary Plot (Churn Prediction)", fontsize=14, pad=20)
    plt.tight_layout()
    shap_summary_path = os.path.join(output_dir, "shap_summary.png")
    plt.savefig(shap_summary_path, dpi=150)
    plt.close()
    print(f"Saved SHAP summary plot to {shap_summary_path}")

    # Plot SHAP bar plot
    print("Generating SHAP bar plot...")
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_val_pos, X_sample, plot_type="bar", show=False)
    plt.title("SHAP Feature Importance (Average Impact)", fontsize=14, pad=20)
    plt.tight_layout()
    shap_bar_path = os.path.join(output_dir, "shap_bar.png")
    plt.savefig(shap_bar_path, dpi=150)
    plt.close()
    print(f"Saved SHAP bar plot to {shap_bar_path}")
    
    print("Model explanation generation complete.")
