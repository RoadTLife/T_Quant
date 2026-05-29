import pandas as pd
from datetime import datetime
from .base import BaseStrategy

class JoinQuantStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.current_date = None
        self.portfolio = {}
    
    def initialize(self):
        pass
    
    def handle_data(self, data):
        self.on_bar(data)
    
    def before_trading_start(self):
        pass
    
    def get_price(self, security, start_date=None, end_date=None, frequency='daily', 
                  fields=None, adjust_type='pre', skip_paused=False, fq='pre'):
        if self.data is None:
            return pd.DataFrame()
        
        if start_date is None:
            start_date = self.data.index[0]
        if end_date is None:
            end_date = self.data.index[-1]
        
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        mask = (self.data.index >= start_date) & (self.data.index <= end_date)
        filtered = self.data.loc[mask]
        
        if fields is not None:
            if isinstance(fields, list):
                filtered = filtered[fields]
            else:
                filtered = filtered[[fields]]
        
        return filtered
    
    def get_current_data(self):
        if self.data is not None and len(self.data) > 0:
            return self.data.iloc[-1]
        return None
    
    def order(self, security, amount, style=None):
        if amount > 0:
            self.buy(quantity=amount)
        elif amount < 0:
            self.sell(quantity=-amount)
    
    def order_target(self, security, target_amount):
        current_pos = self.get_position(security)
        delta = target_amount - current_pos
        self.order(security, delta)
    
    def order_value(self, security, value):
        current_data = self.get_current_data()
        if current_data is not None and 'close' in current_data:
            price = current_data['close']
            amount = int(value / price)
            self.order(security, amount)
    
    def order_target_value(self, security, target_value):
        current_data = self.get_current_data()
        if current_data is not None and 'close' in current_data:
            price = current_data['close']
            current_pos = self.get_position(security)
            current_value = current_pos * price
            delta_value = target_value - current_value
            amount = int(delta_value / price)
            self.order(security, amount)
    
    def get_position(self, security=None):
        if self.broker:
            return self.broker.get_position()
        return 0
    
    def get_portfolio(self):
        return self.portfolio
    
    def get_account(self):
        if self.broker:
            return {
                'total_assets': self.broker.get_total_assets(),
                'cash': self.broker.get_cash(),
                'positions': self.broker.get_positions()
            }
        return {}
    
    def log(self, message, level='INFO'):
        print(f"[{level}] {message}")


class JQSimpleMA(JoinQuantStrategy):
    def __init__(self, short_window=5, long_window=20):
        super().__init__()
        self.short_window = short_window
        self.long_window = long_window
    
    def initialize(self):
        self.log("策略初始化完成")
    
    def on_bar(self, data):
        if len(data) < self.long_window:
            return
        
        short_ma = data['close'].rolling(window=self.short_window).mean().iloc[-1]
        long_ma = data['close'].rolling(window=self.long_window).mean().iloc[-1]
        
        if short_ma > long_ma and not self._has_position():
            self.log(f"金叉信号，买入")
            self.buy()
        elif short_ma < long_ma and self._has_position():
            self.log(f"死叉信号，卖出")
            self.sell()
    
    def _has_position(self):
        return self.get_position() > 0


class JQBreakout(JoinQuantStrategy):
    def __init__(self, window=20):
        super().__init__()
        self.window = window
        self.previous_high = None
    
    def initialize(self):
        self.log("突破策略初始化完成")
    
    def on_bar(self, data):
        if len(data) < self.window:
            return
        
        current_high = data['high'].iloc[-1]
        window_high = data['high'].rolling(window=self.window).max().iloc[-2]
        
        if current_high > window_high and not self._has_position():
            self.log(f"突破新高，买入")
            self.buy()
        elif self._has_position():
            current_close = data['close'].iloc[-1]
            stop_loss = data['close'].rolling(window=self.window).mean().iloc[-1] * 0.95
            if current_close < stop_loss:
                self.log(f"止损卖出")
                self.sell()
    
    def _has_position(self):
        return self.get_position() > 0


class JQRSI(JoinQuantStrategy):
    def __init__(self, period=14, overbought=70, oversold=30):
        super().__init__()
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def initialize(self):
        self.log("RSI策略初始化完成")
    
    def on_bar(self, data):
        if len(data) < self.period + 1:
            return
        
        deltas = data['close'].diff()
        gains = deltas.where(deltas > 0, 0)
        losses = -deltas.where(deltas < 0, 0)
        
        avg_gain = gains.rolling(window=self.period).mean().iloc[-1]
        avg_loss = losses.rolling(window=self.period).mean().iloc[-1]
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        if rsi < self.oversold and not self._has_position():
            self.log(f"RSI超卖，买入 (RSI: {rsi:.2f})")
            self.buy()
        elif rsi > self.overbought and self._has_position():
            self.log(f"RSI超买，卖出 (RSI: {rsi:.2f})")
            self.sell()
    
    def _has_position(self):
        return self.get_position() > 0