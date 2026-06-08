import yaml
import os
from typing import Dict, Any, Optional

class ConfigError(Exception):
    """配置错误异常"""
    pass

class ConfigLoader:
    """配置文件加载器，支持YAML格式配置文件"""
    
    _instance = None
    _config = None
    _main_config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._config = None
            cls._main_config = None
        return cls._instance
    
    def _load_main_config(self, config_path: str = None):
        """加载主配置文件 config.yaml"""
        if self._main_config is not None:
            return
        
        if config_path is None:
            possible_paths = [
                '/home/devops/code/quant/config.yaml',
                './config.yaml',
                '../config.yaml',
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break
        
        if config_path is None:
            raise ConfigError("未找到主配置文件 config.yaml")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._main_config = yaml.safe_load(f)
            print(f"[OK] 已加载主配置文件: {config_path}")
        except Exception as e:
            raise ConfigError(f"加载主配置文件失败: {e}")
    
    def _load_config(self, config_path: str = None):
        """加载回测配置文件"""
        if self._config is not None:
            return
        
        if config_path is None:
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
            raise ConfigError("未找到回测配置文件")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            print(f"[OK] 已加载回测配置文件: {config_path}")
        except Exception as e:
            raise ConfigError(f"加载回测配置文件失败: {e}")
    
    def get_main_config(self, key: str = None) -> Any:
        """
        获取主配置（从 config.yaml）
        
        参数:
            key: 配置键，如 'database.host'，不传则返回全部配置
        
        返回:
            配置值或配置字典
        
        异常:
            ConfigError: 配置文件不存在或配置键不存在
        """
        self._load_main_config()
        
        if key is None:
            return self._main_config
        
        keys = key.split('.')
        value = self._main_config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError) as e:
            raise ConfigError(f"主配置键 '{key}' 不存在") from e
    
    def get_config(self, key: str = None, config_path: str = None) -> Any:
        """
        获取回测配置
        
        参数:
            key: 配置键，如 'backtest.lot_size'，不传则返回全部配置
            config_path: 配置文件路径，可选
        
        返回:
            配置值或配置字典
        
        异常:
            ConfigError: 配置文件不存在或配置键不存在
        """
        self._load_config(config_path)
        
        if key is None:
            return self._config
        
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError as e:
            raise ConfigError(f"配置键 '{key}' 不存在") from e
    
    def get_backtest_config(self) -> Dict[str, Any]:
        """获取回测配置"""
        try:
            return self.get_config('backtest')
        except ConfigError:
            return self.get_main_config('backtest')
    
    def get_macd_config(self) -> Dict[str, Any]:
        """获取MACD配置"""
        try:
            return self.get_config('macd')
        except ConfigError:
            return self.get_main_config('macd')
    
    def get_paths_config(self) -> Dict[str, Any]:
        """获取路径配置"""
        try:
            return self.get_config('paths')
        except ConfigError:
            return self.get_main_config('paths')
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self.get_main_config('database')

config_loader = ConfigLoader()

def get_config(key: str = None) -> Any:
    """快捷函数：获取回测配置"""
    return config_loader.get_config(key)

def get_main_config(key: str = None) -> Any:
    """快捷函数：获取主配置"""
    return config_loader.get_main_config(key)

def get_backtest_config() -> Dict[str, Any]:
    """快捷函数：获取回测配置"""
    return config_loader.get_backtest_config()

def get_macd_config() -> Dict[str, Any]:
    """快捷函数：获取MACD配置"""
    return config_loader.get_macd_config()

def get_database_config() -> Dict[str, Any]:
    """快捷函数：获取数据库配置"""
    return config_loader.get_database_config()