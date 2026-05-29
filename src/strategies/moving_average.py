import pandas as pd
from .base import BaseStrategy

class MovingAverageStrategy(BaseStrategy):
    def __init__(self, short_window=50, long_window=200):
        super().__init__()
        self.short_window = short_window
        self.long_window = long_window
    
    def on_bar(self, data):
        if len(data) < self.long_window:
            return
        
        short_ma = data['close'].rolling(window=self.short_window).mean().iloc[-1]
        long_ma = data['close'].rolling(window=self.long_window).mean().iloc[-1]
        
        if short_ma > long_ma and not self._has_position():
            self.buy()
        elif short_ma < long_ma and self._has_position():
            self.sell()
    
    def _has_position(self):
        if self.broker:
            return self.broker.get_position() > 0
        return False