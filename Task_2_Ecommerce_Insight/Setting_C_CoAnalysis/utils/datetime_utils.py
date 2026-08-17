import pandas as pd

def parse_date(val):
    """
    Parse timestamp string into pandas Timestamp.
    """
    if pd.isna(val):
        return pd.NaT
    try:
        return pd.to_datetime(val)
    except Exception:
        return pd.NaT

def normalize_to_date(val):
    """
    Normalize string or timestamp to datetime.date.
    """
    parsed = parse_date(val)
    if pd.isna(parsed):
        return None
    return parsed.date()

def calculate_days_between(start_date, end_date):
    """
    Calculate days between two dates.
    """
    if pd.isna(start_date) or pd.isna(end_date):
        return None
    return (end_date - start_date).days
