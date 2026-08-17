import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger("churn_prediction.documentation.technical_doc")

def generate_final_doc_technical_doc(config: Dict[str, Any], best_candidate: Dict[str, Any], features: List[str], output_path: str) -> None:
    """
    Generate final technical documentation detailing pipeline steps, models, and parameters.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    features_list = "\n".join([f"- `{f}`" for f in features])
    params_str = json.dumps(best_candidate.get('best_params', {}), indent=4) if 'best_params' in best_candidate else "{}"
    
    content = f"""# Technical Pipeline Documentation

This technical document details the implementation architecture, parameter spaces, feature matrices, and training schedules of the Olist churn prediction model.

## 1. System Architecture
The codebase is structured into cohesive modules:
- `data_loading/`: memory-efficient parsing with downcasted dtypes and sequential table merging.
- `churn_labeling/`: 90-day inactivity labeling.
- `data_splitting/`: temporal cohort split based on target calendar cutoff dates.
- `baseline/`: baseline Logistic Regression floor evaluation.
- `modeling/`: advanced feature extraction, class weighting, and model training.
- `evaluation/`: performance reporting.
- `explainability/`: feature importance and SHAP analysis.

## 2. Feature Schema
The model uses the following features:
{features_list}

## 3. Best Model Parameter Set
- **Model Name**: {best_candidate.get('model_name', 'N/A')}
- **CV Validation Score (AUC-ROC)**: {best_candidate.get('best_score', 0.0):.4f}
- **Parameters**:
```json
{params_str}
```

## 4. Replication Steps
To execute the pipeline from scratch:
1. Ensure the raw Olist dataset files are located in: `{config['paths']['dataset_dir']}`
2. Run the advanced full pipeline:
```powershell
python pipelines/full_pipeline.py
```
3. The results will populate the output directories specified under `{config['paths']['output_dir']}`.
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Final technical documentation generated at {output_path}")
