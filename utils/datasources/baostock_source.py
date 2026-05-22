import pandas as pd
import logging
from .base import BaseDataSource

logger = logging.getLogger(__name__)

class BaostockDataSource(BaseDataSource):
    def __init__(self):
        super().__init__('baostock')
        self.bs = None
    
    def initialize(self):
        try:
            import baostock as bs
            self.bs = bs
            lg = self.bs.login()
            if lg.error_code == '0':
                self.initialized = True
                logger.info("Baostock登录成功")
            else:
                logger.error(f"Baostock登录失败: {lg.error_msg}")
                raise ConnectionError(f"Baostock登录失败: {lg.error_msg}")
        except ImportError as e:
            logger.error(f"Baostock导入失败: {e}")
            raise ImportError("请先安装Baostock: pip install baostock")
    
    def get_stock_list(self, market='A'):
        if not self.initialized:
            self.initialize()
        
        try:
            if market == 'A':
                rs = self.bs.query_stock_basic()
            elif market == 'HK':
                rs = self.bs.query_hk_stock_basic()
            else:
                raise ValueError(f"不支持的市场类型: {market}")
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return pd.DataFrame()
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            df['data_source'] = self.name
            
            rename_map = {
                'code': 'symbol',
                'code_name': 'name',
                'industry': 'industry',
                'listDate': 'listed_date',
                'list_date': 'listed_date'
            }
            
            for old_name, new_name in rename_map.items():
                if old_name in df.columns:
                    df.rename(columns={old_name: new_name}, inplace=True)
            
            result_cols = ['symbol', 'name', 'data_source']
            if 'industry' in df.columns:
                result_cols.append('industry')
            else:
                df['industry'] = ''
                result_cols.append('industry')
            if 'listed_date' in df.columns:
                result_cols.append('listed_date')
            else:
                df['listed_date'] = ''
                result_cols.append('listed_date')
            
            return df[result_cols]
        
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def _is_convertible_bond(self, symbol):
        """判断是否为可转债"""
        symbol = str(symbol).lower()
        # 可转债代码特征
        convertible_patterns = [
            'sh.110', 'sh.113',  # 上海可转债
            'sz.127', 'sz.128'   # 深圳可转债
        ]
        for pattern in convertible_patterns:
            if symbol.startswith(pattern):
                return True
        return False
    
    def get_daily_data(self, symbol, start_date, end_date, adjust='qfq'):
        if not self.initialized:
            self.initialize()
        
        try:
            if self._is_convertible_bond(symbol):
                logger.warning(f"跳过可转债 {symbol}，Baostock 不支持可转债数据")
                return pd.DataFrame()
            
            symbol_clean = self._clean_symbol(symbol)
            adjust_flag = self._get_adjust_flag(adjust)
            
            rs = self.bs.query_history_k_data_plus(
                symbol_clean,
                "date,open,high,low,close,volume,amount",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag=adjust_flag
            )
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return pd.DataFrame()
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
            df[numeric_cols] = df[numeric_cols].replace('', None)
            df[numeric_cols] = df[numeric_cols].astype(float)
            
            df['data_source'] = self.name
            df['symbol'] = symbol
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df
        
        except Exception as e:
            logger.error(f"获取日线数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def get_minute_data(self, symbol, start_date, end_date, freq='1min'):
        if not self.initialized:
            self.initialize()
        
        try:
            symbol_clean = self._clean_symbol(symbol)
            
            freq_map = {
                '1min': '1',
                '5min': '5',
                '15min': '15',
                '30min': '30',
                '60min': '60'
            }
            
            if freq not in freq_map:
                raise ValueError(f"不支持的频率: {freq}")
            
            rs = self.bs.query_history_k_data_plus(
                symbol_clean,
                "date,time,open,high,low,close,volume,amount",
                start_date=start_date,
                end_date=end_date,
                frequency=freq_map[freq]
            )
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return pd.DataFrame()
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
            df[numeric_cols] = df[numeric_cols].replace('', None)
            df[numeric_cols] = df[numeric_cols].astype(float)
            
            df['data_source'] = self.name
            df['symbol'] = symbol
            df['freq'] = freq
            
            return df
        
        except Exception as e:
            logger.error(f"获取分钟数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def get_index_data(self, index_symbol, start_date, end_date):
        if not self.initialized:
            self.initialize()
        
        try:
            symbol_clean = self._clean_symbol(index_symbol)
            
            rs = self.bs.query_history_k_data_plus(
                symbol_clean,
                "date,open,high,low,close,volume,amount",
                start_date=start_date,
                end_date=end_date,
                frequency="d"
            )
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return pd.DataFrame()
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
            df[numeric_cols] = df[numeric_cols].replace('', None)
            df[numeric_cols] = df[numeric_cols].astype(float)
            
            df['data_source'] = self.name
            df['index_symbol'] = index_symbol
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df
        
        except Exception as e:
            logger.error(f"获取指数数据失败 {index_symbol}: {e}")
            return pd.DataFrame()
    
    def _clean_symbol(self, symbol):
        symbol = str(symbol).strip()
        if '.' not in symbol:
            if symbol.startswith('6'):
                return f"{symbol}.SH"
            elif symbol.startswith('0') or symbol.startswith('3'):
                return f"{symbol}.SZ"
        return symbol
    
    def _get_adjust_flag(self, adjust):
        adjust_flag_map = {
            None: '3',
            '': '3',
            'none': '3',
            'qfq': '2',
            'hfq': '1'
        }
        return adjust_flag_map.get(adjust.lower(), '3')
    
    def logout(self):
        if self.initialized:
            self.bs.logout()
            self.initialized = False
            logger.info("Baostock已登出")