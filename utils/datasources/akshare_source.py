import pandas as pd
import logging
from .base import BaseDataSource

logger = logging.getLogger(__name__)

class AKShareDataSource(BaseDataSource):
    """基于AKShare的数据源实现"""
    
    def __init__(self):
        super().__init__('akshare')
        self.ak = None
    
    def initialize(self):
        """初始化AKShare"""
        try:
            import akshare as ak
            self.ak = ak
            self.initialized = True
            logger.info("AKShare数据源初始化成功")
        except ImportError as e:
            logger.error(f"AKShare导入失败: {e}")
            raise ImportError("请先安装AKShare: pip install akshare")
    
    def get_stock_list(self, market='A'):
        """
        获取股票列表
        
        Args:
            market: 市场类型 ('A' for A股, 'HK' for 港股, 'US' for 美股)
        
        Returns:
            DataFrame: 股票列表数据
        """
        if not self.initialized:
            self.initialize()
        
        try:
            if market == 'A':
                df = self.ak.stock_zh_a_spot_em()
            elif market == 'HK':
                df = self.ak.stock_hk_spot_em()
            elif market == 'US':
                df = self.ak.stock_us_spot_em()
            else:
                raise ValueError(f"不支持的市场类型: {market}")
            
            df['data_source'] = self.name
            return df
        
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_daily_data(self, symbol, start_date, end_date, adjust='qfq'):
        """
        获取日线数据
        
        Args:
            symbol: 股票代码 (如 '600519' 或 '600519.SH')
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            adjust: 复权类型 ('qfq' for 前复权, 'hfq' for 后复权, None for 不复权)
        
        Returns:
            DataFrame: 日线数据
        """
        if not self.initialized:
            self.initialize()
        
        try:
            symbol_clean = self._clean_symbol(symbol)
            
            df = self.ak.stock_zh_a_hist(
                symbol=symbol_clean,
                period='daily',
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                adjust=adjust if adjust else ''
            )
            
            df['data_source'] = self.name
            df['symbol'] = symbol
            df['adjust_type'] = adjust
            
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            })
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df
        
        except Exception as e:
            logger.error(f"获取日线数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
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
        if not self.initialized:
            self.initialize()
        
        try:
            symbol_clean = self._clean_symbol(symbol)
            
            df = self.ak.stock_zh_a_hist_min_em(
                symbol=symbol_clean,
                period=freq,
                start_date=start_date,
                end_date=end_date
            )
            
            df['data_source'] = self.name
            df['symbol'] = symbol
            df['freq'] = freq
            
            return df
        
        except Exception as e:
            logger.error(f"获取分钟数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def get_index_data(self, index_symbol, start_date, end_date):
        """
        获取指数数据
        
        Args:
            index_symbol: 指数代码 (如 '000001' 或 '000001.SH')
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        
        Returns:
            DataFrame: 指数数据
        """
        if not self.initialized:
            self.initialize()
        
        try:
            symbol_clean = self._clean_symbol(index_symbol)
            
            df = self.ak.stock_zh_index_daily_em(
                symbol=symbol_clean,
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', '')
            )
            
            df['data_source'] = self.name
            df['index_symbol'] = index_symbol
            
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume'
            })
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df
        
        except Exception as e:
            logger.error(f"获取指数数据失败 {index_symbol}: {e}")
            return pd.DataFrame()
    
    def get_wencai_data(self, query, page=1, per_page=100):
        """
        通过同花顺问财获取数据
        
        Args:
            query: 问财查询语句 (中文)
            page: 页码
            per_page: 每页条数
        
        Returns:
            DataFrame: 查询结果
        """
        if not self.initialized:
            self.initialize()
        
        try:
            df = self.ak.stock_zh_a_wencai(
                query=query,
                page=page,
                per_page=per_page
            )
            
            df['data_source'] = self.name
            df['query'] = query
            
            return df
        
        except AttributeError:
            logger.warning("当前AKShare版本不支持问财接口")
            return self._fallback_wencai(query, page, per_page)
        except Exception as e:
            logger.error(f"问财查询失败 '{query}': {e}")
            return pd.DataFrame()
    
    def _fallback_wencai(self, query, page, per_page):
        """备用问财查询方法"""
        logger.info(f"使用备用方法查询: {query}")
        return pd.DataFrame()
    
    def _clean_symbol(self, symbol):
        """清理股票代码，移除交易所后缀"""
        if '.' in symbol:
            return symbol.split('.')[0]
        return symbol