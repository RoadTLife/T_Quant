import pandas as pd
import os
from .datasources import DataSourceFactory

class DataFetcher:
    def __init__(self, data_dir='data/raw', default_source='akshare'):
        self.data_dir = data_dir
        self.default_source = default_source
        self.source = None
    
    def set_source(self, source_name):
        """设置当前数据源"""
        self.source = DataSourceFactory.create_source(source_name)
        self.source.initialize()
    
    def get_source(self):
        """获取当前数据源"""
        if self.source is None:
            self.set_source(self.default_source)
        return self.source
    
    def fetch_from_csv(self, filename):
        """从CSV文件读取数据"""
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        df = pd.read_csv(filepath)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        return df
    
    def save_to_csv(self, df, filename):
        """保存数据到CSV文件"""
        filepath = os.path.join(self.data_dir, filename)
        df.to_csv(filepath)
    
    def get_stock_list(self, market='A', source_name=None):
        """
        获取股票列表
        
        Args:
            market: 市场类型 ('A' for A股, 'HK' for 港股, 'US' for 美股)
            source_name: 数据源名称，默认为默认数据源
        
        Returns:
            DataFrame: 股票列表数据
        """
        source = self._get_source(source_name)
        return source.get_stock_list(market)
    
    def get_daily_data(self, symbol, start_date, end_date, adjust='qfq', source_name=None):
        """
        获取日线数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            adjust: 复权类型 ('qfq' for 前复权, 'hfq' for 后复权, None for 不复权)
            source_name: 数据源名称，默认为默认数据源
        
        Returns:
            DataFrame: 日线数据
        """
        source = self._get_source(source_name)
        return source.get_daily_data(symbol, start_date, end_date, adjust)
    
    def get_minute_data(self, symbol, start_date, end_date, freq='1min', source_name=None):
        """
        获取分钟级数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            freq: 频率 ('1min', '5min', '15min', '30min', '60min')
            source_name: 数据源名称，默认为默认数据源
        
        Returns:
            DataFrame: 分钟级数据
        """
        source = self._get_source(source_name)
        return source.get_minute_data(symbol, start_date, end_date, freq)
    
    def get_index_data(self, index_symbol, start_date, end_date, source_name=None):
        """
        获取指数数据
        
        Args:
            index_symbol: 指数代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            source_name: 数据源名称，默认为默认数据源
        
        Returns:
            DataFrame: 指数数据
        """
        source = self._get_source(source_name)
        return source.get_index_data(index_symbol, start_date, end_date)
    
    def get_wencai_data(self, query, page=1, per_page=100, source_name=None):
        """
        通过同花顺问财获取数据
        
        Args:
            query: 问财查询语句 (中文)
            page: 页码
            per_page: 每页条数
            source_name: 数据源名称，默认为默认数据源
        
        Returns:
            DataFrame: 查询结果
        """
        source = self._get_source(source_name)
        if hasattr(source, 'get_wencai_data'):
            return source.get_wencai_data(query, page, per_page)
        raise NotImplementedError(f"数据源 {source.get_name()} 不支持问财查询")
    
    def _get_source(self, source_name):
        """获取指定的数据源，如未指定则使用默认数据源"""
        if source_name is not None:
            source = DataSourceFactory.create_source(source_name)
            source.initialize()
            return source
        return self.get_source()
    
    def get_available_sources(self):
        """获取所有可用的数据源"""
        return DataSourceFactory.get_available_sources()