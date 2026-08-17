import pandas as pd
import gc

def aggregate_geolocation(geo_df: pd.DataFrame) -> pd.DataFrame:
    """
    Groups geolocation data by zip_code_prefix to reduce the rows from 1M to ~19k,
    preventing Out-Of-Memory issues when joining with other tables.
    """
    print("Aggregating geolocation data...")
    initial_rows = len(geo_df)
    
    # Perform aggregation
    agg_df = geo_df.groupby('geolocation_zip_code_prefix').agg({
        'geolocation_lat': 'mean',
        'geolocation_lng': 'mean',
        'geolocation_city': 'first',
        'geolocation_state': 'first'
    }).reset_index()
    
    final_rows = len(agg_df)
    print(f"Geolocation aggregated: {initial_rows} rows -> {final_rows} rows.")
    
    # Cast coordinate types to float32 to save space
    agg_df['geolocation_lat'] = agg_df['geolocation_lat'].astype('float32')
    agg_df['geolocation_lng'] = agg_df['geolocation_lng'].astype('float32')
    
    # Cast state/city to category or category types as well
    agg_df['geolocation_state'] = agg_df['geolocation_state'].astype('category')
    
    gc.collect()
    return agg_df
