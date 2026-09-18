import os
from pathlib import Path

ENV_VAR = "LINEARTV_CONFIG_DIR"
DEFAULT_DIR_NAME = ".lineartvstream"

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