from .datetime_normalizer import normalize_timestamps
from .delivery_metrics import calculate_delivery_metrics

def prepare_orders_clean(orders_raw_df):
    normalized = normalize_timestamps(orders_raw_df)
    return calculate_delivery_metrics(normalized)
