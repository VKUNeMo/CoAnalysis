import numpy as np
import pandas as pd
from scipy import stats

def proportions_ztest_custom(count1, nobs1, count2, nobs2):
    """
    Perform a two-sample z-test of proportions.
    """
    p1 = count1 / nobs1
    p2 = count2 / nobs2
    p_combined = (count1 + count2) / (nobs1 + nobs2)
    
    # Standard error
    se = np.sqrt(p_combined * (1 - p_combined) * (1 / nobs1 + 1 / nobs2))
    if se == 0:
        return 0.0, 1.0  # z-stat = 0, p-val = 1
        
    z_stat = (p1 - p2) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    return z_stat, p_value

def cohens_d(group1, group2):
    """
    Calculate Cohen's d effect size for two independent samples.
    """
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_se = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_se == 0:
        return 0.0
        
    mean1, mean2 = np.mean(group1), np.mean(group2)
    return (mean1 - mean2) / pooled_se

def calculate_partial_correlation(df, x_col, y_col, control_cols):
    """
    Calculate partial correlation between x_col and y_col controlling for control_cols.
    This runs OLS of x on controls and y on controls, and calculates Pearson correlation of their residuals.
    Uses pure numpy/scipy (pseudo-inverse) to avoid external package dependencies like statsmodels.
    """
    # Drop rows with missing values in relevant columns
    cols_to_use = [x_col, y_col] + control_cols
    clean_df = df[cols_to_use].dropna()
    if len(clean_df) < 5:
        return 0.0, 1.0
        
    # Standardize target variables
    std_x = clean_df[x_col].std()
    std_y = clean_df[y_col].std()
    
    X_target = (clean_df[x_col] - clean_df[x_col].mean()) / (std_x if std_x > 0 else 1.0)
    Y_target = (clean_df[y_col] - clean_df[y_col].mean()) / (std_y if std_y > 0 else 1.0)
    
    # One-hot encode categorical control variables
    controls_encoded = pd.get_dummies(clean_df[control_cols], drop_first=True)
    Z = controls_encoded.astype(float).values
    
    # Add constant column (column of ones) for OLS intercept
    Z_const = np.column_stack([np.ones(Z.shape[0]), Z])
    
    # Compute OLS coefficients using pseudo-inverse for numerical stability
    try:
        pinv_Z = np.linalg.pinv(Z_const)
        
        # Residuals for X target
        beta_x = pinv_Z @ X_target.values
        res_x = X_target.values - Z_const @ beta_x
        
        # Residuals for Y target
        beta_y = pinv_Z @ Y_target.values
        res_y = Y_target.values - Z_const @ beta_y
        
        # Pearson correlation of residuals
        corr, pval = stats.pearsonr(res_x, res_y)
        return corr, pval
    except Exception as e:
        # Fallback to simple pearson correlation if regression fails
        corr, pval = stats.pearsonr(X_target.values, Y_target.values)
        return corr, pval

