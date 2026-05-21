import pytest
import pandas as pd
import numpy as np
from backtest.engine import BackTestEngine
from backtest.analyzer import Analyzer
from strategies.moving_average import MovingAverageStrategy
from trading.broker import Broker

class TestBackTestEngine:
    def test_run_with_data(self):
        engine = BackTestEngine()
        strategy = MovingAverageStrategy()
        broker = Broker(initial_capital=100000)
        
        data = pd.DataFrame({
            'open': 100 + np.cumsum(np.random.randn(300) * 0.5),
            'high': 100 + np.cumsum(np.random.randn(300) * 0.5) + 1,
            'low': 100 + np.cumsum(np.random.randn(300) * 0.5) - 1,
            'close': 100 + np.cumsum(np.random.randn(300) * 0.5),
            'volume': np.random.randint(1000, 10000, 300)
        }, index=pd.date_range('2023-01-01', periods=300))
        
        engine.set_data(data)
        engine.set_strategy(strategy)
        engine.set_broker(broker)
        
        results = engine.run()
        assert 'portfolio_value' in results
        assert 'trades' in results
        assert 'signals' in results

class TestAnalyzer:
    def test_calculate_total_return(self):
        portfolio_value = pd.DataFrame({
            'value': [100000, 110000, 105000, 120000]
        }, index=pd.date_range('2023-01-01', periods=4))
        
        results = {
            'portfolio_value': portfolio_value,
            'trades': []
        }
        
        analyzer = Analyzer(results)
        report = analyzer.get_report()
        assert report['total_return'] == 0.2