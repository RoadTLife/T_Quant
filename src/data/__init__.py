# -*- coding: utf-8 -*-
"""
数据采集模块

注意：
- market_data 和 financial_data 需要安装 MiniQMT (xtquant)
- 其他模块只需要 AkShare
"""

# 延迟导入，避免启动时加载所有依赖
def get_market_data_collector():
    """获取行情数据采集器（需要 xtquant）"""
    try:
        from .market_data import MarketDataCollector
        return MarketDataCollector
    except ImportError as e:
        raise ImportError("market_data 需要安装 MiniQMT (xtquant)") from e

def get_financial_data_collector():
    """获取财务数据采集器（需要 xtquant）"""
    try:
        from .financial_data import FinancialDataCollector
        return FinancialDataCollector
    except ImportError as e:
        raise ImportError("financial_data 需要安装 MiniQMT (xtquant)") from e

def get_macro_data_collector():
    """获取宏观数据采集器"""
    from .macro_data import MacroDataCollector
    return MacroDataCollector

def get_news_events_collector():
    """获取新闻事件采集器"""
    from .news_events import NewsEventsCollector
    return NewsEventsCollector

def get_research_reports_collector():
    """获取研报数据采集器"""
    from .research_reports import ResearchReportsCollector
    return ResearchReportsCollector

def get_calendar_data_collector():
    """获取财经日历采集器"""
    from .calendar_data import CalendarDataCollector
    return CalendarDataCollector

def get_catalysts_collector():
    """获取催化剂数据采集器"""
    from .catalysts import CatalystsCollector
    return CatalystsCollector

def get_market_sentiment_collector():
    """获取市场情绪数据采集器"""
    from .market_sentiment import MarketSentimentCollector
    return MarketSentimentCollector

def get_data_manager():
    """获取数据管理器"""
    from .data_manager import DataManager
    return DataManager

__all__ = [
    'get_market_data_collector',
    'get_financial_data_collector',
    'get_macro_data_collector',
    'get_news_events_collector',
    'get_research_reports_collector',
    'get_calendar_data_collector',
    'get_catalysts_collector',
    'get_market_sentiment_collector',
    'get_data_manager'
]