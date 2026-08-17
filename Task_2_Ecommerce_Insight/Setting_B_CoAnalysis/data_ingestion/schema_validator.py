from config.settings import REQUIRED_COLUMNS
from utils.logger import get_logger

logger = get_logger("data_ingestion.schema_validator")

def validate_schema(datasets):
    """
    Validates that each dataset contains the required columns and reports missing values.
    """
    logger.info("Starting schema validation of loaded datasets...")
    validation_report = {}
    
    for table_name, df in datasets.items():
        if table_name not in REQUIRED_COLUMNS:
            continue
            
        required_cols = REQUIRED_COLUMNS[table_name]
        existing_cols = df.columns
        missing_cols = [col for col in required_cols if col not in existing_cols]
        
        if missing_cols:
            error_msg = f"Table '{table_name}' is missing required columns: {missing_cols}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Calculate missing rates for required columns
        missing_rates = {col: float(df[col].isna().mean()) for col in required_cols}
        
        report = {
            'row_count': len(df),
            'missing_rates': missing_rates
        }
        
        # Additional checks for orders status distribution
        if table_name == 'orders':
            status_dist = df['order_status'].value_counts().to_dict()
            report['order_status_dist'] = {str(k): int(v) for k, v in status_dist.items()}
            
        validation_report[table_name] = report
        logger.info(f"Table '{table_name}' validated successfully. Row count: {len(df)}")
        
    return validation_report
