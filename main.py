from src.strategies.moving_average import MovingAverageStrategy
from src.backtest.engine import BackTestEngine
from src.trading.broker import Broker
from src.utils.data_manager import DataManager
from src.utils.cli_utils import print_title, print_error, print_info
import pandas as pd
import os

def main(symbol=None):
    """
    主回测函数
    
    Args:
        symbol: 股票代码（可选，默认使用数据库中第一只股票）
    """
    print_title("量化交易回测系统")
    
    dm = DataManager()
    
    if symbol:
        print_info(f"使用指定股票: {symbol}")
    else:
        symbol = os.environ.get('BACKTEST_SYMBOL')
    
    if not symbol:
        stocks = dm.list_downloaded_stocks()
        if stocks.empty:
            print_error("数据库中没有股票数据")
            print_info("请先添加股票并下载数据:")
            print_info("  python quant.py add 600519 --name='贵州茅台'")
            print_info("  python quant.py download 600519 2023-01-01 2023-12-31")
            return
        
        print_info(f"已找到 {len(stocks)} 只股票")
        print_info("使用第一只股票进行回测...")
        symbol = stocks.iloc[0]['symbol']
    
    print(f"\n股票代码: {symbol}")
    
    conn = dm._connect()
    query = f"SELECT * FROM daily_data WHERE symbol = '{symbol}' ORDER BY date"
    data = pd.read_sql(query, conn)
    conn.close()
    
    if data.empty:
        print_error(f"股票 {symbol} 没有日线数据")
        return
    
    data['date'] = pd.to_datetime(data['date'])
    data.set_index('date', inplace=True)
    
    print_info(f"数据周期: {data.index.min().date()} ~ {data.index.max().date()}")
    print_info(f"数据条数: {len(data)}")
    
    strategy = MovingAverageStrategy(short_window=50, long_window=200)
    broker = Broker(initial_capital=100000)
    engine = BackTestEngine()
    
    engine.set_data(data)
    engine.set_strategy(strategy)
    engine.set_broker(broker)
    
    print_info("\n开始回测...")
    results = engine.run()
    report = engine.analyze()
    
    print("\n" + "=" * 60)
    print("回测报告")
    print("=" * 60)
    print(f"股票代码: {symbol}")
    print(f"数据周期: {data.index.min().date()} ~ {data.index.max().date()}")
    print(f"数据条数: {len(data)}")
    print("\n性能指标:")
    print(f"  总收益率: {report['total_return']:.2%}")
    print(f"  年化收益率: {report['annualized_return']:.2%}")
    print(f"  最大回撤: {report['max_drawdown']:.2%}")
    print(f"  Sharpe比率: {report['sharpe_ratio']:.2f}")
    print(f"  胜率: {report['win_rate']:.2%}")
    print(f"  盈利因子: {report['profit_factor']:.2f}")
    print(f"  交易次数: {report['total_trades']}")

if __name__ == '__main__':
    main()