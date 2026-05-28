import yaml
import os
from typing import Dict, Any, Optional

class ConfigLoader:
    """配置文件加载器，支持YAML格式配置文件"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._config = None
        return cls._instance
    
    def _load_config(self, config_path: str = None):
        """加载配置文件"""
        if self._config is not None:
            return
        
        if config_path is None:
            # 尝试多个可能的路径
            possible_paths = [
                '/home/devops/code/quant/config/backtest_config.yaml',
                './config/backtest_config.yaml',
                '../config/backtest_config.yaml'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break
        
        if config_path is None:
            # 如果没有找到配置文件，使用默认配置
            self._config = self._get_default_config()
            print("⚠️  未找到配置文件，使用默认配置")
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            print(f"✓ 已加载配置文件: {config_path}")
        except Exception as e:
            print(f"✗ 加载配置文件失败: {e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'backtest': {
                'initial_capital': 100000.0,
                'lot_size': 100,
                'commission_rate': 0.0003,
                'min_trade_amount': 0.0
            },
            'macd': {
                'short_period': 12,
                'long_period': 26,
                'signal_period': 9
            },
            'paths': {
                'data_dir': './data',
                'output_dir': './outputs',
                'log_dir': './logs'
            }
        }
    
    def get_config(self, key: str = None, config_path: str = None) -> Any:
        """
        获取配置
        
        参数:
            key: 配置键，如 'backtest.lot_size'，不传则返回全部配置
            config_path: 配置文件路径，可选
        
        返回:
            配置值或配置字典
        """
        self._load_config(config_path)
        
        if key is None:
            return self._config
        
        # 支持点分隔的键路径
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            print(f"⚠️  配置键 '{key}' 不存在")
            return None
    
    def get_backtest_config(self) -> Dict[str, Any]:
        """获取回测配置"""
        return self.get_config('backtest')
    
    def get_macd_config(self) -> Dict[str, Any]:
        """获取MACD配置"""
        return self.get_config('macd')
    
    def get_paths_config(self) -> Dict[str, Any]:
        """获取路径配置"""
        return self.get_config('paths')

# 全局实例
config_loader = ConfigLoader()

# 便捷函数
def get_config(key: str = None) -> Any:
    """快捷函数：获取配置"""
    return config_loader.get_config(key)

def get_backtest_config() -> Dict[str, Any]:
    """快捷函数：获取回测配置"""
    return config_loader.get_backtest_config()

def get_macd_config() -> Dict[str, Any]:
    """快捷函数：获取MACD配置"""
    return config_loader.get_macd_config()