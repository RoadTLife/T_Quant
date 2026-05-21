import yaml
import os

class Config:
    def __init__(self, config_file='config.yaml'):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        return self._get_default_config()
    
    def _get_default_config(self):
        return {
            'data': {
                'data_dir': 'data/raw',
                'processed_dir': 'data/processed'
            },
            'backtest': {
                'initial_capital': 100000.0,
                'commission': 0.001
            },
            'trading': {
                'api_key': '',
                'api_secret': '',
                'mode': 'backtest'
            },
            'logging': {
                'level': 'INFO',
                'log_dir': 'logs'
            }
        }
    
    def get(self, key, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k)
            if value is None:
                return default
        return value
    
    def set(self, key, value):
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def save(self):
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)