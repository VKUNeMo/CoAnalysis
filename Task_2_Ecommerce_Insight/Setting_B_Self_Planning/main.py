import gc
import os
import sys
import time
import json
from datetime import datetime

# Add the directory of this file to the python path to fix Windows local import issues with non-ASCII paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psutil
import pandas as pd

from config import DATA_FILES, OUTPUT_DIR
from data_loader.reader import load_and_optimize_csv
from data_loader.aggregator import aggregate_geolocation
from quality.validator import run_data_quality_checks
from transformation.fact_builder import build_order_fact, build_order_item_fact, build_customer_month_fact
from analysis.retention import analyze_customer_retention
from analysis.delivery import analyze_delivery_performance
from analysis.revenue import analyze_revenue_trends
from analysis.correlator import correlate_delivery_and_customer_behavior
from analysis.statistical_tests import run_statistical_tests
from reporting.visualizer import generate_and_save_charts
from reporting.notebook_generator import create_structured_jupyter_notebook

def get_ram_usage_mb() -> float:
    """Returns the current RSS memory usage of the process in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 2)

def log_ram(phase: str):
    """Logs the current memory usage of the process."""
    ram = get_ram_usage_mb()
    print(f"\n[MEM_LOG] {phase} | Current RAM Usage: {ram:.2f} MB\n" + "-" * 50)

def main():
    start_time = time.time()
    print("=" * 60)
    print("STARTING OLIST E-COMMERCE DATA ANALYSIS PIPELINE (SETTING C)")
    print("=" * 60)
    log_ram("Pipeline Start")
    
    # -------------------------------------------------------------
    # PHASE 1: Load and Optimize Memory
    # -------------------------------------------------------------
    print("\n>>> PHASE 1: Loading datasets and optimizing memory...")
    
    # Load each dataset using optimized function
    dfs = {}
    for table_name, file_path in DATA_FILES.items():
        dfs[table_name] = load_and_optimize_csv(file_path, table_name)
        
    # Special optimization: Aggregate geolocation data before merging
    dfs['geolocation'] = aggregate_geolocation(dfs['geolocation'])
    
    log_ram("PHASE 1: Data Loading & Geolocation Aggregation")
    
    # -------------------------------------------------------------
    # PHASE 2: Data Quality Check (with JSON report export)
    # -------------------------------------------------------------
    print("\n>>> PHASE 2: Running data quality validations...")
    dq_results = run_data_quality_checks(dfs, output_dir=OUTPUT_DIR)
    
    log_ram("PHASE 2: Data Quality Checks")
    
    # -------------------------------------------------------------
    # PHASE 3: Data Transformation (Build Fact Tables)
    # -------------------------------------------------------------
    print("\n>>> PHASE 3: Transforming raw data to Fact Tables...")
    
    order_fact = build_order_fact(
        orders_df=dfs['orders'],
        payments_df=dfs['order_payments'],
        customers_df=dfs['customers'],
        valid_delivery_order_ids=dq_results['valid_delivery_order_ids']
    )
    
    order_item_fact = build_order_item_fact(
        items_df=dfs['order_items'],
        products_df=dfs['olist_products_dataset.csv' if 'olist_products_dataset.csv' in dfs else 'products'],
        translation_df=dfs['translation']
    )
    
    customer_month_fact = build_customer_month_fact(order_fact)
    
    log_ram("PHASE 3: Fact Tables Built")
    
    # Free up memory by deleting tables that are no longer needed
    # We only need order_fact, order_item_fact, customer_month_fact, order_reviews and order_payments
    temp_tables_to_delete = ['orders', 'customers', 'geolocation', 'order_items', 'products', 'sellers', 'translation']
    for table in temp_tables_to_delete:
        if table in dfs:
            del dfs[table]
            
    gc.collect()
    log_ram("PHASE 3: Cleaned Unused Raw Tables")
    
    # -------------------------------------------------------------
    # PHASE 4 & 5: Analytical Computations & Correlations
    # -------------------------------------------------------------
    print("\n>>> PHASE 4 & 5: Running statistical computations & correlation models...")
    
    # Customer retention & cohort metrics
    retention_results = analyze_customer_retention(customer_month_fact, order_fact)
    
    # Delivery operational performance metrics
    delivery_results = analyze_delivery_performance(order_fact)
    
    # Revenue multi-dimensional trends
    revenue_results = analyze_revenue_trends(order_fact, order_item_fact, dfs['order_payments'])
    
    # Operational quality vs customer behavior correlations (now with revenue linkage + CLV)
    correlation_results = correlate_delivery_and_customer_behavior(order_fact, customer_month_fact, dfs['order_reviews'])
    
    # Statistical significance tests (Z-test, Mann-Whitney, Partial Correlation)
    statistical_results = run_statistical_tests(order_fact, customer_month_fact, dfs['order_reviews'], order_item_fact)
    
    log_ram("PHASE 4 & 5: Analysis, Correlations & Statistical Tests")
    
    # -------------------------------------------------------------
    # PHASE 6: Save Outputs, Visualization, and Notebook Generation
    # -------------------------------------------------------------
    print("\n>>> PHASE 6: Exporting summarized data, generating plots, and creating report...")
    
    # Save intermediate aggregated dataframes for the Jupyter Notebook to load directly
    # This prevents the notebook from needing to do heavy reads/joins on startup
    retention_results['cohort_retention'].to_csv(os.path.join(OUTPUT_DIR, 'cohort_retention.csv'))
    delivery_results['state_metrics'].to_csv(os.path.join(OUTPUT_DIR, 'state_metrics.csv'), index=False)
    delivery_results['monthly_metrics'].to_csv(os.path.join(OUTPUT_DIR, 'monthly_metrics.csv'), index=False)
    revenue_results['monthly_revenue'].to_csv(os.path.join(OUTPUT_DIR, 'monthly_revenue.csv'), index=False)
    revenue_results['top_categories'].to_csv(os.path.join(OUTPUT_DIR, 'top_categories.csv'), index=False)
    revenue_results['state_revenue'].to_csv(os.path.join(OUTPUT_DIR, 'state_revenue.csv'), index=False)
    revenue_results['payment_metrics'].to_csv(os.path.join(OUTPUT_DIR, 'payment_metrics.csv'), index=False)
    correlation_results['rpr_by_delivery'].to_csv(os.path.join(OUTPUT_DIR, 'rpr_by_delivery.csv'), index=False)
    correlation_results['review_by_delay'].to_csv(os.path.join(OUTPUT_DIR, 'review_by_delay.csv'), index=False)
    
    # New outputs from upgraded correlator
    correlation_results['delay_revenue_impact'].to_csv(os.path.join(OUTPUT_DIR, 'delay_revenue_impact.csv'), index=False)
    correlation_results['clv_by_first_delivery'].to_csv(os.path.join(OUTPUT_DIR, 'clv_by_first_delivery.csv'), index=False)
    
    # Statistical test results
    statistical_results['results_df'].to_csv(os.path.join(OUTPUT_DIR, 'statistical_tests_results.csv'), index=False)
    
    # Prepare combined dictionary of analysis metrics
    all_analysis_metrics = {
        'monthly_revenue': revenue_results['monthly_revenue'],
        'top_categories': revenue_results['top_categories'],
        'state_revenue': revenue_results['state_revenue'],
        'payment_metrics': revenue_results['payment_metrics'],
        'overall_late_rate': delivery_results['overall_late_rate'],
        'state_metrics': delivery_results['state_metrics'],
        'monthly_metrics': delivery_results['monthly_metrics'],
        'cohort_retention': retention_results['cohort_retention'],
        'rpr': retention_results['rpr'],
        'rpr_by_delivery': correlation_results['rpr_by_delivery'],
        'review_by_delay': correlation_results['review_by_delay'],
        'delay_revenue_impact': correlation_results['delay_revenue_impact'],
        'clv_by_first_delivery': correlation_results['clv_by_first_delivery'],
    }
    
    # Save an expanded JSON file with metadata values
    total_unique_customers = len(customer_month_fact)
    repeat_customers_count = int(customer_month_fact['is_repeat_customer'].sum())
    
    validation_summary = dq_results.get('validation_summary', {})
    
    metadata_summary = {
        'run_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'valid_orders_count': len(order_fact),
        'total_unique_customers': total_unique_customers,
        'repeat_customers': repeat_customers_count,
        'time_logic_errors_count': dq_results['time_logic_errors_count'],
        'rpr': retention_results['rpr'],
        'overall_late_rate': delivery_results['overall_late_rate'],
        'late_rate_method': 'delivered_orders_only, datetime_comparison (delivery_timestamp > estimated_timestamp)',
        'total_revenue_payment_value': float(revenue_results['monthly_revenue']['monthly_revenue'].sum()),
        'revenue_method': 'sum(payment_value) per order, grouped monthly',
        'validation_summary': f"{validation_summary.get('passed', 0)}/{validation_summary.get('total_checks', 0)} checks passed",
        'statistical_tests_count': len(statistical_results['results_df']),
        'statistical_tests_significant': int(statistical_results['results_df']['significant'].sum()),
        'hardware_limitations': 'RAM 8GB CPU-Only Optimized'
    }
    with open(os.path.join(OUTPUT_DIR, 'summary_metadata.json'), 'w', encoding='utf-8') as f:
        json.dump(metadata_summary, f, indent=4, ensure_ascii=False)
        
    # Generate and save PNG charts
    chart_paths = generate_and_save_charts(all_analysis_metrics, OUTPUT_DIR)
    
    # Generate structured Jupyter Notebook (with statistical results and validation report)
    # Note: final_report.ipynb will be written in the root directory Task_2_Setting_C
    notebook_path = os.path.join(os.path.dirname(OUTPUT_DIR), "final_report.ipynb")
    create_structured_jupyter_notebook(
        analysis_results=all_analysis_metrics, 
        chart_paths=chart_paths, 
        output_path=notebook_path,
        statistical_results=statistical_results,
        validation_report=dq_results
    )
    
    log_ram("PHASE 6: Output & Reporting Generation")
    
    # Cleanup memory
    del order_fact, order_item_fact, customer_month_fact, dfs
    gc.collect()
    
    end_time = time.time()
    elapsed = end_time - start_time
    print("=" * 60)
    print("OLIST PIPELINE EXECUTION SUCCESSFUL")
    print(f"Total time elapsed: {elapsed:.2f} seconds")
    print(f"Final memory clean: {get_ram_usage_mb():.2f} MB")
    print("=" * 60)

if __name__ == "__main__":
    main()
