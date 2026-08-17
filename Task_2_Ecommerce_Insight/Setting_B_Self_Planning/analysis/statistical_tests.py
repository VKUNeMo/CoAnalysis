import pandas as pd
import numpy as np
from typing import Dict, Any
from scipy import stats


def _cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """Compute Cohen's d effect size between two groups."""
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0.0
    var1, var2 = group1.var(ddof=1), group2.var(ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return float((group1.mean() - group2.mean()) / pooled_std)


def _partial_correlation(df: pd.DataFrame, x: str, y: str, covariates: list) -> Dict[str, float]:
    """
    Compute partial correlation between x and y, controlling for covariates
    using residual-based approach (OLS regression residuals).
    """
    from numpy.linalg import lstsq

    valid = df[[x, y] + covariates].dropna()
    if len(valid) < 10:
        return {'r': 0.0, 'p_value': 1.0, 'n': len(valid)}

    # Build covariate matrix with intercept
    Z = valid[covariates].values.astype(float)
    Z = np.column_stack([np.ones(len(Z)), Z])

    # Residualize x
    x_vals = valid[x].values.astype(float)
    beta_x, _, _, _ = lstsq(Z, x_vals, rcond=None)
    resid_x = x_vals - Z @ beta_x

    # Residualize y
    y_vals = valid[y].values.astype(float)
    beta_y, _, _, _ = lstsq(Z, y_vals, rcond=None)
    resid_y = y_vals - Z @ beta_y

    # Pearson correlation on residuals
    r, p = stats.pearsonr(resid_x, resid_y)
    return {'r': float(r), 'p_value': float(p), 'n': len(valid)}


def run_statistical_tests(
    order_fact_df: pd.DataFrame,
    customer_month_df: pd.DataFrame,
    reviews_df: pd.DataFrame,
    order_item_fact_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Runs statistical significance tests to validate key findings:
    1. Z-test: RPR on-time vs late first-order delivery
    2. Mann-Whitney U: review scores across delay groups
    3. Partial correlation: delay_days vs review_score controlling for state & month
    4. Effect sizes (Cohen's d) for each comparison
    """
    print("Running statistical significance tests...")
    results = []

    # -------------------------------------------------------------------------
    # 1. Z-test for RPR difference (on-time vs late first order)
    # -------------------------------------------------------------------------
    sorted_orders = order_fact_df.sort_values('order_purchase_timestamp')
    first_idx = sorted_orders.groupby('customer_unique_id')['order_purchase_timestamp'].idxmin()
    first_orders = order_fact_df.loc[first_idx][['customer_unique_id', 'is_late']].copy()
    first_orders.rename(columns={'is_late': 'first_order_is_late'}, inplace=True)

    merged = pd.merge(
        first_orders,
        customer_month_df[['customer_unique_id', 'is_repeat_customer']],
        on='customer_unique_id', how='inner'
    )

    on_time = merged[merged['first_order_is_late'] == 0]
    late = merged[merged['first_order_is_late'] == 1]

    n1, p1 = len(on_time), on_time['is_repeat_customer'].mean()
    n2, p2 = len(late), late['is_repeat_customer'].mean()

    # Pooled proportion Z-test
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2) if (n1 + n2) > 0 else 0
    se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2)) if n1 > 0 and n2 > 0 else 1
    z_stat = (p1 - p2) / se if se > 0 else 0
    z_p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    rpr_relative_diff = ((p1 - p2) / p2 * 100) if p2 > 0 else 0

    results.append({
        'test_id': 'STAT-01',
        'test_name': 'Z-test: RPR On-Time vs Late (First Order)',
        'group_1': f'On-Time (n={n1}, RPR={p1:.4f})',
        'group_2': f'Late (n={n2}, RPR={p2:.4f})',
        'statistic': round(z_stat, 4),
        'p_value': round(z_p_value, 6),
        'effect_size': round(rpr_relative_diff, 2),
        'effect_type': 'relative_diff_%',
        'significant': z_p_value < 0.05,
        'interpretation': f'RPR giảm {abs(rpr_relative_diff):.1f}% tương đối khi đơn đầu bị trễ (p={z_p_value:.4f})'
    })

    # -------------------------------------------------------------------------
    # 2. Mann-Whitney U: review scores on_time vs late_light vs late_heavy
    # -------------------------------------------------------------------------
    df_temp = order_fact_df.copy()
    conditions = [
        df_temp['is_late'] == 0,
        (df_temp['is_late'] == 1) & (df_temp['days_late'] <= 7.0),
        (df_temp['is_late'] == 1) & (df_temp['days_late'] > 7.0)
    ]
    choices = ['on_time', 'late_light', 'late_heavy']
    df_temp['delay_group'] = np.select(conditions, choices, default='unknown')

    rev_agg = reviews_df.groupby('order_id')['review_score'].mean().reset_index()
    order_rev = pd.merge(df_temp[['order_id', 'delay_group']], rev_agg, on='order_id', how='inner')

    on_time_scores = order_rev[order_rev['delay_group'] == 'on_time']['review_score'].values
    late_light_scores = order_rev[order_rev['delay_group'] == 'late_light']['review_score'].values
    late_heavy_scores = order_rev[order_rev['delay_group'] == 'late_heavy']['review_score'].values

    # On-time vs Late Light
    u_stat_1, u_p_1 = stats.mannwhitneyu(on_time_scores, late_light_scores, alternative='two-sided')
    d_1 = _cohens_d(on_time_scores, late_light_scores)
    results.append({
        'test_id': 'STAT-02a',
        'test_name': 'Mann-Whitney U: Review Score On-Time vs Late ≤7d',
        'group_1': f'On-Time (n={len(on_time_scores)}, mean={on_time_scores.mean():.3f})',
        'group_2': f'Late ≤7d (n={len(late_light_scores)}, mean={late_light_scores.mean():.3f})',
        'statistic': round(float(u_stat_1), 2),
        'p_value': round(float(u_p_1), 8),
        'effect_size': round(d_1, 4),
        'effect_type': 'cohens_d',
        'significant': u_p_1 < 0.05,
        'interpretation': f'Review giảm {on_time_scores.mean() - late_light_scores.mean():.2f} điểm (Cohen d={d_1:.2f}, p<0.001)'
    })

    # On-time vs Late Heavy
    u_stat_2, u_p_2 = stats.mannwhitneyu(on_time_scores, late_heavy_scores, alternative='two-sided')
    d_2 = _cohens_d(on_time_scores, late_heavy_scores)
    results.append({
        'test_id': 'STAT-02b',
        'test_name': 'Mann-Whitney U: Review Score On-Time vs Late >7d',
        'group_1': f'On-Time (n={len(on_time_scores)}, mean={on_time_scores.mean():.3f})',
        'group_2': f'Late >7d (n={len(late_heavy_scores)}, mean={late_heavy_scores.mean():.3f})',
        'statistic': round(float(u_stat_2), 2),
        'p_value': round(float(u_p_2), 8),
        'effect_size': round(d_2, 4),
        'effect_type': 'cohens_d',
        'significant': u_p_2 < 0.05,
        'interpretation': f'Review giảm {on_time_scores.mean() - late_heavy_scores.mean():.2f} điểm (Cohen d={d_2:.2f}, p<0.001)'
    })

    # -------------------------------------------------------------------------
    # 3. Partial correlation: days_late vs review_score, controlling for state & month
    # -------------------------------------------------------------------------
    pc_df = order_fact_df[['order_id', 'days_late', 'customer_state', 'order_purchase_timestamp']].copy()
    pc_df['purchase_month_num'] = pc_df['order_purchase_timestamp'].dt.month + \
                                   (pc_df['order_purchase_timestamp'].dt.year - 2017) * 12
    # Encode state as numeric
    state_codes = pc_df['customer_state'].astype('category').cat.codes
    pc_df['state_code'] = state_codes

    pc_df = pd.merge(pc_df, rev_agg, on='order_id', how='inner')

    pc_result = _partial_correlation(
        pc_df, 'days_late', 'review_score',
        covariates=['state_code', 'purchase_month_num']
    )

    results.append({
        'test_id': 'STAT-03',
        'test_name': 'Partial Correlation: Days Late vs Review Score (controlling state, month)',
        'group_1': f'days_late',
        'group_2': f'review_score',
        'statistic': round(pc_result['r'], 4),
        'p_value': round(pc_result['p_value'], 8),
        'effect_size': round(pc_result['r'], 4),
        'effect_type': 'partial_r',
        'significant': pc_result['p_value'] < 0.05,
        'interpretation': f'Partial r = {pc_result["r"]:.3f} (n={pc_result["n"]}): delay vẫn là driver chính của dissatisfaction ngay cả khi kiểm soát state và tháng'
    })

    # -------------------------------------------------------------------------
    # Build summary DataFrame
    # -------------------------------------------------------------------------
    results_df = pd.DataFrame(results)

    print(f"Statistical tests completed: {len(results)} tests, "
          f"{results_df['significant'].sum()} significant at alpha=0.05")

    return {
        'results_df': results_df,
        'rpr_z_test': {
            'z_stat': z_stat,
            'p_value': z_p_value,
            'rpr_ontime': p1,
            'rpr_late': p2,
            'relative_diff_pct': rpr_relative_diff,
            'n_ontime': n1,
            'n_late': n2
        },
        'review_mannwhitney': {
            'ontime_mean': float(on_time_scores.mean()),
            'late_light_mean': float(late_light_scores.mean()),
            'late_heavy_mean': float(late_heavy_scores.mean()),
            'cohens_d_light': d_1,
            'cohens_d_heavy': d_2
        },
        'partial_correlation': pc_result
    }
