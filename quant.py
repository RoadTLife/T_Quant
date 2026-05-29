#!/usr/bin/env python3
"""
量化交易系统统一命令入口

Usage:
    python quant.py <command> [options]

Commands:
    gui                 启动交互式数据管理界面
    list                列出已下载股票
    summary             数据库统计概况
    detail <symbol>     查看股票详情
    add <symbol>        添加股票
    download            下载股票数据
    scan                扫描数据缺口
    fix                 修复数据缺口
    sync                同步当日数据
    schedule <time>     设置定时同步
    backtest <symbol>   运行回测
"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(
        description='量化交易系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    subparsers.add_parser('gui', help='启动交互式数据管理界面')
    subparsers.add_parser('list', help='列出已下载股票')
    subparsers.add_parser('summary', help='数据库统计概况')
    subparsers.add_parser('sync', help='同步当日数据')
    
    detail_parser = subparsers.add_parser('detail', help='查看股票详情')
    detail_parser.add_argument('symbol', help='股票代码')
    
    add_parser = subparsers.add_parser('add', help='添加股票')
    add_parser.add_argument('symbol', help='股票代码')
    add_parser.add_argument('--name', default='', help='股票名称')
    add_parser.add_argument('--market', default='A', help='市场类型')
    add_parser.add_argument('--industry', default='', help='行业')
    add_parser.add_argument('--listed_date', default='', help='上市日期')
    
    download_parser = subparsers.add_parser('download', help='下载股票数据')
    download_parser.add_argument('start', help='开始日期 (YYYY-MM-DD)')
    download_parser.add_argument('end', help='结束日期 (YYYY-MM-DD)')
    download_parser.add_argument('--symbol', help='股票代码（不指定则使用--all）')
    download_parser.add_argument('--all', action='store_true', help='下载所有股票')
    download_parser.add_argument('--source', default='baostock', help='数据源')
    
    scan_parser = subparsers.add_parser('scan', help='扫描数据缺口')
    scan_parser.add_argument('--symbol', help='股票代码（可选）')
    
    fix_parser = subparsers.add_parser('fix', help='修复数据缺口')
    fix_parser.add_argument('--symbol', help='股票代码（可选）')
    
    schedule_parser = subparsers.add_parser('schedule', help='设置定时同步')
    schedule_parser.add_argument('time', help='定时时间 (HH:MM)')
    
    backtest_parser = subparsers.add_parser('backtest', help='运行回测')
    backtest_parser.add_argument('symbol', help='股票代码（可选）')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    execute_command(args)

def execute_command(args):
    """执行命令"""
    if args.command == 'gui':
        from src.cli.data_manager_gui import DataManagerGUI
        gui = DataManagerGUI()
        gui.run()
        return
    
    from src.cli.data_cli import (
        cmd_list, cmd_summary, cmd_detail, cmd_add,
        cmd_download, cmd_scan, cmd_fix, cmd_sync, cmd_schedule
    )
    
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
    
    if args.command == 'backtest':
        run_backtest(args)
        return
    
    if args.command in commands:
        try:
            commands[args.command](args)
        except Exception as e:
            from src.utils.cli_utils import exit_with_error
            exit_with_error(f"执行失败: {e}")
    else:
        print(f"未知命令: {args.command}")
        sys.exit(1)

def run_backtest(args):
    """运行回测"""
    from main import main as run_main
    
    if hasattr(args, 'symbol') and args.symbol:
        import os
        os.environ['BACKTEST_SYMBOL'] = args.symbol
    
    run_main()

if __name__ == '__main__':
    main()