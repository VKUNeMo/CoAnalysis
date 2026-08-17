import os

# Default hyperparameters for candidate models
DEFAULT_MODELING_CONFIG = {
    'cv_folds': 3,
    'cv_gap_days': 30,
    'tuner_iter': 20,
    'random_state': 42,
    'memory_limit_gb': 6.0,
    'baseline_models': ['LightGBM', 'XGBoost', 'LogisticRegression']
}
