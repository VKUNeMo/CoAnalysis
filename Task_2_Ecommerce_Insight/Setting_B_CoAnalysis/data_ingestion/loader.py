import os
import pandas as pd
from utils.logger import get_logger
from config.settings import DATA_DIR, CSV_FILES

logger = get_logger("data_ingestion.loader")

def load_datasets(data_dir=DATA_DIR):
    """
    Loads the 9 CSV files of the Olist dataset and returns them in a dictionary.
    """
    logger.info(f"Starting data loading from directory: {data_dir}")
    datasets = {}
    
    for key, filename in CSV_FILES.items():
        file_path = os.path.join(data_dir, filename)
        if not os.path.exists(file_path):
            error_msg = f"Missing required file: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        logger.info(f"Loading {key} from {filename}...")
        try:
            # Try to read UTF-8 first, fallback to Latin-1
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            logger.warning(f"UTF-8 decoding failed for {filename}. Retrying with latin-1 encoding.")
            df = pd.read_csv(file_path, encoding='latin-1')
            
        if len(df) == 0:
            logger.warning(f"File {filename} is empty.")
            
        datasets[key] = df
        logger.info(f"Successfully loaded {key} with {len(df)} rows and {len(df.columns)} columns.")
        
    return datasets
