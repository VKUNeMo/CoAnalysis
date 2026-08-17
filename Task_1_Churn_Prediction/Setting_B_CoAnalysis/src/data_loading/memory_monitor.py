import logging
import os
import warnings

# Define a custom MemoryWarning
class MemoryWarning(UserWarning):
    pass

logger = logging.getLogger("churn_prediction.memory_monitor")

def check_usage(df=None, threshold_gb=6.0, process_level=False):
    """
    Monitor memory usage of a DataFrame or the entire process.
    Raises a MemoryWarning if the usage exceeds threshold_gb.
    """
    current_usage_gb = 0.0
    
    if df is not None:
        # Compute exact dataframe size in gigabytes
        current_usage_gb = df.memory_usage(deep=True).sum() / 1e9
        logger.info(f"DataFrame memory usage: {current_usage_gb:.4f} GB")
    
    if process_level:
        try:
            import psutil
            process = psutil.Process(os.getpid())
            current_usage_gb = process.memory_info().rss / 1e9
            logger.info(f"Process physical memory (RSS) usage: {current_usage_gb:.4f} GB")
        except ImportError:
            logger.warning("psutil is not installed. Skipping process-level memory monitoring.")
            # Fall back to dataframe check only or zero
    
    exceeded = current_usage_gb > threshold_gb
    
    report = {
        "current_usage_gb": current_usage_gb,
        "threshold_gb": threshold_gb,
        "exceeded": exceeded
    }
    
    if exceeded:
        msg = f"Memory usage ({current_usage_gb:.4f} GB) exceeded threshold ({threshold_gb:.4f} GB)!"
        warnings.warn(msg, MemoryWarning)
        logger.warning(msg)
        
    return report
