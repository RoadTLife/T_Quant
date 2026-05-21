from strategies.moving_average import MovingAverageStrategy
from backtest.engine import BackTestEngine
from trading.broker import Broker
from utils.data_fetcher import DataFetcher

def main():
    print("Starting Quant Trading Framework...")
    
    fetcher = DataFetcher()
    data = fetcher.generate_sample_data(days=500)
    
    strategy = MovingAverageStrategy(short_window=50, long_window=200)
    broker = Broker(initial_capital=100000)
    engine = BackTestEngine()
    
    engine.set_data(data)
    engine.set_strategy(strategy)
    engine.set_broker(broker)
    
    results = engine.run()
    report = engine.analyze()
    
    print("\nBacktest Report:")
    print(f"Total Return: {report['total_return']:.2%}")
    print(f"Annualized Return: {report['annualized_return']:.2%}")
    print(f"Max Drawdown: {report['max_drawdown']:.2%}")
    print(f"Sharpe Ratio: {report['sharpe_ratio']:.2f}")
    print(f"Win Rate: {report['win_rate']:.2%}")
    print(f"Profit Factor: {report['profit_factor']:.2f}")
    print(f"Total Trades: {report['total_trades']}")

if __name__ == '__main__':
    main()