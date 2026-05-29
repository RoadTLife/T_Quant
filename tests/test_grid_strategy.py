import pandas as pd
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config_loader import get_backtest_config
from src.utils.stock_code_finder import get_stock_name_by_code
from src.utils.backtest_utils import backtest_grid, GridStrategy
from src.utils.plot_utils import plot_grid_strategy_results


def main():
    backtest_config = get_backtest_config()
    
    initial_capital = backtest_config.get('initial_capital', 1000000)
    lot_size = backtest_config.get('lot_size', 100)
    commission_rate = backtest_config.get('commission_rate', 0.0003)
    
    # 自定义网格参数（根据2023年贵州茅台价格范围调整）
    # 2023年价格范围：1475.33 ~ 1744.53，平均价：1614.88
    CENTER_PRICE = 1600
    BUY_GRID_PRICES = [1575, 1550, 1525, 1500]
    SELL_GRID_PRICES = [1625, 1650, 1675, 1700]
    LOWER_LIMIT = 1475
    UPPER_LIMIT = 1750
    
    params = {
        'initial_capital': initial_capital
    }
    
    print(f"网格交易策略回测配置参数：")
    print(f"  初始资金: {initial_capital:,.2f} 元")
    print(f"  最小交易单位: {lot_size} 股")
    print(f"  手续费率: {commission_rate*10000:.2f}‰")
    print(f"  中心价格: {CENTER_PRICE}")
    print(f"  买入网格: {BUY_GRID_PRICES}")
    print(f"  卖出网格: {SELL_GRID_PRICES}")
    print()
    
    data_path = '/home/devops/code/quant/data/csv/baostock_2023-01-01_2023-12-31_all.csv'
    print(f"正在读取股票数据: {data_path}")
    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['date'])
    
    test_stocks = ['sh.600519']
    
    results = {}
    
    for symbol in test_stocks:
        stock_name = get_stock_name_by_code(symbol) or symbol
        print(f"\n正在测试股票: {symbol} ({stock_name})")
        
        stock_data = df[df['symbol'] == symbol].copy()
        stock_data = stock_data.sort_values('date').set_index('date')
        
        if len(stock_data) < 30:
            print(f"  数据不足，跳过")
            continue
        
        # 使用自定义网格参数进行回测
        result = backtest_grid(
            data=stock_data,
            initial_capital=initial_capital,
            lot_size=lot_size,
            commission_rate=commission_rate,
            center_price=CENTER_PRICE,
            buy_grid_prices=BUY_GRID_PRICES,
            sell_grid_prices=SELL_GRID_PRICES
        )
        
        results[symbol] = result
        
        print(f"  最终资金: {result['final_capital']:,.2f}")
        print(f"  总收益率: {result['total_return']*100:.2f}%")
        print(f"  最大回撤: {result['max_drawdown']*100:.2f}%")
        print(f"  交易次数: {result['trade_count']}")
        print(f"    买入次数: {result['buy_count']}")
        print(f"    卖出次数: {result['sell_count']}")
        print(f"  累计手续费: {result['total_commission']:,.2f} 元")
        print(f"  胜率: {result['win_rate']*100:.2f}%")
        
        if result['trade_count'] > 0:
            nav_series = pd.Series(result['equity_curve'], index=stock_data.index)
            close_prices = stock_data['close'].values
            date_index = stock_data.index
            trades = result['trades']
            
            plot_grid_strategy_results(
                date_index=date_index,
                close_prices=close_prices,
                nav_series=nav_series,
                trades=trades,
                stock_name=stock_name,
                stock_code=symbol,
                center_price=CENTER_PRICE,
                buy_grid_prices=BUY_GRID_PRICES,
                sell_grid_prices=SELL_GRID_PRICES,
                lower_limit=LOWER_LIMIT,
                upper_limit=UPPER_LIMIT
            )
    
    print("\n" + "="*125)
    print("{:^125}".format("网格交易策略测试汇总"))
    print("="*125)
    print(f"{'股票代码':<12} {'股票名称':<10} {'最终资金':>14} {'收益率':>10} {'最大回撤':>10} {'交易次数':>8} {'买入次数':>8} {'卖出次数':>8} {'累计手续费':>12} {'胜率':>8}")
    print("-"*125)
    for symbol, result in results.items():
        stock_name = get_stock_name_by_code(symbol) or symbol
        print(f"{symbol:<12} {stock_name:<10} {result['final_capital']:>14,.2f} {result['total_return']*100:>10.2f}% {result['max_drawdown']*100:>10.2f}% {result['trade_count']:>8} {result['buy_count']:>8} {result['sell_count']:>8} {result['total_commission']:>12,.2f} {result['win_rate']*100:>8.2f}%")


if __name__ == '__main__':
    main()