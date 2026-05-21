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
from utils.cli_utils import (
    print_table, print_title, print_success, print_error, 
    print_info, exit_with_error, validate_date, validate_time, validate_stock_symbol
)

def cmd_list(args):
    """列出已下载股票"""
    dm = DataManager()
    stocks = dm.list_downloaded_stocks()
    
    if stocks.empty:
        print_info("暂无已下载的股票")
    else:
        print_title("已下载股票列表")
        print_table(stocks)

def cmd_summary(args):
    """数据库统计概况"""
    dm = DataManager()
    summary = dm.get_database_summary()
    
    print_title("数据库统计概况")
    print_table({
        '股票数量': summary['total_stocks'],
        '数据记录': summary['total_records'],
        '日期范围': f"{summary['date_range']['start']} ~ {summary['date_range']['end']}",
        '不完整股票': summary['incomplete_stocks'],
        '数据库路径': summary['database_path']
    })

def cmd_detail(args):
    """查看股票详情"""
    valid, msg = validate_stock_symbol(args.symbol)
    if not valid:
        exit_with_error(msg)
    
    dm = DataManager()
    detail = dm.get_stock_detail(args.symbol)
    
    if not detail:
        exit_with_error(f"未找到股票: {args.symbol}")
    
    print_title(f"股票详情: {args.symbol}")
    print_table({
        '名称': detail['name'],
        '市场': detail['market'],
        '行业': detail['industry'],
        '上市日期': detail['listed_date'],
        '最早数据': detail['earliest_date'],
        '最新数据': detail['latest_date'],
        '数据记录': detail['total_records'],
        '最后同步': detail['last_sync'],
        '状态': detail['status']
    })
    
    if not detail['recent_data'].empty:
        print("\n最近10条数据:")
        print_table(detail['recent_data'])

def cmd_add(args):
    """添加股票"""
    valid, msg = validate_stock_symbol(args.symbol)
    if not valid:
        exit_with_error(msg)
    
    dm = DataManager()
    success = dm.add_stock(args.symbol, args.name, args.market, args.industry, args.listed_date)
    
    if success:
        print_success(f"成功添加股票: {args.symbol}")
    else:
        print_error(f"股票已存在: {args.symbol}")

def cmd_download(args):
    """下载数据"""
    valid, msg = validate_stock_symbol(args.symbol)
    if not valid:
        exit_with_error(msg)
    
    valid_start, msg = validate_date(args.start)
    if not valid_start:
        exit_with_error(f"开始日期{msg}")
    
    valid_end, msg = validate_date(args.end)
    if not valid_end:
        exit_with_error(f"结束日期{msg}")
    
    dm = DataManager()
    print_info(f"正在下载 {args.symbol} ({args.start} ~ {args.end})...")
    
    success, msg = dm.download_data(args.symbol, args.start, args.end, args.source)
    
    if success:
        print_success(msg)
    else:
        print_error(msg)

def cmd_scan(args):
    """扫描数据缺口"""
    dm = DataManager()
    print_info("正在扫描数据缺口...")
    
    gaps = dm.scan_data_gaps(args.symbol)
    
    if not gaps:
        print_info("暂无数据")
        return
    
    for symbol, info in gaps.items():
        print(f"\n股票: {symbol}")
        print_table({
            '状态': info['status'],
            '预期记录': info['expected_records'],
            '实际记录': info['actual_records'],
            '缺口数量': info['gap_count']
        })
        if info['missing_dates']:
            print(f"缺失日期示例: {', '.join(info['missing_dates'][:5])}")

def cmd_fix(args):
    """修复数据缺口"""
    dm = DataManager()
    print_info("正在修复数据缺口...")
    
    results = dm.fix_data_gaps(args.symbol)
    
    if not results:
        print_info("没有需要修复的股票")
        return
    
    for symbol, result in results.items():
        print(f"\n股票: {symbol}")
        print_table({
            '状态': result['status'],
            '修复数量': result['fixed_count']
        })
        if result.get('failed_dates'):
            print(f"失败日期: {len(result['failed_dates'])} 个")

def cmd_sync(args):
    """同步当日数据"""
    dm = DataManager()
    print_info("正在同步当日数据...")
    
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
    valid, msg = validate_time(args.time)
    if not valid:
        exit_with_error(msg)
    
    dm = DataManager()
    success, msg = dm.schedule_sync(args.time)
    
    if success:
        print_success(msg)
    else:
        print_error(msg)

def main():
    parser = argparse.ArgumentParser(
        description='数据管理命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    subparsers.add_parser('list', help='列出已下载股票')
    subparsers.add_parser('summary', help='数据库统计概况')
    
    detail_parser = subparsers.add_parser('detail', help='查看股票详情')
    detail_parser.add_argument('symbol', help='股票代码')
    
    add_parser = subparsers.add_parser('add', help='添加股票')
    add_parser.add_argument('symbol', help='股票代码')
    add_parser.add_argument('--name', default='', help='股票名称')
    add_parser.add_argument('--market', default='A', help='市场类型')
    add_parser.add_argument('--industry', default='', help='行业')
    add_parser.add_argument('--listed_date', default='', help='上市日期')
    
    download_parser = subparsers.add_parser('download', help='下载数据')
    download_parser.add_argument('symbol', help='股票代码')
    download_parser.add_argument('start', help='开始日期 (YYYY-MM-DD)')
    download_parser.add_argument('end', help='结束日期 (YYYY-MM-DD)')
    download_parser.add_argument('--source', default='akshare', help='数据源')
    
    scan_parser = subparsers.add_parser('scan', help='扫描数据缺口')
    scan_parser.add_argument('--symbol', help='股票代码（可选）')
    
    fix_parser = subparsers.add_parser('fix', help='修复数据缺口')
    fix_parser.add_argument('--symbol', help='股票代码（可选）')
    
    subparsers.add_parser('sync', help='同步当日数据')
    
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
    
    try:
        commands[args.command](args)
    except Exception as e:
        exit_with_error(f"执行失败: {e}")

if __name__ == '__main__':
    main()