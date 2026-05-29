import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os


def plot_grid_strategy_results(date_index, close_prices, nav_series, trades, stock_name, stock_code,
                               center_price, buy_grid_prices, sell_grid_prices, lower_limit, upper_limit):
    """
    绘制网格策略回测结果图表
    参数:
        date_index: 日期索引
        close_prices: 收盘价序列
        nav_series: 净值序列（pandas Series）
        trades: 交易记录列表
        stock_name: 股票名称
        stock_code: 股票代码
        center_price: 中心价格
        buy_grid_prices: 买入网格价格列表
        sell_grid_prices: 卖出网格价格列表
        lower_limit: 最低价格
        upper_limit: 最高价格
    """
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans', 'Arial', 'SimHei', 'Arial Unicode MS', 'Noto Sans CJK SC']
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    fig.suptitle(f'{stock_name}({stock_code}) Grid Trading Strategy', fontsize=16, fontweight='bold')
    
    buy_dates = []
    buy_prices = []
    sell_dates = []
    sell_prices = []
    
    for trade in trades:
        if trade['action'] == '买入':
            buy_dates.append(trade['date'])
            buy_prices.append(trade['exec_price'] if 'exec_price' in trade else trade.get('price', 0))
        elif trade['action'] == '卖出':
            sell_dates.append(trade['date'])
            sell_prices.append(trade['exec_price'] if 'exec_price' in trade else trade.get('price', 0))
    
    # 子图1：股价走势、网格线和买卖点
    ax1 = axes[0]
    ax1.plot(date_index, close_prices, 'b-', linewidth=1.5, label='Close Price')
    
    # 中心线
    ax1.axhline(y=center_price, color='gray', linestyle='-', linewidth=2, alpha=0.8, label=f'Center {center_price}')
    
    # 买入网格线（绿色虚线）
    for price in buy_grid_prices:
        ax1.axhline(y=price, color='green', linestyle='--', linewidth=1, alpha=0.6)
        ax1.text(date_index[0], price, f' Buy {int(price)}', va='center', fontsize=9, color='green')
    
    # 卖出网格线（红色虚线）
    for price in sell_grid_prices:
        ax1.axhline(y=price, color='red', linestyle='--', linewidth=1, alpha=0.6)
        ax1.text(date_index[0], price, f' Sell {int(price)}', va='center', fontsize=9, color='red')
    
    # 标记买入点
    if buy_dates:
        ax1.scatter(buy_dates, buy_prices, marker='^', color='green', s=120, 
                   zorder=5, label='Buy', edgecolors='darkgreen', linewidths=1)
    
    # 标记卖出点
    if sell_dates:
        ax1.scatter(sell_dates, sell_prices, marker='v', color='red', s=120, 
                   zorder=5, label='Sell', edgecolors='darkred', linewidths=1)
    
    ax1.set_ylabel('Price (CNY)', fontsize=12)
    ax1.legend(loc='upper right', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_title('Price Chart with Grid Lines', fontsize=12)
    
    price_min = min(min(close_prices), lower_limit) * 0.95
    price_max = max(max(close_prices), upper_limit) * 1.05
    ax1.set_ylim(price_min, price_max)
    
    # 子图2：资金曲线
    ax2 = axes[1]
    
    nav_values = nav_series.values / 10000 if hasattr(nav_series, 'values') else np.array(nav_series) / 10000
    init_nav = nav_values[0]
    ax2.plot(date_index, nav_values, 'purple', linewidth=1.5, label='Equity Curve')
    ax2.axhline(y=init_nav, color='gray', linestyle='--', linewidth=1, alpha=0.7, label='Initial Capital')
    
    ax2.fill_between(date_index, nav_values, init_nav, 
                     where=(nav_values >= init_nav), color='lightgreen', alpha=0.3)
    ax2.fill_between(date_index, nav_values, init_nav, 
                     where=(nav_values < init_nav), color='lightcoral', alpha=0.3)
    
    for trade in trades:
        trade_date = trade['date']
        if trade_date in date_index:
            idx = date_index.get_loc(trade_date)
            nav_val = nav_values[idx]
            color = 'green' if trade['action'] == '买入' else 'red'
            marker = '^' if trade['action'] == '买入' else 'v'
            ax2.scatter([trade_date], [nav_val], marker=marker, color=color, s=60, zorder=5)
    
    ax2.set_ylabel('Equity (10K CNY)', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.legend(loc='upper left', fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_title('Equity Curve', fontsize=12)
    
    final_nav = nav_values[-1]
    final_return = (nav_values[-1] / init_nav - 1) * 100
    ax2.annotate(f'Final: {final_nav:.2f}K ({final_return:+.2f}%)', 
                 xy=(date_index[-1], final_nav),
                 xytext=(-150, 20), textcoords='offset points',
                 fontsize=11, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color='purple'),
                 color='purple')
    
    ax2.xaxis.set_major_locator(mdates.MonthLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    
    output_dir = os.path.join(os.getcwd(), 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    chart_file = os.path.join(output_dir, f'grid_chart_{stock_code.replace(".", "_")}.png')
    plt.savefig(chart_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"Grid chart saved to: {chart_file}")
    
    plt.close()
    return chart_file


def plot_strategy_results(date_index, close_prices, nav_series, macd_data, trades, stock_name, stock_code, params):
    """Plot strategy backtest results chart"""
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans', 'Arial', 'SimHei', 'Arial Unicode MS', 'Noto Sans CJK SC']
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    fig.suptitle(f'{stock_code} Strategy Backtest', fontsize=16, fontweight='bold')
    
    buy_dates = []
    buy_prices = []
    sell_dates = []
    sell_prices = []
    
    for trade in trades:
        if trade['action'] == '买入':
            buy_dates.append(trade['date'])
            buy_prices.append(trade['price'])
        elif trade['action'] == '卖出':
            sell_dates.append(trade['date'])
            sell_prices.append(trade['price'])
    
    ax1 = axes[0]
    ax1.plot(date_index, close_prices, 'b-', linewidth=1.5, label='Close Price')
    
    if buy_dates:
        ax1.scatter(buy_dates, buy_prices, marker='^', color='red', s=150, 
                   zorder=5, label='Buy', edgecolors='darkred', linewidths=1)
        for i, (date, price) in enumerate(zip(buy_dates, buy_prices)):
            ax1.annotate(f'B{i+1}', (date, price), textcoords="offset points", 
                        xytext=(0, 15), ha='center', fontsize=9, color='red', fontweight='bold')
    
    if sell_dates:
        ax1.scatter(sell_dates, sell_prices, marker='v', color='green', s=150, 
                   zorder=5, label='Sell', edgecolors='darkgreen', linewidths=1)
        for i, (date, price) in enumerate(zip(sell_dates, sell_prices)):
            ax1.annotate(f'S{i+1}', (date, price), textcoords="offset points", 
                        xytext=(0, -20), ha='center', fontsize=9, color='green', fontweight='bold')
    
    ax1.set_ylabel('Price (CNY)', fontsize=12)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_title('Price Chart with Buy/Sell Signals', fontsize=12)
    
    price_min = min(close_prices) * 0.95
    price_max = max(close_prices) * 1.05
    ax1.set_ylim(price_min, price_max)
    
    if macd_data is not None and 'macd' in macd_data.columns:
        ax2 = axes[1]
        
        dif = macd_data['macd'].values
        dea = macd_data['signal_line'].values if 'signal_line' in macd_data.columns else macd_data['signal'].values
        macd_bar = macd_data['histogram'].values if 'histogram' in macd_data.columns else (dif - dea)
        
        ax2.plot(date_index, dif, 'b-', linewidth=1.2, label='DIF')
        ax2.plot(date_index, dea, 'orange', linewidth=1.2, label='DEA')
        
        colors = ['red' if val >= 0 else 'green' for val in macd_bar]
        ax2.bar(date_index, macd_bar, color=colors, alpha=0.6, width=1.5, label='MACD Histogram')
        
        ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.7)
        ax2.set_ylabel('MACD', fontsize=12)
        ax2.legend(loc='upper left', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.set_title(f'MACD Indicator', fontsize=12)
        
        for trade in trades:
            trade_date = trade['date']
            if trade_date in date_index:
                color = 'red' if trade['action'] == '买入' else 'green'
                ax2.axvline(x=trade_date, color=color, linestyle='--', alpha=0.5, linewidth=1)
    else:
        ax2 = axes[1]
        ax2.plot(date_index, close_prices, 'b-', linewidth=1.5, label='Close Price')
        ax2.set_ylabel('Price (CNY)', fontsize=12)
        ax2.legend(loc='upper left', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.set_title('Price Movement', fontsize=12)
    
    ax3 = axes[2]
    
    nav_values = np.array(nav_series) / 10000
    ax3.plot(date_index, nav_values, 'purple', linewidth=1.5, label='Equity Curve')
    ax3.axhline(y=params['initial_capital'] / 10000, color='gray', linestyle='--', linewidth=1, alpha=0.7, label='Initial Capital')
    
    init_nav = params['initial_capital'] / 10000
    ax3.fill_between(date_index, nav_values, init_nav, 
                     where=(nav_values >= init_nav), color='lightgreen', alpha=0.3)
    ax3.fill_between(date_index, nav_values, init_nav, 
                     where=(nav_values < init_nav), color='lightcoral', alpha=0.3)
    
    for trade in trades:
        trade_date = trade['date']
        if trade_date in date_index:
            idx = date_index.get_loc(trade_date)
            nav_val = nav_values[idx]
            color = 'red' if trade['action'] == '买入' else 'green'
            marker = '^' if trade['action'] == '买入' else 'v'
            ax3.scatter([trade_date], [nav_val], marker=marker, color=color, s=80, zorder=5)
    
    ax3.set_ylabel('Equity (10K CNY)', fontsize=12)
    ax3.set_xlabel('Date', fontsize=12)
    ax3.legend(loc='upper left', fontsize=10)
    ax3.grid(True, alpha=0.3)
    ax3.set_title('Equity Curve', fontsize=12)
    
    final_nav = nav_values[-1]
    final_return = (nav_series[-1] / params['initial_capital'] - 1) * 100
    ax3.annotate(f'Final: {final_nav:.2f}K ({final_return:+.2f}%)', 
                 xy=(date_index[-1], final_nav),
                 xytext=(-150, 20), textcoords='offset points',
                 fontsize=11, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color='purple'),
                 color='purple')
    
    ax3.xaxis.set_major_locator(mdates.MonthLocator())
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    
    output_dir = os.path.join(os.getcwd(), 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    chart_file = os.path.join(output_dir, f'chart_{stock_code.replace(".", "_")}.png')
    plt.savefig(chart_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"Chart saved to: {chart_file}")
    
    plt.close()
    return chart_file