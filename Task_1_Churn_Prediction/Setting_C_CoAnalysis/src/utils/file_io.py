import os
import json
import yaml
import pickle
import pandas as pd

def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_yaml(data, file_path):
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path, indent=4):
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)

def save_pickle(obj, file_path):
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, 'wb') as f:
        pickle.dump(obj, f)

def load_pickle(file_path):
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def save_dataframe(df, file_path, index=False):
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    if file_path.endswith('.csv'):
        df.to_csv(file_path, index=index, encoding='utf-8')
    elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df.to_excel(file_path, index=index)
    elif file_path.endswith('.parquet'):
        df.to_parquet(file_path, index=index)
    else:
        raise ValueError(f"Unsupported file format for dataframe: {file_path}")
