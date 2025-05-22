import os
from typing import Dict, Any
import yaml

from src.exceptions import ConfigNotFoundError, ConfigParseError

EXAMPLE_CONFIG_FILE = 'config.example.yaml'


def load_config(config_file: str) -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(config_file):
        if os.path.exists(EXAMPLE_CONFIG_FILE):
            print(
                "An example configuration file "
                f"'{EXAMPLE_CONFIG_FILE}' exists.")
            print(
                f"You can copy or rename it to '{config_file}' "
                "and modify it with your settings.")
        raise ConfigNotFoundError("Error: Configuration file "
                                  f"'{config_file}' not found.")

    try:
        with open(config_file, 'r') as f:
            config: Dict[str, Any] = yaml.safe_load(f) or {}
        return config.get('servers', {})
    except yaml.YAMLError as e:
        raise ConfigParseError(f"Error parsing '{config_file}': {e}")
