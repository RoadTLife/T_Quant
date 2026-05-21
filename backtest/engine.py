import pandas as pd
from .analyzer import Analyzer

class BackTestEngine:
    def __init__(self):
        self.data = None
        self.strategy = None
        self.broker = None
        self.results = None
    
    def set_data(self, data):
        self.data = data
    
    def set_strategy(self, strategy):
        self.strategy = strategy
    
    def set_broker(self, broker):
        self.broker = broker
        if self.strategy:
            self.strategy.set_broker(broker)
    
    def run(self, start_date=None, end_date=None):
        if self.data is None or self.strategy is None:
            raise ValueError("Data and strategy must be set before running")
        
        filtered_data = self.data.copy()
        if start_date:
            filtered_data = filtered_data[filtered_data.index >= start_date]
        if end_date:
            filtered_data = filtered_data[filtered_data.index <= end_date]
        
        self.broker.reset()
        
        for i in range(len(filtered_data)):
            current_data = filtered_data.iloc[:i+1]
            current_date = filtered_data.index[i]
            current_price = filtered_data['close'].iloc[i]
            
            self.broker.set_price(current_price)
            self.strategy.set_data(current_data)
            self.strategy.on_bar(current_data)
            
            self.broker.update_portfolio(current_date)
        
        self.results = self._generate_results()
        return self.results
    
    def _generate_results(self):
        portfolio_value = pd.DataFrame({
            'date': self.broker.portfolio_history['date'],
            'value': self.broker.portfolio_history['value']
        })
        portfolio_value.set_index('date', inplace=True)
        
        return {
            'portfolio_value': portfolio_value,
            'trades': self.broker.trades,
            'signals': self.strategy.get_signals()
        }
    
    def analyze(self):
        if self.results is None:
            raise ValueError("Run backtest first before analyzing")
        
        analyzer = Analyzer(self.results)
        return analyzer.get_report()