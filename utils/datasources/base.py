from abc import ABC, abstractmethod
import pandas as pd

class BaseDataSource(ABC):
    """数据源基类，定义统一的接口"""
    
    def __init__(self, name):
        self.name = name
        self.initialized = False
    
    @abstractmethod
    def initialize(self):
        """初始化数据源"""
        pass
    
    @abstractmethod
    def get_stock_list(self, market='A'):
        """
        获取股票列表
        
        Args:
            market: 市场类型 ('A' for A股, 'HK' for 港股, 'US' for 美股)
        
        Returns:
            DataFrame: 股票列表数据
        """
        pass
    
    @abstractmethod
    def get_daily_data(self, symbol, start_date, end_date, adjust='qfq'):
        """
        获取日线数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            adjust: 复权类型 ('qfq' for 前复权, 'hfq' for 后复权, None for 不复权)
        
        Returns:
            DataFrame: 日线数据
        """
        pass
    
    @abstractmethod
    def get_minute_data(self, symbol, start_date, end_date, freq='1min'):
        """
        获取分钟级数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            freq: 频率 ('1min', '5min', '15min', '30min', '60min')
        
        Returns:
            DataFrame: 分钟级数据
        """
        pass
    
    @abstractmethod
    def get_index_data(self, index_symbol, start_date, end_date):
        """
        获取指数数据
        
        Args:
            index_symbol: 指数代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        
        Returns:
            DataFrame: 指数数据
        """
        pass
    
    def get_name(self):
        """获取数据源名称"""
        return self.name
    
    def is_initialized(self):
        """检查数据源是否已初始化"""
        return self.initialized