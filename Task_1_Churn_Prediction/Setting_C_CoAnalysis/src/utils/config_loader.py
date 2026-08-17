import os
from src.utils.file_io import load_yaml

def get_config(config_path=None):
    if config_path is None:
        # Resolve path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.abspath(os.path.join(current_dir, "..", "..", "pipelines", "config.yaml"))
    return load_yaml(config_path)
