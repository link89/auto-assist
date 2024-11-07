from .lib import USER_HOME

import json
import os

config_file = os.path.join(USER_HOME, '.auto_assist.json')
missing = object()

def load(config_file=config_file):
    """
    Load the config from file
    """
    if not os.path.exists(config_file):
        return {}
    with open(config_file) as f:
        return json.load(f)

def save(config, config_file=config_file):
    """
    Save the config to file
    """
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

def set(key, value=None, config_file=config_file):
    """
    Set a config value
    """
    config = load(config_file=config_file)
    if value is None:
        del config[key]
    else:
        config[key] = value
    save(config)

def get(key, default=missing, config_file=config_file):
    """
    Get a config value
    """
    if default is missing:
        return load(config_file=config_file)[key]
    else:
        return load(config_file=config_file).get(key, default)


class ConfigCmd:

    def __init__(self, config_file=config_file):
        self._config_file = config_file

    def set(self, key, value=None):
        """
        Set a config value
        """
        set(key, value, config_file=self._config_file)
