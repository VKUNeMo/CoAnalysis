# Relational E-Commerce Insights & Descriptive Analytics Pipeline

This repository implements a modular Python-based data analytics pipeline for processing the **Olist Brazilian E-Commerce Dataset** (~100,000 orders spanning 32 months). The system generates key descriptive metrics and statistical validations regarding customer retention, delivery performance (SLAs), and revenue growth.

The implementation details follow the blueprint in `DESIGN_TASK_INSIGHT_DETAIL.md`.

## Project Structure
- `config/`: Contains `settings.py` managing paths, required schemas, and configuration parameters.
- `utils/`: Common utilities for logging, datetime handling, and statistical functions.
- `data_ingestion/`: Handles loading 9 CSV files and verifying their schemas.
- `data_preparation/`: Standardizes date-level indices and computes logistics SLA tags.
- `data_aggregation/`: Groups orders by unique customers and sums GMV without double counting.
- `baseline_metrics/`: Evaluates overall baseline statistics for all three business pillars.
- `analysis/`: Computes monthly cohort retention matrices, logistics segments, and controlled partial correlations.
- `validation/`: Integrates data audits, statistical significance testing (Proportion Z-Test/t-test), and recommendation traceability mapping.
- `reporting/`: Compiles findings and validation checks into the final Markdown report.
- `main.py`: Pipeline entry point coordinating all stages.
- `requirements.txt`: Project dependencies list.

## Setup & Running
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure the dataset directory in `config/settings.py` (defaults to the dataset folder path).
3. Execute the pipeline:
   ```bash
   python main.py
   ```
4. Find the generated report at `outputs/olist_business_insights_report.md` and logging history in `outputs/analytics.log`.

## License
This analysis uses the public Olist Brazilian E-Commerce dataset.
- License: **CC BY-NC-SA 4.0**
- Usage: Non-commercial only, sharing under similar terms.
