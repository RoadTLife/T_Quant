import pandas as pd
import numpy as np

class Analyzer:
    def __init__(self, results):
        self.results = results
        self.portfolio_value = results['portfolio_value']
        self.trades = results['trades']
    
    def get_report(self):
        report = {
            'total_return': self._calculate_total_return(),
            'annualized_return': self._calculate_annualized_return(),
            'max_drawdown': self._calculate_max_drawdown(),
            'sharpe_ratio': self._calculate_sharpe_ratio(),
            'win_rate': self._calculate_win_rate(),
            'profit_factor': self._calculate_profit_factor(),
            'total_trades': len(self.trades)
        }
        return report
    
    def _calculate_total_return(self):
        initial = self.portfolio_value['value'].iloc[0]
        final = self.portfolio_value['value'].iloc[-1]
        return (final - initial) / initial
    
    def _calculate_annualized_return(self):
        total_return = self._calculate_total_return()
        days = (self.portfolio_value.index[-1] - self.portfolio_value.index[0]).days
        years = days / 365.25
        if years <= 0:
            return 0
        return (1 + total_return) ** (1 / years) - 1
    
    def _calculate_max_drawdown(self):
        values = self.portfolio_value['value']
        peak = values.cummax()
        drawdown = (values - peak) / peak
        return drawdown.min()
    
    def _calculate_sharpe_ratio(self):
        daily_returns = self.portfolio_value['value'].pct_change().dropna()
        if len(daily_returns) == 0:
            return 0
        risk_free_rate = 0.02
        excess_returns = daily_returns - risk_free_rate / 252
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)
    
    def _calculate_win_rate(self):
        if not self.trades:
            return 0
        winning_trades = sum(1 for trade in self.trades if trade['profit'] > 0)
        return winning_trades / len(self.trades)
    
    def _calculate_profit_factor(self):
        if not self.trades:
            return 0
        gross_profit = sum(trade['profit'] for trade in self.trades if trade['profit'] > 0)
        gross_loss = abs(sum(trade['profit'] for trade in self.trades if trade['profit'] < 0))
        if gross_loss == 0:
            return float('inf')
        return gross_profit / gross_loss