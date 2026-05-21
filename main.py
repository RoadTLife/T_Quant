from strategies.moving_average import MovingAverageStrategy
from backtest.engine import BackTestEngine
from trading.broker import Broker
from utils.data_manager import DataManager
import pandas as pd

def main():
    print("Starting Quant Trading Framework...")
    
    dm = DataManager()
    
    stocks = dm.list_downloaded_stocks()
    if stocks.empty:
        print("警告: 数据库中没有股票数据，请先通过 data_cli.py 或 data_manager_gui.py 添加股票并下载数据")
        print("示例:")
        print("  python data_cli.py add 600519 --name='贵州茅台'")
        print("  python data_cli.py download 600519 2023-01-01 2023-12-31")
        return
    
    print(f"已找到 {len(stocks)} 只股票")
    print("使用第一只股票进行回测...")
    
    symbol = stocks.iloc[0]['symbol']
    print(f"股票代码: {symbol}")
    
    conn = dm._connect()
    query = f"SELECT * FROM daily_data WHERE symbol = '{symbol}' ORDER BY date"
    data = pd.read_sql(query, conn)
    conn.close()
    
    if data.empty:
        print(f"警告: 股票 {symbol} 没有日线数据")
        return
    
    data['date'] = pd.to_datetime(data['date'])
    data.set_index('date', inplace=True)
    
    strategy = MovingAverageStrategy(short_window=50, long_window=200)
    broker = Broker(initial_capital=100000)
    engine = BackTestEngine()
    
    engine.set_data(data)
    engine.set_strategy(strategy)
    engine.set_broker(broker)
    
    results = engine.run()
    report = engine.analyze()
    
    print("\nBacktest Report:")
    print(f"股票代码: {symbol}")
    print(f"数据周期: {data.index.min().date()} ~ {data.index.max().date()}")
    print(f"数据条数: {len(data)}")
    print(f"\nPerformance Metrics:")
    print(f"Total Return: {report['total_return']:.2%}")
    print(f"Annualized Return: {report['annualized_return']:.2%}")
    print(f"Max Drawdown: {report['max_drawdown']:.2%}")
    print(f"Sharpe Ratio: {report['sharpe_ratio']:.2f}")
    print(f"Win Rate: {report['win_rate']:.2%}")
    print(f"Profit Factor: {report['profit_factor']:.2f}")
    print(f"Total Trades: {report['total_trades']}")

if __name__ == '__main__':
    main()