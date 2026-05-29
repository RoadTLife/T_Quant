import pandas as pd
import numpy as np


def calculate_macd(data, short_period=12, long_period=26, signal_period=9):
    """计算MACD指标"""
    result = data.copy()
    
    result['ema_short'] = result['close'].ewm(span=short_period, adjust=False).mean()
    result['ema_long'] = result['close'].ewm(span=long_period, adjust=False).mean()
    result['macd'] = result['ema_short'] - result['ema_long']
    result['signal_line'] = result['macd'].ewm(span=signal_period, adjust=False).mean()
    result['histogram'] = result['macd'] - result['signal_line']
    
    return result


def generate_macd_signals(data):
    """根据MACD生成交易信号"""
    result = data.copy()
    result['signal'] = 0
    
    result.loc[(result['macd'].shift(1) < result['signal_line'].shift(1)) & (result['macd'] > result['signal_line']), 'signal'] = 1
    result.loc[(result['macd'].shift(1) > result['signal_line'].shift(1)) & (result['macd'] < result['signal_line']), 'signal'] = -1
    
    return result


def calculate_max_drawdown(nav_series):
    """计算最大回撤"""
    running_max = nav_series.cummax()
    drawdown = (nav_series / running_max) - 1.0
    max_drawdown = drawdown.min()
    
    return max_drawdown


def backtest_macd(data, initial_capital=100000, lot_size=100, commission_rate=0.0003):
    """回测MACD策略"""
    capital = initial_capital
    position = 0
    equity_curve = []
    trade_count = 0
    win_count = 0
    total_commission = 0.0
    trades = []
    entry_price = 0.0
    
    for idx, row in data.iterrows():
        if row['signal'] == 1 and position == 0:
            available_cash = capital / (1 + commission_rate)
            max_shares = int(available_cash / row['close'] / lot_size) * lot_size
            
            if max_shares >= lot_size:
                buy_amount = max_shares * row['close']
                commission = buy_amount * commission_rate
                total_cost = buy_amount + commission
                
                if total_cost <= capital:
                    position = max_shares
                    capital -= total_cost
                    entry_price = row['close']
                    trade_count += 1
                    total_commission += commission
                    
                    trades.append({
                        'date': idx,
                        'action': '买入',
                        'price': row['close'],
                        'shares': max_shares,
                        'amount': buy_amount,
                        'commission': commission,
                        'cash': capital,
                        'position': position * row['close'] / (capital + position * row['close'])
                    })
        
        elif row['signal'] == -1 and position > 0:
            sell_amount = position * row['close']
            commission = sell_amount * commission_rate
            net_proceeds = sell_amount - commission
            
            if row['close'] > entry_price:
                win_count += 1
            
            trades.append({
                'date': idx,
                'action': '卖出',
                'price': row['close'],
                'shares': position,
                'amount': sell_amount,
                'commission': commission,
                'cash': capital + net_proceeds,
                'position': 0.0
            })
            
            capital += net_proceeds
            total_commission += commission
            trade_count += 1
            position = 0
        
        total_assets = capital + position * row['close']
        equity_curve.append(total_assets)
    
    data['equity_curve'] = equity_curve
    
    final_capital = capital + position * data['close'].iloc[-1]
    total_return = (final_capital - initial_capital) / initial_capital
    win_rate = win_count / trade_count if trade_count > 0 else 0
    max_drawdown = calculate_max_drawdown(pd.Series(equity_curve))
    
    return {
        'final_capital': final_capital,
        'total_return': total_return,
        'trade_count': trade_count,
        'win_rate': win_rate,
        'total_commission': total_commission,
        'max_drawdown': max_drawdown,
        'equity_curve': equity_curve,
        'trades': trades
    }


class GridStrategy:
    """
    层级网格交易策略类
    
    核心逻辑：
    - 使用"持仓层级"概念控制网格触发
    - 每买入一次层级+1，每卖出一次层级-1
    - 当前层级决定了哪些网格可以触发
    
    例如：买入网格[1450, 1400, 1350, 1300]，卖出网格[1550, 1600, 1650, 1700]
    - 层级0：可触发1450买入，不能卖出
    - 层级1：可触发1400买入，可触发1550卖出
    - 层级2：可触发1350买入，可触发1600卖出
    - 层级3：可触发1300买入，可触发1650卖出
    - 层级4：不能再买，可触发1700卖出
    """
    def __init__(self, center_price, grid_shares, 
                 buy_grid_prices, sell_grid_prices,
                 init_cash, init_shares, commission_rate):
        self.center_price = center_price
        self.grid_shares = grid_shares
        self.commission_rate = commission_rate
        
        self.cash = init_cash
        self.shares = init_shares
        
        self.buy_grid_prices = sorted(buy_grid_prices, reverse=True)
        self.sell_grid_prices = sorted(sell_grid_prices)
        
        self.position_level = init_shares // grid_shares if grid_shares > 0 else 0
        self.trades = []
    
    def get_nav(self, current_price):
        """计算当前净值"""
        return self.cash + self.shares * current_price
    
    def execute(self, date, current_price, prev_price):
        """
        执行网格交易逻辑
        参数:
            date: 当前日期
            current_price: 当前价格
            prev_price: 前一日价格（用于判断穿越方向）
        返回:
            trade: 交易记录，如果没有交易则返回None
        """
        if prev_price is None:
            return None
        
        trade = None
        
        # 检查买入网格
        if self.position_level < len(self.buy_grid_prices):
            target_buy_price = self.buy_grid_prices[self.position_level]
            
            if prev_price > target_buy_price >= current_price:
                exec_price = target_buy_price
                buy_amount = self.grid_shares * exec_price
                commission = buy_amount * self.commission_rate
                total_cost = buy_amount + commission
                
                if self.cash >= total_cost:
                    self.cash -= total_cost
                    self.shares += self.grid_shares
                    self.position_level += 1
                    
                    trade = {
                        'date': date,
                        'action': '买入',
                        'grid_price': target_buy_price,
                        'exec_price': exec_price,
                        'shares': self.grid_shares,
                        'amount': buy_amount,
                        'commission': commission,
                        'cash': self.cash,
                        'total_shares': self.shares,
                        'position_level': self.position_level,
                        'nav': self.get_nav(current_price)
                    }
                    self.trades.append(trade)
        
        # 检查卖出网格
        if trade is None and self.position_level > 0:
            sell_index = self.position_level - 1
            if sell_index < len(self.sell_grid_prices):
                target_sell_price = self.sell_grid_prices[sell_index]
                
                if prev_price < target_sell_price <= current_price:
                    if self.shares >= self.grid_shares:
                        exec_price = target_sell_price
                        sell_amount = self.grid_shares * exec_price
                        commission = sell_amount * self.commission_rate
                        net_proceeds = sell_amount - commission
                        
                        self.cash += net_proceeds
                        self.shares -= self.grid_shares
                        self.position_level -= 1
                        
                        trade = {
                            'date': date,
                            'action': '卖出',
                            'grid_price': target_sell_price,
                            'exec_price': exec_price,
                            'shares': self.grid_shares,
                            'amount': sell_amount,
                            'commission': commission,
                            'cash': self.cash,
                            'total_shares': self.shares,
                            'position_level': self.position_level,
                            'nav': self.get_nav(current_price)
                        }
                        self.trades.append(trade)
        
        return trade


def calculate_grid_levels(data, grid_count=5, grid_range=0.1):
    """
    计算网格交易的网格水平
    参数:
        data: 包含close列的DataFrame
        grid_count: 网格数量
        grid_range: 网格总范围（百分比）
    返回:
        网格水平列表（从低到高）
    """
    close_mean = data['close'].mean()
    grid_spacing = close_mean * grid_range / grid_count
    
    grid_levels = [close_mean - (grid_count // 2) * grid_spacing + i * grid_spacing 
                   for i in range(grid_count + 1)]
    
    return grid_levels


def backtest_grid(data, initial_capital=100000, lot_size=100, commission_rate=0.0003, 
                  center_price=None, buy_grid_prices=None, sell_grid_prices=None,
                  grid_count=5, grid_range=0.1):
    """
    回测网格交易策略（支持自定义网格或自动计算）
    
    参数:
        data: 包含close列的DataFrame
        initial_capital: 初始资金
        lot_size: 每次交易股数
        commission_rate: 手续费率
        center_price: 中心价格（可选，自动计算时为None）
        buy_grid_prices: 买入网格价格列表（可选）
        sell_grid_prices: 卖出网格价格列表（可选）
        grid_count: 网格数量（自动计算时使用）
        grid_range: 网格总范围（自动计算时使用）
    """
    # 如果没有提供自定义网格，自动计算
    if center_price is None or buy_grid_prices is None or sell_grid_prices is None:
        close_mean = data['close'].mean()
        center_price = center_price or close_mean
        grid_spacing = close_mean * grid_range / grid_count
        
        buy_grid_prices = [center_price - i * grid_spacing for i in range(1, grid_count // 2 + 1)]
        sell_grid_prices = [center_price + i * grid_spacing for i in range(1, grid_count // 2 + 1)]
    
    strategy = GridStrategy(
        center_price=center_price,
        grid_shares=lot_size,
        buy_grid_prices=buy_grid_prices,
        sell_grid_prices=sell_grid_prices,
        init_cash=initial_capital,
        init_shares=0,
        commission_rate=commission_rate
    )
    
    close_prices = data['close'].values
    dates = data.index
    
    nav_list = []
    first_price = close_prices[0]
    nav_list.append(strategy.get_nav(first_price))
    
    for i in range(1, len(close_prices)):
        current_price = close_prices[i]
        prev_price = close_prices[i-1]
        current_date = dates[i]
        
        strategy.execute(current_date, current_price, prev_price)
        nav_list.append(strategy.get_nav(current_price))
    
    final_capital = strategy.get_nav(close_prices[-1])
    total_return = (final_capital - initial_capital) / initial_capital
    trades = strategy.trades
    
    buy_trades = [t for t in trades if t['action'] == '买入']
    sell_trades = [t for t in trades if t['action'] == '卖出']
    win_count = sum(1 for t in sell_trades if t['exec_price'] > buy_trades[i]['exec_price'] 
                    for i in range(len(buy_trades)) if buy_trades[i]['date'] < t['date'])
    
    win_rate = len(sell_trades) / len(buy_trades) if buy_trades else 0
    total_commission = sum(t['commission'] for t in trades)
    max_drawdown = calculate_max_drawdown(pd.Series(nav_list))
    
    return {
        'final_capital': final_capital,
        'total_return': total_return,
        'trade_count': len(trades),
        'buy_count': len(buy_trades),
        'sell_count': len(sell_trades),
        'win_rate': win_rate,
        'total_commission': total_commission,
        'max_drawdown': max_drawdown,
        'equity_curve': nav_list,
        'trades': trades,
        'center_price': center_price,
        'buy_grid_prices': sorted(buy_grid_prices, reverse=True),
        'sell_grid_prices': sorted(sell_grid_prices)
    }