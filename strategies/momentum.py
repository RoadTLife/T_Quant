import pandas as pd
from .base import BaseStrategy

class MomentumStrategy(BaseStrategy):
    def __init__(self, period=12):
        super().__init__()
        self.period = period
        self.previous_roc = None
    
    def on_bar(self, data):
        if len(data) < self.period + 1:
            return
        
        current_price = data['close'].iloc[-1]
        past_price = data['close'].iloc[-self.period - 1]
        roc = (current_price - past_price) / past_price
        
        if self.previous_roc is not None:
            if roc > 0 and self.previous_roc <= 0 and not self._has_position():
                self.buy()
            elif roc < 0 and self.previous_roc >= 0 and self._has_position():
                self.sell()
        
        self.previous_roc = roc
    
    def _has_position(self):
        if self.broker:
            return self.broker.get_position() > 0
        return False