import pandas as pd
import os
import re
from typing import List, Dict, Optional

class StockCodeFinder:
    """股票代码查询工具，通过股票名称获取股票代码"""
    
    _instance = None
    _stock_data = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StockCodeFinder, cls).__new__(cls)
            cls._stock_data = None
        return cls._instance
    
    def _load_stock_list(self):
        """加载股票列表数据"""
        if self._stock_data is not None:
            return
        
        # 尝试多个可能的路径
        possible_paths = [
            '/home/devops/code/quant/data/basic/stock_list.csv',
            './data/basic/stock_list.csv',
            '../data/basic/stock_list.csv'
        ]
        
        stock_list_path = None
        for path in possible_paths:
            if os.path.exists(path):
                stock_list_path = path
                break
        
        if stock_list_path is None:
            raise FileNotFoundError("未找到股票列表文件 stock_list.csv")
        
        try:
            self._stock_data = pd.read_csv(stock_list_path)
            # 确保symbol和name列存在
            if 'symbol' not in self._stock_data.columns or 'name' not in self._stock_data.columns:
                raise ValueError("股票列表文件格式不正确，缺少 symbol 或 name 列")
            print(f"[OK] 已加载 {len(self._stock_data)} 条股票数据")
        except Exception as e:
            print(f"[FAIL] 加载股票列表失败: {e}")
            raise
    
    def get_code_by_name(self, stock_name: str, exact_match: bool = False) -> Optional[str]:
        """
        根据股票名称获取股票代码
        
        参数:
            stock_name: 股票名称（如 "贵州茅台"）
            exact_match: 是否精确匹配（默认False，支持模糊匹配）
        
        返回:
            股票代码（如 "sh.600519"），未找到返回None
        """
        self._load_stock_list()
        
        if exact_match:
            # 精确匹配
            result = self._stock_data[self._stock_data['name'] == stock_name]
        else:
            # 模糊匹配
            result = self._stock_data[self._stock_data['name'].str.contains(stock_name, na=False)]
        
        if len(result) == 0:
            return None
        elif len(result) == 1:
            return result['symbol'].iloc[0]
        else:
            # 多个匹配结果，返回第一个
            return result['symbol'].iloc[0]
    
    def search_stocks(self, keyword: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        搜索股票，返回匹配的股票列表
        
        参数:
            keyword: 搜索关键词（股票名称或代码）
            limit: 返回结果数量限制（默认10）
        
        返回:
            匹配的股票列表，每个元素包含 'symbol' 和 'name'
        """
        self._load_stock_list()
        
        # 先尝试按名称搜索
        name_result = self._stock_data[self._stock_data['name'].str.contains(keyword, na=False)]
        
        # 如果名称搜索结果少，再尝试按代码搜索
        if len(name_result) < limit:
            code_result = self._stock_data[self._stock_data['symbol'].str.contains(keyword, na=False)]
            # 合并结果并去重
            combined = pd.concat([name_result, code_result]).drop_duplicates(subset='symbol')
        else:
            combined = name_result
        
        # 限制返回数量
        combined = combined.head(limit)
        
        return [
            {'symbol': row['symbol'], 'name': row['name']}
            for _, row in combined.iterrows()
        ]
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, str]]:
        """
        根据股票代码获取股票详细信息
        
        参数:
            symbol: 股票代码（如 "sh.600519"）
        
        返回:
            股票信息字典，包含 symbol, name, industry, listed_date，未找到返回None
        """
        self._load_stock_list()
        
        result = self._stock_data[self._stock_data['symbol'] == symbol]
        
        if len(result) == 0:
            return None
        
        row = result.iloc[0]
        return {
            'symbol': row['symbol'],
            'name': row['name'],
            'industry': row.get('industry', ''),
            'listed_date': row.get('listed_date', '')
        }
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """
        验证股票代码是否有效
        
        参数:
            symbol: 股票代码（如 "sh.600519"）
        
        返回:
            True 如果代码有效，False 否则
        """
        self._load_stock_list()
        return symbol in self._stock_data['symbol'].values

# 全局实例
stock_code_finder = StockCodeFinder()

# 便捷函数
def get_stock_code(stock_name: str, exact_match: bool = False) -> Optional[str]:
    """快捷函数：根据股票名称获取股票代码"""
    return stock_code_finder.get_code_by_name(stock_name, exact_match)

def search_stock(keyword: str, limit: int = 10) -> List[Dict[str, str]]:
    """快捷函数：搜索股票"""
    return stock_code_finder.search_stocks(keyword, limit)

def get_stock_info_by_code(symbol: str) -> Optional[Dict[str, str]]:
    """快捷函数：根据股票代码获取信息"""
    return stock_code_finder.get_stock_info(symbol)

def get_stock_name_by_code(symbol: str) -> Optional[str]:
    """
    快捷函数：根据股票代码获取股票名称
    
    参数:
        symbol: 股票代码（如 "sh.600519"）
    
    返回:
        股票名称（如 "贵州茅台"），未找到返回None
    """
    info = stock_code_finder.get_stock_info(symbol)
    return info['name'] if info else None