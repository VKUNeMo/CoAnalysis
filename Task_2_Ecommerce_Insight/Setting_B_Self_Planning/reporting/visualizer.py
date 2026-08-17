import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, Any

def generate_and_save_charts(analysis_results: Dict[str, Any], output_dir: str) -> Dict[str, str]:
    """
    Generates and saves high-quality charts for Olist analysis:
    1. Monthly Revenue & Late Delivery Trends
    2. Cohort Retention Heatmap
    3. Top 10 Product Categories by Revenue
    4. RPR by First Order Delivery Status
    5. Average Review Score by Lateness Group
    """
    print("Generating charts...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Set style for all charts
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
        'figure.titlesize': 18,
        'axes.titlesize': 16,
        'axes.labelsize': 14,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 12
    })
    
    chart_paths = {}
    
    # 1. Monthly Revenue & Late Delivery Trends (Double Plot side-by-side)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
    
    monthly_rev = analysis_results['monthly_revenue']
    sns.lineplot(
        data=monthly_rev, 
        x='purchase_month', 
        y='monthly_revenue', 
        marker='o', 
        color='#1f77b4', 
        linewidth=2.5, 
        ax=ax1
    )
    ax1.set_title("Monthly Revenue Trend (R$)", pad=15, fontweight='bold')
    ax1.set_xlabel("Purchase Month")
    ax1.set_ylabel("Revenue (R$)")
    ax1.tick_params(axis='x', rotation=45)
    # Format y-axis as thousands/millions
    ax1.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    
    monthly_del = analysis_results['monthly_metrics']
    sns.lineplot(
        data=monthly_del, 
        x='purchase_month', 
        y='late_rate', 
        marker='s', 
        color='#d62728', 
        linewidth=2.5, 
        ax=ax2
    )
    ax2.set_title("Monthly Late Delivery Rate Trend", pad=15, fontweight='bold')
    ax2.set_xlabel("Purchase Month")
    ax2.set_ylabel("Late Delivery Rate")
    ax2.tick_params(axis='x', rotation=45)
    ax2.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:.1%}".format(x)))
    
    plt.tight_layout()
    path_trends = os.path.join(output_dir, "monthly_trends.png")
    plt.savefig(path_trends, dpi=150, bbox_inches='tight')
    plt.close()
    chart_paths['monthly_trends'] = path_trends
    
    # 2. Cohort Retention Heatmap
    cohort_ret = analysis_results['cohort_retention']
    plt.figure(figsize=(14, 8))
    
    # Select a subset of cohorts to make the heatmap readable (e.g. cohorts with complete data or just the top rows)
    # We will show the retention rate in percentage
    sns.heatmap(
        cohort_ret, 
        annot=True, 
        fmt=".1%", 
        cmap="YlGnBu", 
        linewidths=.5, 
        cbar_kws={'label': 'Retention Rate'},
        vmin=0.0, 
        vmax=0.1  # Cap at 10% for color scaling since retention is low in this dataset
    )
    plt.title("Cohort Retention Matrix (Month 0 to Month 6)", pad=20, fontweight='bold')
    plt.xlabel("Months Active")
    plt.ylabel("Cohort Start Month")
    
    plt.tight_layout()
    path_cohort = os.path.join(output_dir, "cohort_retention.png")
    plt.savefig(path_cohort, dpi=150, bbox_inches='tight')
    plt.close()
    chart_paths['cohort_retention'] = path_cohort
    
    # 3. Top 10 Product Categories by Revenue
    top_cats = analysis_results['top_categories']
    plt.figure(figsize=(12, 7))
    
    sns.barplot(
        data=top_cats, 
        y='product_category_name_english', 
        x='category_revenue', 
        palette="viridis"
    )
    plt.title("Top 10 Product Categories by Revenue Contribution", pad=15, fontweight='bold')
    plt.xlabel("Total Revenue (R$)")
    plt.ylabel("Category")
    
    # Add values on the bars
    for index, value in enumerate(top_cats['category_revenue']):
        plt.text(value, index, f" R$ {value:,.0f}", va='center', fontsize=10)
        
    plt.tight_layout()
    path_cats = os.path.join(output_dir, "top_categories.png")
    plt.savefig(path_cats, dpi=150, bbox_inches='tight')
    plt.close()
    chart_paths['top_categories'] = path_cats
    
    # 4. RPR by First Order Delivery Status
    rpr_df = analysis_results['rpr_by_delivery']
    plt.figure(figsize=(8, 6))
    
    ax = sns.barplot(
        data=rpr_df, 
        x='first_order_status', 
        y='rpr', 
        palette=['#2ca02c', '#d62728']
    )
    plt.title("Repeat Purchase Rate (RPR) by First Order Delivery Status", pad=15, fontweight='bold')
    plt.xlabel("First Order Delivery Status")
    plt.ylabel("Repeat Purchase Rate")
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:.2%}".format(x)))
    
    # Add value annotations on top of bars
    for p in ax.patches:
        height = p.get_height()
        ax.annotate(f'{height:.2%}',
                    xy=(p.get_x() + p.get_width() / 2, height),
                    xytext=(0, 5),  # 5 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontweight='bold', fontsize=12)
                    
    plt.ylim(0, rpr_df['rpr'].max() * 1.25)
    plt.tight_layout()
    path_rpr = os.path.join(output_dir, "rpr_by_delivery.png")
    plt.savefig(path_rpr, dpi=150, bbox_inches='tight')
    plt.close()
    chart_paths['rpr_by_delivery'] = path_rpr
    
    # 5. Average Review Score by Lateness Group
    rev_delay = analysis_results['review_by_delay']
    plt.figure(figsize=(10, 6))
    
    # Map group names to prettier names
    rev_delay_mapped = rev_delay.copy()
    label_map = {
        'on_time': 'On Time\n(is_late = 0)',
        'late_light': 'Late 1-7 Days\n(days_late \u2264 7)',
        'late_heavy': 'Late > 7 Days\n(days_late > 7)'
    }
    rev_delay_mapped['delay_group_label'] = rev_delay_mapped['delay_group'].map(label_map)
    
    ax = sns.barplot(
        data=rev_delay_mapped, 
        x='delay_group_label', 
        y='avg_review_score', 
        palette="coolwarm"
    )
    plt.title("Average Review Score by Delivery Delay Severity", pad=15, fontweight='bold')
    plt.xlabel("Delivery Status & Severity")
    plt.ylabel("Average Review Score (1-5)")
    
    # Add values on top of bars
    for p in ax.patches:
        height = p.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(p.get_x() + p.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom', fontweight='bold', fontsize=12)
                    
    plt.ylim(0, 5.5)
    plt.tight_layout()
    path_reviews = os.path.join(output_dir, "review_by_delay.png")
    plt.savefig(path_reviews, dpi=150, bbox_inches='tight')
    plt.close()
    chart_paths['review_by_delay'] = path_reviews
    
    print(f"Charts saved successfully in {os.path.basename(output_dir)}")
    return chart_paths
