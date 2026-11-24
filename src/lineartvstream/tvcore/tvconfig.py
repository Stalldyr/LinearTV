import os
from pathlib import Path
import json
from datetime import date

ENV_VAR = "LINEARTV_CONFIG_DIR"
DEFAULT_DIR_NAME = ".lineartvstream"
CONFIG_FILENAME = "config.json"

def default_dict():
    base_dir = str(get_config_dir())

    return {   
        "language": "en",
        "schedule": {
            "broadcast_start": "04:00",
            "broadcast_end": "04:00",
            "years_back": 25,
            "weeks": 0,
        },
        "paths": {
            "logs": base_dir + "/logs",
            "media": base_dir + "/tvfiles",
            "database": base_dir + "/data"
        },
        "sync": {
            "frequency": 1,
            "download_buffer": 3,
            "verify_buffer": 3,
            "overlap_minutes": 3,
            "delete_overlaps": False
        },
        "refresh":{
            "frequency": 7,
            "buffer_weeks": 4,
            "missing": False
        },
        "video":{
            "quality": 480
        },
        "logging": True
    }

def get_config_dir() -> Path:
    """
    Returns the directory where LinearTV stores its config, database
    and downloaded media. Resolved in this order:

    1. The LINEARTV_CONFIG_DIR environment variable, if set.
    2. Otherwise, ~/.lineartvstream/

    The directory is created if it doesn't already exist.
    """
    env_value = os.getenv(ENV_VAR)

    if env_value:
        config_dir = Path(env_value).expanduser()
    else:
        config_dir = Path.home() / DEFAULT_DIR_NAME

    config_dir.mkdir(parents=True, exist_ok=True)

    return config_dir


def deep_merge(defaults: dict, overrides: dict) -> dict:
    result = {}

    for key, default_value in defaults.items():
        if key in overrides:
            user_value = overrides[key]
            if isinstance(default_value, dict) and isinstance(user_value, dict):
                result[key] = deep_merge(default_value, user_value)
            else:
                result[key] = user_value
        else:
            result[key] = default_value

    for key, value in overrides.items():
        if key not in defaults:
            result[key] = value

    return result

def get_config_dict():
    path = get_config_dir() / CONFIG_FILENAME
    defaults = default_dict()

    if not path.exists():
        path.write_text(json.dumps(defaults, indent=4), encoding="utf-8")
        return defaults

    with open(path, "r", encoding="utf-8") as f:
        user_config = json.load(f)

    return deep_merge(defaults, user_config)