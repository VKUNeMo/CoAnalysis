import os
import pandas as pd
import logging

logger = logging.getLogger("churn_prediction.high_risk_list.exporter")

def export_high_risk_list(df: pd.DataFrame, output_path: str, format_type: str = 'csv') -> None:
    """
    Export the high-risk customer list to CSV or Excel with rounded probabilities.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Format probabilities
    export_df = df.copy()
    export_df['churn_probability'] = export_df['churn_probability'].round(4)
    
    if format_type.lower() == 'csv':
        export_df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"High-risk list successfully exported to CSV at {output_path}")
    elif format_type.lower() == 'excel' or format_type.lower() == 'xlsx':
        try:
            export_df.to_excel(output_path, index=False, sheet_name='High-Risk Customers')
            logger.info(f"High-risk list successfully exported to Excel at {output_path}")
        except Exception as e:
            logger.error(f"Excel export failed. Falling back to CSV. Error: {e}")
            csv_fallback = output_path.replace('.xlsx', '.csv').replace('.xls', '.csv')
            export_df.to_csv(csv_fallback, index=False, encoding='utf-8')
    else:
        raise ValueError(f"Unsupported format type: {format_type}")
        
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        logger.info(f"Export file verified: size is {os.path.getsize(output_path)} bytes.")
    else:
        logger.warning("Export verification failed. File is missing or empty.")
