import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from utils.logger import get_logger

logger = get_logger("visualizations.chart_generator")

# Set style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 10

COLORS = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e',
    'success': '#2ca02c',
    'danger': '#d62728',
    'warning': '#9467bd',
    'dark': '#333333',
    'light_bg': '#f8f9fa'
}

def plot_monthly_revenue_trend(monthly_rev_trend, output_dir):
    """
    Plots dual-axis chart: Monthly GMV (Revenue) & Completed Order Volume over time.
    """
    if monthly_rev_trend.empty:
        return
        
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    x = [str(m) for m in monthly_rev_trend['month']]
    y_rev = monthly_rev_trend['total_revenue'] / 1e3  # in thousands BRL
    y_ord = monthly_rev_trend['order_count']
    
    color_rev = '#1f77b4'
    color_ord = '#ff7f0e'
    
    # Bar chart for Order Volume
    ax1.set_xlabel('Month', fontweight='bold')
    ax1.set_ylabel('Order Count', color=color_ord, fontweight='bold')
    bars = ax1.bar(x, y_ord, color=color_ord, alpha=0.3, label='Order Count')
    ax1.tick_params(axis='y', labelcolor=color_ord)
    plt.xticks(rotation=45, ha='right')
    
    # Line chart for Revenue
    ax2 = ax1.twinx()
    ax2.set_ylabel('Delivered Revenue (k BRL)', color=color_rev, fontweight='bold')
    line = ax2.plot(x, y_rev, color=color_rev, marker='o', linewidth=2.5, label='GMV Revenue (k BRL)')
    ax2.tick_params(axis='y', labelcolor=color_rev)
    
    plt.title('Monthly Delivered GMV Revenue & Completed Order Volume (Jan 2016 - Aug 2018)', pad=15, fontweight='bold')
    fig.tight_layout()
    
    save_path = os.path.join(output_dir, "monthly_revenue_trend.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved chart to {save_path}")

def plot_delay_rate_by_state(late_by_state, baseline_late_rate, output_dir):
    """
    Plots Top 10 States by Delivery Delay Rate (%) vs Baseline.
    """
    if late_by_state.empty:
        return
        
    df_top = late_by_state.head(10).copy()
    df_top['late_rate_pct'] = df_top['late_rate'] * 100.0
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    bars = ax.barh(df_top['customer_state'][::-1], df_top['late_rate_pct'][::-1], color='#e74c3c', alpha=0.85)
    ax.axvline(x=baseline_late_rate * 100.0, color='#2c3e50', linestyle='--', linewidth=1.5, 
               label=f'National Average ({baseline_late_rate*100.0:.2f}%)')
    
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.3, bar.get_y() + bar.get_height()/2, f'{width:.1f}%', 
                va='center', ha='left', fontsize=9, fontweight='bold')
                
    ax.set_xlabel('Delivery Late Rate (%)', fontweight='bold')
    ax.set_ylabel('Customer State', fontweight='bold')
    ax.set_title('Top 10 Brazilian States by Logistics Delivery Late Rate', pad=15, fontweight='bold')
    ax.legend(loc='lower right')
    fig.tight_layout()
    
    save_path = os.path.join(output_dir, "delay_rate_by_state.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved chart to {save_path}")

def plot_review_score_by_delay_severity(late_severity_reviews, output_dir):
    """
    Plots Average Review Score and Low Rating Rate by Delay Severity Bin.
    """
    if late_severity_reviews.empty:
        return
        
    fig, ax1 = plt.subplots(figsize=(10, 5))
    
    bins = late_severity_reviews['late_severity_bin'].astype(str)
    avg_score = late_severity_reviews['avg_review_score']
    low_rate = late_severity_reviews['low_rating_rate'] * 100.0
    
    # Bar chart for Avg Review Score
    bars = ax1.bar(bins, avg_score, color='#2980b9', alpha=0.75, width=0.4, label='Avg Review Score (1-5)')
    ax1.set_ylabel('Average Review Score', color='#2980b9', fontweight='bold')
    ax1.set_ylim(1, 5)
    ax1.tick_params(axis='y', labelcolor='#2980b9')
    ax1.set_xlabel('Delivery Delay Severity Bin', fontweight='bold')
    
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height - 0.3, f'{height:.2f}',
                 ha='center', va='bottom', color='white', fontweight='bold')
                 
    # Twin axis for Low Rating Rate
    ax2 = ax1.twinx()
    line = ax2.plot(bins, low_rate, color='#c0392b', marker='s', linewidth=2.5, markersize=8, label='Low Rating Rate (<=3 Stars)')
    ax2.set_ylabel('Low Rating Rate (%)', color='#c0392b', fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='#c0392b')
    ax2.set_ylim(0, 100)
    
    for i, txt in enumerate(low_rate):
        ax2.annotate(f'{txt:.1f}%', (bins.iloc[i], low_rate.iloc[i] + 3), 
                     ha='center', color='#c0392b', fontweight='bold')
                     
    plt.title('Impact of Delivery Delay Severity on Customer Satisfaction & Negative Ratings', pad=15, fontweight='bold')
    fig.tight_layout()
    
    save_path = os.path.join(output_dir, "review_score_by_delay_severity.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved chart to {save_path}")

def plot_first_experience_impact(first_experience_retention, output_dir):
    """
    Plots Customer Repeat Purchase Rate by First Order Experience (On-Time vs Late).
    """
    if first_experience_retention.empty:
        return
        
    fig, ax = plt.subplots(figsize=(7, 5))
    
    exp = first_experience_retention['first_order_experience'].astype(str).str.replace('_', ' ').str.title()
    rates = first_experience_retention['repeat_rate']
    
    colors = ['#27ae60' if 'On' in e else '#e74c3c' for e in exp]
    bars = ax.bar(exp, rates, color=colors, width=0.45, alpha=0.85)
    
    ax.set_ylabel('Customer Repeat Purchase Rate (%)', fontweight='bold')
    ax.set_ylim(0, max(rates) * 1.35 if max(rates) > 0 else 10)
    ax.set_title('First-Order Delivery Experience vs. Future Repeat Purchase Rate', pad=15, fontweight='bold')
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1, f'{height:.2f}%',
                ha='center', va='bottom', fontweight='bold', fontsize=11)
                
    fig.tight_layout()
    
    save_path = os.path.join(output_dir, "first_experience_impact.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved chart to {save_path}")

def plot_top_categories_revenue(rev_by_category, output_dir):
    """
    Plots Top 10 Product Categories by Delivered GMV Revenue (BRL).
    """
    if rev_by_category.empty:
        return
        
    df_top = rev_by_category.head(10).copy()
    col_cat = 'product_category' if 'product_category' in df_top.columns else 'product_category_name'
    
    df_top['rev_k'] = df_top['total_revenue'] / 1e3
    
    fig, ax = plt.subplots(figsize=(10, 5.5))
    
    bars = ax.barh(df_top[col_cat][::-1], df_top['rev_k'][::-1], color='#3498db', alpha=0.85)
    
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 10, bar.get_y() + bar.get_height()/2, f'{width:,.1f}k BRL', 
                va='center', ha='left', fontsize=9, fontweight='bold')
                
    ax.set_xlabel('Delivered GMV Revenue (Thousand BRL)', fontweight='bold')
    ax.set_ylabel('Product Category', fontweight='bold')
    ax.set_title('Top 10 Product Categories by Delivered Revenue Contribution', pad=15, fontweight='bold')
    fig.tight_layout()
    
    save_path = os.path.join(output_dir, "top_categories_revenue.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved chart to {save_path}")

def plot_cohort_retention_heatmap(retention_matrix, output_dir):
    """
    Plots Cohort Retention Matrix Heatmap (First 12 Cohorts, Months 0 to 6).
    """
    if retention_matrix.empty:
        return
        
    df_plot = retention_matrix.iloc[:12, :7].copy()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.heatmap(df_plot, annot=True, fmt='.2f', cmap='YlGnBu', cbar_kws={'label': 'Retention Rate (%)'},
                ax=ax, linewidths=0.5, annot_kws={'weight': 'bold', 'size': 9})
                
    ax.set_title('Cohort Customer Retention Rate Heatmap (%) (First 12 Cohorts)', pad=15, fontweight='bold')
    ax.set_xlabel('Months Since First Purchase', fontweight='bold')
    ax.set_ylabel('Cohort Month', fontweight='bold')
    fig.tight_layout()
    
    save_path = os.path.join(output_dir, "cohort_retention_heatmap.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved chart to {save_path}")

def generate_all_visualizations(analysis_results, baseline_metrics, output_dir="outputs"):
    """
    Generates and saves all 6 core business visualization plots.
    """
    logger.info("Generating publication-ready visualization charts...")
    vis_dir = os.path.join(output_dir, "visualizations")
    os.makedirs(vis_dir, exist_ok=True)
    
    baseline_late_rate = baseline_metrics['delivery']['late_rate'] / 100.0 if baseline_metrics['delivery']['late_rate'] > 1.0 else baseline_metrics['delivery']['late_rate']
    
    plot_monthly_revenue_trend(analysis_results['monthly_rev_trend'], vis_dir)
    plot_delay_rate_by_state(analysis_results['late_by_state'], baseline_late_rate, vis_dir)
    plot_review_score_by_delay_severity(analysis_results['late_severity_reviews'], vis_dir)
    plot_first_experience_impact(analysis_results['first_experience_retention'], vis_dir)
    plot_top_categories_revenue(analysis_results['rev_by_category'], vis_dir)
    plot_cohort_retention_heatmap(analysis_results['retention_matrix'], vis_dir)
    
    logger.info(f"All visualizations successfully generated in {vis_dir}")
    return vis_dir
