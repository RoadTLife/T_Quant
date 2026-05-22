from .base import BaseDataSource
from .baostock_source import BaostockDataSource

class DataSourceFactory:
    """数据源工厂类，用于创建和管理不同的数据源"""
    
    _sources = {
        'baostock': BaostockDataSource
    }
    
    @classmethod
    def create_source(cls, source_name):
        """创建数据源实例"""
        if source_name not in cls._sources:
            raise ValueError(f"不支持的数据源: {source_name}")
        
        source_class = cls._sources[source_name]
        return source_class()
    
    @classmethod
    def register_source(cls, name, source_class):
        """注册新的数据源"""
        if not issubclass(source_class, BaseDataSource):
            raise ValueError("数据源类必须继承自BaseDataSource")
        
        cls._sources[name] = source_class
        print(f"数据源 '{name}' 已注册")
    
    @classmethod
    def get_available_sources(cls):
        """获取所有可用的数据源名称"""
        return list(cls._sources.keys())

__all__ = ['BaseDataSource', 'BaostockDataSource', 'DataSourceFactory']