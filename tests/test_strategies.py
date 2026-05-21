import pytest
import pandas as pd
import numpy as np
from strategies.moving_average import MovingAverageStrategy
from strategies.momentum import MomentumStrategy

class TestMovingAverageStrategy:
    def test_init(self):
        strategy = MovingAverageStrategy(short_window=50, long_window=200)
        assert strategy.short_window == 50
        assert strategy.long_window == 200
    
    def test_on_bar_no_signal_short_data(self):
        strategy = MovingAverageStrategy()
        data = pd.DataFrame({'close': np.random.rand(100)}, index=pd.date_range('2023-01-01', periods=100))
        strategy.on_bar(data)
        assert len(strategy.get_signals()) == 0

class TestMomentumStrategy:
    def test_init(self):
        strategy = MomentumStrategy(period=12)
        assert strategy.period == 12
    
    def test_on_bar_no_signal_short_data(self):
        strategy = MomentumStrategy()
        data = pd.DataFrame({'close': np.random.rand(10)}, index=pd.date_range('2023-01-01', periods=10))
        strategy.on_bar(data)
        assert len(strategy.get_signals()) == 0