import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config_loader import get_backtest_config, get_macd_config
from src.utils.stock_code_finder import get_stock_name_by_code
from src.utils.backtest_utils import calculate_macd, generate_macd_signals, backtest_macd
from src.utils.plot_utils import plot_strategy_results


def main():
    backtest_config = get_backtest_config()
    macd_config = get_macd_config()
    
    initial_capital = backtest_config.get('initial_capital', 100000)
    lot_size = backtest_config.get('lot_size', 100)
    commission_rate = backtest_config.get('commission_rate', 0.0003)
    
    short_period = macd_config.get('short_period', 12)
    long_period = macd_config.get('long_period', 26)
    signal_period = macd_config.get('signal_period', 9)
    
    params = {
        'initial_capital': initial_capital,
        'short_period': short_period,
        'long_period': long_period,
        'signal_period': signal_period
    }
    
    print(f"回测配置参数：")
    print(f"  初始资金: {initial_capital:.2f} 元")
    print(f"  最小交易单位: {lot_size} 股")
    print(f"  手续费率: {commission_rate*10000:.2f}‰")
    print(f"  MACD参数: 快线={short_period}, 慢线={long_period}, 信号线={signal_period}")
    print()
    
    data_path = '/home/devops/code/quant/data/csv/baostock_2023-01-01_2023-12-31_all.csv'
    print(f"正在读取股票数据: {data_path}")
    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['date'])
    
    test_stocks = ['sh.600519', 'sz.000858', 'sh.601318', 'sz.000001']
    
    results = {}
    
    for symbol in test_stocks:
        stock_name = get_stock_name_by_code(symbol) or symbol
        print(f"\n正在测试股票: {symbol} ({stock_name})")
        
        stock_data = df[df['symbol'] == symbol].copy()
        stock_data = stock_data.sort_values('date').set_index('date')
        
        if len(stock_data) < 30:
            print(f"  数据不足，跳过")
            continue
        
        stock_data = calculate_macd(stock_data, short_period, long_period, signal_period)
        stock_data = generate_macd_signals(stock_data)
        result = backtest_macd(stock_data, initial_capital, lot_size, commission_rate)
        
        results[symbol] = result
        
        print(f"  最终资金: {result['final_capital']:.2f}")
        print(f"  总收益率: {result['total_return']*100:.2f}%")
        print(f"  最大回撤: {result['max_drawdown']*100:.2f}%")
        print(f"  交易次数: {result['trade_count']}")
        print(f"  累计手续费: {result['total_commission']:.2f} 元")
        print(f"  胜率: {result['win_rate']*100:.2f}%")
        
        if result['trade_count'] > 0:
            nav_series = result['equity_curve']
            close_prices = stock_data['close'].values
            date_index = stock_data.index
            trades = result['trades']
            
            plot_strategy_results(date_index, close_prices, nav_series, stock_data, trades, stock_name, symbol, params)
    
    print("\n" + "="*125)
    print("{:^125}".format("MACD策略测试汇总"))
    print("="*125)
    print(f"{'股票代码':<12} {'股票名称':<10} {'最终资金':>14} {'收益率':>10} {'最大回撤':>10} {'交易次数':>8} {'累计手续费':>12} {'胜率':>8}")
    print("-"*125)
    for symbol, result in results.items():
        stock_name = get_stock_name_by_code(symbol) or symbol
        print(f"{symbol:<12} {stock_name:<10} {result['final_capital']:>14.2f} {result['total_return']*100:>10.2f}% {result['max_drawdown']*100:>10.2f}% {result['trade_count']:>8} {result['total_commission']:>12.2f} {result['win_rate']*100:>8.2f}%")


if __name__ == '__main__':
    main()