import pandas as pd
import logging
from .base import BaseDataSource

logger = logging.getLogger(__name__)

class AKShareBondDataSource(BaseDataSource):
    """基于 AKShare 的可转债数据源实现"""
    
    def __init__(self):
        super().__init__('akshare_bond')
        self.ak = None
    
    def initialize(self):
        """初始化 AKShare"""
        try:
            import akshare as ak
            self.ak = ak
            self.initialized = True
            logger.info("AKShare 可转债数据源初始化成功")
        except ImportError as e:
            logger.error(f"AKShare 导入失败: {e}")
            raise ImportError("请先安装 AKShare: pip install akshare")
    
    def get_bond_list(self):
        """获取可转债列表"""
        if not self.initialized:
            self.initialize()
        
        try:
            df = self.ak.bond_cov_comparison()
            
            df['data_source'] = self.name
            df = df.rename(columns={
                '转债代码': 'symbol',
                '转债名称': 'name'
            })
            
            return df[['symbol', 'name', 'data_source']]
        
        except Exception as e:
            logger.error(f"获取可转债列表失败: {e}")
            return pd.DataFrame()
    
    def get_bond_daily_data(self, symbol, start_date, end_date):
        """获取可转债日线数据"""
        if not self.initialized:
            self.initialize()
        
        try:
            symbol_clean = self._clean_symbol(symbol)
            
            df = self.ak.bond_zh_hs_cov_spot()
            
            df = df[df['code'] == symbol_clean]
            
            if df.empty:
                logger.warning(f"未找到可转债 {symbol} 的实时行情数据")
                return pd.DataFrame()
            
            df = df[['trade', 'high', 'low', 'open', 'volume', 'amount']]
            
            df.columns = ['close', 'high', 'low', 'open', 'volume', 'amount']
            
            df['date'] = pd.Timestamp.now().strftime('%Y-%m-%d')
            df['data_source'] = self.name
            df['symbol'] = symbol
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
            df[numeric_cols] = df[numeric_cols].replace('', None)
            df[numeric_cols] = df[numeric_cols].astype(float)
            
            return df
        
        except Exception as e:
            logger.error(f"获取可转债数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def get_daily_data(self, symbol, start_date, end_date, adjust='qfq'):
        """获取日线数据（兼容接口）"""
        return self.get_bond_daily_data(symbol, start_date, end_date)
    
    def get_stock_list(self, market='A'):
        """获取股票列表（兼容接口，返回可转债列表）"""
        return self.get_bond_list()
    
    def get_minute_data(self, symbol, start_date, end_date, freq='1min'):
        """获取分钟级数据（可转债不支持，返回空DataFrame）"""
        logger.warning(f"可转债不支持分钟级数据: {symbol}")
        return pd.DataFrame()
    
    def get_index_data(self, index_symbol, start_date, end_date):
        """获取指数数据（可转债数据源不支持，返回空DataFrame）"""
        logger.warning(f"可转债数据源不支持指数数据: {index_symbol}")
        return pd.DataFrame()
    
    def _clean_symbol(self, symbol):
        """清理可转债代码"""
        symbol = str(symbol).strip()
        if symbol.startswith('sh.'):
            return symbol.replace('sh.', '')
        elif symbol.startswith('sz.'):
            return symbol.replace('sz.', '')
        return symbol
