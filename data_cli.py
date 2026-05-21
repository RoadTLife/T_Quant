#!/usr/bin/env python3
"""
数据管理命令行工具

Usage:
    python data_cli.py list                          # 列出已下载股票
    python data_cli.py summary                       # 数据库统计概况
    python data_cli.py detail <symbol>               # 查看股票详情
    python data_cli.py add <symbol> [--name=<name>]  # 添加股票
    python data_cli.py download <symbol> <start> <end> [--source=<source>]  # 下载数据
    python data_cli.py scan [--symbol=<symbol>]      # 扫描数据缺口
    python data_cli.py fix [--symbol=<symbol>]       # 修复数据缺口
    python data_cli.py sync                          # 同步当日数据
    python data_cli.py schedule <time>               # 设置定时同步
"""

import argparse
import sys
from utils.data_manager import DataManager

def print_table(data):
    """打印表格数据"""
    if isinstance(data, dict):
        for key, value in data.items():
            print(f"{key}: {value}")
    elif hasattr(data, 'to_string'):
        print(data.to_string())
    else:
        print(data)

def cmd_list(args):
    """列出已下载股票"""
    dm = DataManager()
    stocks = dm.list_downloaded_stocks()
    if stocks.empty:
        print("暂无已下载的股票")
    else:
        print("已下载股票列表:")
        print(stocks)

def cmd_summary(args):
    """数据库统计概况"""
    dm = DataManager()
    summary = dm.get_database_summary()
    print("数据库统计概况:")
    print(f"  股票数量: {summary['total_stocks']}")
    print(f"  数据记录: {summary['total_records']}")
    print(f"  日期范围: {summary['date_range']['start']} ~ {summary['date_range']['end']}")
    print(f"  不完整股票: {summary['incomplete_stocks']}")
    print(f"  数据库路径: {summary['database_path']}")

def cmd_detail(args):
    """查看股票详情"""
    dm = DataManager()
    detail = dm.get_stock_detail(args.symbol)
    if not detail:
        print(f"未找到股票: {args.symbol}")
        return
    
    print(f"股票详情: {args.symbol}")
    print(f"  名称: {detail['name']}")
    print(f"  市场: {detail['market']}")
    print(f"  行业: {detail['industry']}")
    print(f"  上市日期: {detail['listed_date']}")
    print(f"  最早数据: {detail['earliest_date']}")
    print(f"  最新数据: {detail['latest_date']}")
    print(f"  数据记录: {detail['total_records']}")
    print(f"  最后同步: {detail['last_sync']}")
    print(f"  状态: {detail['status']}")
    
    if not detail['recent_data'].empty:
        print("\n  最近10条数据:")
        print(detail['recent_data'].to_string(index=False))

def cmd_add(args):
    """添加股票"""
    dm = DataManager()
    success = dm.add_stock(args.symbol, args.name, args.market, args.industry, args.listed_date)
    if success:
        print(f"成功添加股票: {args.symbol}")
    else:
        print(f"股票已存在: {args.symbol}")

def cmd_download(args):
    """下载数据"""
    dm = DataManager()
    print(f"正在下载 {args.symbol} ({args.start} ~ {args.end})...")
    success, msg = dm.download_data(args.symbol, args.start, args.end, args.source)
    if success:
        print(f"✅ 成功: {msg}")
    else:
        print(f"❌ 失败: {msg}")

def cmd_scan(args):
    """扫描数据缺口"""
    dm = DataManager()
    print("正在扫描数据缺口...")
    gaps = dm.scan_data_gaps(args.symbol)
    
    if not gaps:
        print("暂无数据")
        return
    
    for symbol, info in gaps.items():
        print(f"\n股票: {symbol}")
        print(f"  状态: {info['status']}")
        print(f"  预期记录: {info['expected_records']}")
        print(f"  实际记录: {info['actual_records']}")
        print(f"  缺口数量: {info['gap_count']}")
        if info['missing_dates']:
            print(f"  缺失日期示例: {', '.join(info['missing_dates'][:5])}")

def cmd_fix(args):
    """修复数据缺口"""
    dm = DataManager()
    print("正在修复数据缺口...")
    results = dm.fix_data_gaps(args.symbol)
    
    if not results:
        print("没有需要修复的股票")
        return
    
    for symbol, result in results.items():
        print(f"\n股票: {symbol}")
        print(f"  状态: {result['status']}")
        print(f"  修复数量: {result['fixed_count']}")
        if result.get('failed_dates'):
            print(f"  失败日期: {len(result['failed_dates'])} 个")

def cmd_sync(args):
    """同步当日数据"""
    dm = DataManager()
    print("正在同步当日数据...")
    result = dm.sync_today_data()
    
    print(f"\n同步结果:")
    print(f"  成功: {len(result['success'])} 只股票")
    if result['success']:
        print(f"    {', '.join(result['success'])}")
    
    if result['failed']:
        print(f"  失败: {len(result['failed'])} 只股票")
        for item in result['failed']:
            print(f"    {item['symbol']}: {item['error']}")

def cmd_schedule(args):
    """设置定时同步"""
    dm = DataManager()
    success, msg = dm.schedule_sync(args.time)
    if success:
        print(f"✅ {msg}")
    else:
        print(f"❌ {msg}")

def main():
    parser = argparse.ArgumentParser(description='数据管理命令行工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list 命令
    subparsers.add_parser('list', help='列出已下载股票')
    
    # summary 命令
    subparsers.add_parser('summary', help='数据库统计概况')
    
    # detail 命令
    detail_parser = subparsers.add_parser('detail', help='查看股票详情')
    detail_parser.add_argument('symbol', help='股票代码')
    
    # add 命令
    add_parser = subparsers.add_parser('add', help='添加股票')
    add_parser.add_argument('symbol', help='股票代码')
    add_parser.add_argument('--name', default='', help='股票名称')
    add_parser.add_argument('--market', default='A', help='市场类型')
    add_parser.add_argument('--industry', default='', help='行业')
    add_parser.add_argument('--listed_date', default='', help='上市日期')
    
    # download 命令
    download_parser = subparsers.add_parser('download', help='下载数据')
    download_parser.add_argument('symbol', help='股票代码')
    download_parser.add_argument('start', help='开始日期 (YYYY-MM-DD)')
    download_parser.add_argument('end', help='结束日期 (YYYY-MM-DD)')
    download_parser.add_argument('--source', default='akshare', help='数据源')
    
    # scan 命令
    scan_parser = subparsers.add_parser('scan', help='扫描数据缺口')
    scan_parser.add_argument('--symbol', help='股票代码（可选，不填则扫描全部）')
    
    # fix 命令
    fix_parser = subparsers.add_parser('fix', help='修复数据缺口')
    fix_parser.add_argument('--symbol', help='股票代码（可选，不填则修复全部）')
    
    # sync 命令
    subparsers.add_parser('sync', help='同步当日数据')
    
    # schedule 命令
    schedule_parser = subparsers.add_parser('schedule', help='设置定时同步')
    schedule_parser.add_argument('time', help='定时时间 (HH:MM)')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    commands = {
        'list': cmd_list,
        'summary': cmd_summary,
        'detail': cmd_detail,
        'add': cmd_add,
        'download': cmd_download,
        'scan': cmd_scan,
        'fix': cmd_fix,
        'sync': cmd_sync,
        'schedule': cmd_schedule
    }
    
    commands[args.command](args)

if __name__ == '__main__':
    main()