from .market_data import MarketDataCollector
from .financial_data import FinancialDataCollector
from .macro_data import MacroDataCollector
from .news_events import NewsEventsCollector
from .research_reports import ResearchReportsCollector
from .calendar_data import CalendarDataCollector
from .catalysts import CatalystsCollector

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