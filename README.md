# Collaborative AI Analysis & Development Framework (CoAnalysis)

This repository contains the codebase and architectural documentation for evaluating Human-AI collaboration modes across data engineering and machine learning tasks.

---

## 📌 Research Overview

The project evaluates three distinct human-AI interaction settings (**Setting A**, **Setting B**, and **Setting C**) applied to two core machine learning and data engineering tasks:

1. **Task 1: E-Commerce Customer Churn Prediction (`Task_1_Churn_Prediction`)**
   - **Domain**: Predictive modeling for customer retention in e-commerce (Olist dataset).
   - **Goal**: End-to-end churn prediction pipeline, including label generation, feature engineering, model training (LightGBM/XGBoost/RandomForest), hyperparameter tuning, model explainability (SHAP), and high-risk customer targeting.

2. **Task 2: E-Commerce Business & Behavioral Insight Extraction (`Task_2_Ecommerce_Insight`)**
   - **Domain**: Advanced exploratory data analysis, RFM segmentation, cohort analysis, and sales metrics aggregation.
   - **Goal**: Analytical data pipeline and visualization framework to derive actionable business insights and retention metrics.

---

## ⚙️ Settings Description

For each task, implementation is structured across three experimental settings:

| Setting | Name | Description |
| :--- | :--- | :--- |
| **Setting A** | **Direct Coding** | Baseline implementation focusing on immediate, direct script development without extensive design phase or modular decomposition. |
| **Setting B** | **CoAnalysis** | Collaborative human-AI workflow featuring iterative planning, modular pipeline separation, comprehensive error handling, unit testing, and design specification. |
| **Setting C** | **Self-Planning** | AI-driven autonomous planning and execution setting where design specifications, modular code structure, and reporting are pre-planned and structured systematically. |

---

## 📁 Repository Structure

```
CoAnalysis/
├── Task_1_Churn_Prediction/
│   ├── Setting_A_Direct_Coding/        # Source code for Task 1 (Direct Coding setting)
│   ├── Setting_B_CoAnalysis/           # Modular pipeline, tests, and DESIGN_TASK_CHURN_DETAIL.md
│   └── Setting_C_Self_Planning/        # Self-planned pipeline, modeling, features, and DESIGN.md
├── Task_2_Ecommerce_Insight/
│   ├── Setting_A_Direct_Coding/        # Analysis script, run scripts, and insights_report.md
│   ├── Setting_B_CoAnalysis/           # Aggregation, ingestion, preparation, validation & DESIGN_TASK_INSIGHT_DETAIL.md
│   └── Setting_C_Self_Planning/        # Jupyter notebooks, reporting, analysis, and DESIGN_C.md
├── .gitignore                          # Configured to exclude raw datasets, trained models, and output artifacts
└── README.md                           # Repository documentation
```

---

## 🛠️ Usage & Setup

Each setting contains its specific requirements and modules. To run any setting:

1. Navigate to the desired task and setting directory:
   ```bash
   cd Task_1_Churn_Prediction/Setting_B_CoAnalysis
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute the pipeline:
   ```bash
   python pipelines/full_pipeline.py
   ```

> **Note**: Raw dataset files (e.g., Olist Brazilian E-Commerce dataset) and generated outputs/trained models are excluded from this repository in compliance with version control best practices.