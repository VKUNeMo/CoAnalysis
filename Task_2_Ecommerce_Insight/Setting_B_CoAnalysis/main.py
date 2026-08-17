import os
import pandas as pd
from utils.logger import get_logger
from config.settings import DATA_DIR
from data_ingestion import load_datasets, validate_schema
from data_preparation import prepare_orders_clean
from data_aggregation import aggregate_revenue, aggregate_customers
from baseline_metrics import calculate_baseline_metrics
from analysis import run_multidimensional_analysis
from validation import run_validation
from visualizations import generate_all_visualizations
from reporting import build_markdown_report, format_insight, format_recommendation

logger = get_logger("main_pipeline")

def main():
    logger.info("Initializing Olist Business Insights Pipeline...")
    
    # Step 1: Load and validate datasets
    try:
        datasets = load_datasets(DATA_DIR)
        schema_report = validate_schema(datasets)
        logger.info("Step 1 (Ingestion & Schema validation) complete.")
    except Exception as e:
        logger.error(f"Error in Step 1 (Ingestion): {str(e)}")
        raise
        
    # Step 2: Prepare clean orders data (SLA, dates, etc.)
    try:
        orders_clean = prepare_orders_clean(datasets['orders'])
        logger.info("Step 2 (Data Preparation) complete.")
    except Exception as e:
        logger.error(f"Error in Step 2 (Preparation): {str(e)}")
        raise
        
    # Step 3: Aggregate revenues and customers
    try:
        order_revenue = aggregate_revenue(datasets['order_payments'], datasets['order_items'])
        customer_summary = aggregate_customers(orders_clean, datasets['customers'], order_revenue)
        logger.info("Step 3 (Data Aggregation) complete.")
    except Exception as e:
        logger.error(f"Error in Step 3 (Aggregation): {str(e)}")
        raise
        
    # Step 4: Calculate overall baseline metrics
    try:
        raw_orders_count = len(datasets['orders'])
        baseline = calculate_baseline_metrics(
            customer_summary, 
            orders_clean, 
            order_revenue, 
            datasets['order_items'], 
            datasets['products'],
            raw_orders_count
        )
        logger.info("Step 4 (Baseline Evaluation) complete.")
    except Exception as e:
        logger.error(f"Error in Step 4 (Baselines): {str(e)}")
        raise
        
    # Step 5: Multi-dimensional analysis
    try:
        analysis_res = run_multidimensional_analysis(
            customer_summary,
            orders_clean,
            order_revenue,
            datasets['order_items'],
            datasets['products'],
            datasets['customers'],
            datasets['sellers'],
            datasets['order_reviews'],
            datasets['orders'],
            datasets['order_payments']
        )
        logger.info("Step 5 (Candidate Modeling / Analysis) complete.")
    except Exception as e:
        logger.error(f"Error in Step 5 (Analysis): {str(e)}")
        raise
        
    # Extract figures dynamically for business insights evidence
    rep_rate = baseline['retention']['repeat_rate']
    rep_days = baseline['retention']['avg_repurchase_days']
    late_rate = baseline['delivery']['late_rate']
    late_days = baseline['delivery']['avg_late_days']
    freight_ratio = baseline['revenue']['freight_ratio']
    
    top_state_row = analysis_res['late_by_state'].iloc[0]
    top_state_name = top_state_row['customer_state']
    top_state_rate = top_state_row['late_rate'] * 100.0
    
    top_cat_row = analysis_res['rev_by_category'].iloc[0]
    top_cat_name = top_cat_row['product_category_name']
    top_cat_revenue = top_cat_row['total_revenue']
    
    # Review score for on_time vs late_30+
    severity_df = analysis_res['late_severity_reviews']
    on_time_score = severity_df[severity_df['late_severity_bin'] == 'on_time']['avg_review_score'].values[0]
    late_30_score = severity_df[severity_df['late_severity_bin'] == 'late_30+']['avg_review_score'].values[0]
    
    on_time_low_rating_pct = severity_df[severity_df['late_severity_bin'] == 'on_time']['low_rating_rate'].values[0] * 100.0
    late_30_low_rating_pct = severity_df[severity_df['late_severity_bin'] == 'late_30+']['low_rating_rate'].values[0] * 100.0
    
    # First-experience impact
    exp_df = analysis_res['first_experience_retention']
    on_time_exp_repeat = exp_df[exp_df['first_order_experience'] == 'on_time']['repeat_rate'].values[0]
    late_exp_repeat = exp_df[exp_df['first_order_experience'] == 'late']['repeat_rate'].values[0]
    
    # Partial Correlation coefficient
    delay_review_corr = analysis_res['corr_matrix'].loc['Late Days', 'Review Score']
    
    # Step 6: Define key quantitative insights (6-10 insights)
    insights = [
        format_insight(
            "INS-01", 
            "Extremely Low Customer Repeat Purchase Propensity",
            "The marketplace exhibits high single-transaction characteristics with only a fraction of customers buying again.",
            "percentage", 
            f"Overall repeat purchase rate: {rep_rate:.2f}%"
        ),
        format_insight(
            "INS-02", 
            "Extended Customer Repurchase Latency",
            "Repeat buyers take several months on average to make their next transaction.",
            "days", 
            f"Average interval between purchases for repeat buyers: {rep_days:.1f} days"
        ),
        format_insight(
            "INS-03", 
            "Pervasive Logistics SLA Non-Compliance",
            "A notable portion of completed orders arrive after the promised estimated delivery date.",
            "percentage", 
            f"Overall delivery late rate: {late_rate:.2f}%"
        ),
        format_insight(
            "INS-04", 
            "Prolonged Logistics Delay Duration",
            "When orders fail to arrive on schedule, the delay stretches for over a week on average.",
            "days", 
            f"Average delay for late deliveries: {late_days:.1f} days"
        ),
        format_insight(
            "INS-05", 
            "Logistical Geographic Discrepancies",
            "Logistics quality is heavily dependent on state geography, with outlying states experiencing severe delays.",
            "percentage_comparison", 
            f"Highest state delay rate: {top_state_name} at {top_state_rate:.2f}% (compared to baseline: {late_rate:.2f}%)"
        ),
        format_insight(
            "INS-06", 
            "Severe Impact of Delay Severity on Satisfaction",
            "Customer satisfaction plummets and negative ratings surge as delivery delays stretch past 30 days.",
            "comparison", 
            f"On-time average rating: {on_time_score:.2f} (Low rating rate: {on_time_low_rating_pct:.1f}%) vs. Late >30 days rating: {late_30_score:.2f} (Low rating rate: {late_30_low_rating_pct:.1f}%)"
        ),
        format_insight(
            "INS-07", 
            "First Impression Logistics Quality Influences Future Loyalty",
            "Buyers who encounter late deliveries on their very first purchase are significantly less likely to repeat buy.",
            "repeat_rate_comparison", 
            f"First-order experience repeat rate: On-Time = {on_time_exp_repeat:.2f}% vs. Late = {late_exp_repeat:.2f}%"
        ),
        format_insight(
            "INS-08", 
            "Highly Concentrated Sales Category Contributions",
            "Delivered revenue is heavily driven by a few dominant product categories.",
            "revenue_sum", 
            f"Top category: '{top_cat_name}' contributing {top_cat_revenue:,.2f} BRL"
        ),
        format_insight(
            "INS-09", 
            "Substantial Freight Overhead Drag on Total GMV",
            "Shipping charges represent a heavy tax on transactions, highlighting logistical friction.",
            "freight_ratio", 
            f"Freight fees share of total payment GMV: {freight_ratio:.2%}"
        ),
        format_insight(
            "INS-10", 
            "Strong Controlled Negative Correlation of Logistics with Review Score",
            "After partialling out categorical, geographical, and temporal confounders, shipping delay remains a major satisfier driver.",
            "partial_correlation", 
            f"Controlled partial correlation between Late Days and Review Score: {delay_review_corr:.4f}"
        )
    ]
    
    # Step 7: Define action-oriented recommendations (linked to insights)
    recommendations = [
        format_recommendation(
            "REC-01",
            "Establish Regional Logistics Cross-Docking in High-Delay States",
            f"Establish regional hubs or select carrier partnerships for states with late rates exceeding {late_rate*1.5:.1f}% (specifically {top_state_name}).",
            ["INS-03", "INS-05"],
            9, 5, 3, "High"
        ),
        format_recommendation(
            "REC-02",
            "Implement a First-Order Experience Customer Recovery Protocol",
            "Proactively issue discount vouchers or apologetic credits to new customers who experience delayed/canceled first orders to protect retention rates.",
            ["INS-01", "INS-07"],
            8, 7, 2, "High"
        ),
        format_recommendation(
            "REC-03",
            "Calibrate SLA Estimation Margins for High-Risk Channels",
            "Adjust the delivery date prediction engine to add margins for outlying regions or high-delay product categories, setting realistic customer expectations.",
            ["INS-03", "INS-06", "INS-10"],
            7, 8, 4, "High"
        ),
        format_recommendation(
            "REC-04",
            "Launch a Seller & Carrier Performance Reward and Penalty Program",
            "Monitor and penalize sellers/carriers whose average delivery delay exceeds 10 days, while incentivizing high-performing on-time sellers.",
            ["INS-03", "INS-04", "INS-06"],
            7, 6, 5, "Medium"
        )
    ]
    
    # Step 8: Validate metrics, comparisons, and traceability
    try:
        validation_res = run_validation(
            customer_summary,
            order_revenue,
            orders_clean,
            datasets['customers'],
            datasets['order_payments'],
            analysis_res['retention_details'],
            analysis_res['first_experience_retention'],
            analysis_res['rev_by_category'],
            analysis_res['monthly_rev_trend'],
            baseline,
            recommendations,
            insights
        )
        logger.info("Step 6 & 7 (Validation & Quality Assurance) complete.")
    except Exception as e:
        logger.error(f"Error in validation step: {str(e)}")
        raise
        
    # Step 8.5: Generate visualization charts
    try:
        vis_dir = generate_all_visualizations(analysis_res, baseline, output_dir="outputs")
        logger.info(f"Step 8 (Visualizations) complete. Saved charts in: {vis_dir}")
    except Exception as e:
        logger.error(f"Error in visualization step: {str(e)}")
        raise
        
    # Step 9: Build report
    try:
        report_path = build_markdown_report(
            baseline,
            analysis_res,
            validation_res,
            insights,
            validation_res['traceability']['classification']['qualified'],
            output_dir="outputs"
        )
        logger.info(f"Pipeline executed successfully. Final report created at: {report_path}")
        print(f"\n=======================================================")
        print(f"SUCCESS: Business insights report built successfully!")
        print(f"Report location: {report_path}")
        print(f"=======================================================\n")
    except Exception as e:
        logger.error(f"Error building markdown report: {str(e)}")
        raise

if __name__ == "__main__":
    main()
