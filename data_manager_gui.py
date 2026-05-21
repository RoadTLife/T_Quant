#!/usr/bin/env python3
"""
数据管理交互式工具

提供菜单式操作界面，方便用户管理股票数据
"""

from utils.data_manager import DataManager
from utils.cli_utils import (
    print_table, print_title, print_success, print_error, 
    print_info, print_warning, get_input, validate_date, 
    validate_time, validate_stock_symbol
)

class DataManagerGUI:
    def __init__(self):
        self.dm = DataManager()
        self.running = True
    
    def print_header(self):
        """打印头部信息"""
        print_title("量化交易数据管理系统")
    
    def print_menu(self):
        """打印主菜单"""
        print("\n请选择操作:")
        menu_items = [
            ("1", "列出已下载股票"),
            ("2", "数据库统计概况"),
            ("3", "查看股票详情"),
            ("4", "添加股票"),
            ("5", "下载股票数据"),
            ("6", "扫描数据缺口"),
            ("7", "修复数据缺口"),
            ("8", "同步当日数据"),
            ("9", "设置定时同步"),
            ("0", "退出系统")
        ]
        
        for key, desc in menu_items:
            print(f"{key}. {desc}")
        print("-" * 40)
    
    def action_list_stocks(self):
        """列出已下载股票"""
        print("\n--- 已下载股票列表 ---")
        stocks = self.dm.list_downloaded_stocks()
        
        if stocks.empty:
            print_info("暂无已下载的股票")
        else:
            print_table(stocks)
    
    def action_summary(self):
        """数据库统计概况"""
        print("\n--- 数据库统计概况 ---")
        summary = self.dm.get_database_summary()
        
        print_table({
            '股票数量': summary['total_stocks'],
            '数据记录': summary['total_records'],
            '日期范围': f"{summary['date_range']['start']} ~ {summary['date_range']['end']}",
            '不完整股票': summary['incomplete_stocks'],
            '数据库路径': summary['database_path']
        })
    
    def action_detail(self):
        """查看股票详情"""
        print("\n--- 查看股票详情 ---")
        
        symbol = get_input("请输入股票代码: ")
        valid, msg = validate_stock_symbol(symbol)
        if not valid:
            print_error(msg)
            return
        
        detail = self.dm.get_stock_detail(symbol)
        if not detail:
            print_error(f"未找到股票: {symbol}")
            return
        
        print(f"\n股票详情: {symbol}")
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
    
    def action_add_stock(self):
        """添加股票"""
        print("\n--- 添加股票 ---")
        
        symbol = get_input("请输入股票代码: ")
        valid, msg = validate_stock_symbol(symbol)
        if not valid:
            print_error(msg)
            return
        
        name = get_input("请输入股票名称 (可选): ", required=False)
        industry = get_input("请输入行业 (可选): ", required=False)
        market = get_input("请输入市场类型 (默认A): ", required=False, default='A')
        listed_date = get_input("请输入上市日期 (可选): ", required=False)
        
        success = self.dm.add_stock(symbol, name, market, industry, listed_date)
        if success:
            print_success(f"成功添加股票: {symbol}")
        else:
            print_warning(f"股票已存在: {symbol}")
    
    def action_download(self):
        """下载股票数据"""
        print("\n--- 下载股票数据 ---")
        
        symbol = get_input("请输入股票代码: ")
        valid, msg = validate_stock_symbol(symbol)
        if not valid:
            print_error(msg)
            return
        
        while True:
            start_date = get_input("请输入开始日期 (YYYY-MM-DD): ")
            valid, msg = validate_date(start_date)
            if valid:
                break
            print_error(msg)
        
        while True:
            end_date = get_input("请输入结束日期 (YYYY-MM-DD): ")
            valid, msg = validate_date(end_date)
            if valid:
                break
            print_error(msg)
        
        source = get_input("请输入数据源 (默认akshare): ", required=False, default='akshare')
        
        print(f"\n正在下载 {symbol} ({start_date} ~ {end_date})...")
        success, msg = self.dm.download_data(symbol, start_date, end_date, source)
        
        if success:
            print_success(msg)
        else:
            print_error(msg)
    
    def action_scan(self):
        """扫描数据缺口"""
        print("\n--- 扫描数据缺口 ---")
        
        symbol = get_input("请输入股票代码 (回车扫描全部): ", required=False)
        
        print_info("正在扫描数据缺口...")
        gaps = self.dm.scan_data_gaps(symbol)
        
        if not gaps:
            print_info("暂无数据")
            return
        
        for sym, info in gaps.items():
            print(f"\n股票: {sym}")
            print_table({
                '状态': info['status'],
                '预期记录': info['expected_records'],
                '实际记录': info['actual_records'],
                '缺口数量': info['gap_count']
            })
            if info['missing_dates']:
                print(f"缺失日期示例: {', '.join(info['missing_dates'][:5])}")
    
    def action_fix(self):
        """修复数据缺口"""
        print("\n--- 修复数据缺口 ---")
        
        symbol = get_input("请输入股票代码 (回车修复全部): ", required=False)
        
        print_info("正在修复数据缺口...")
        results = self.dm.fix_data_gaps(symbol)
        
        if not results:
            print_info("没有需要修复的股票")
            return
        
        for sym, result in results.items():
            print(f"\n股票: {sym}")
            print_table({
                '状态': result['status'],
                '修复数量': result['fixed_count']
            })
            if result.get('failed_dates'):
                print(f"失败日期: {len(result['failed_dates'])} 个")
    
    def action_sync(self):
        """同步当日数据"""
        print("\n--- 同步当日数据 ---")
        
        print_info("正在同步当日数据...")
        result = self.dm.sync_today_data()
        
        print(f"\n同步结果:")
        print(f"  成功: {len(result['success'])} 只股票")
        if result['success']:
            print(f"    {', '.join(result['success'])}")
        
        if result['failed']:
            print(f"  失败: {len(result['failed'])} 只股票")
            for item in result['failed']:
                print(f"    {item['symbol']}: {item['error']}")
    
    def action_schedule(self):
        """设置定时同步"""
        print("\n--- 设置定时同步 ---")
        
        while True:
            time = get_input("请输入定时时间 (默认18:00): ", required=False, default='18:00')
            valid, msg = validate_time(time)
            if valid:
                break
            print_error(msg)
        
        success, msg = self.dm.schedule_sync(time)
        if success:
            print_success(msg)
        else:
            print_error(msg)
    
    def action_exit(self):
        """退出系统"""
        print("\n感谢使用量化交易数据管理系统！")
        self.running = False
    
    def run(self):
        """主运行循环"""
        actions = {
            '1': self.action_list_stocks,
            '2': self.action_summary,
            '3': self.action_detail,
            '4': self.action_add_stock,
            '5': self.action_download,
            '6': self.action_scan,
            '7': self.action_fix,
            '8': self.action_sync,
            '9': self.action_schedule,
            '0': self.action_exit
        }
        
        while self.running:
            self.print_header()
            self.print_menu()
            
            choice = input("请输入操作编号: ").strip()
            
            if choice in actions:
                try:
                    actions[choice]()
                except Exception as e:
                    print_error(f"操作失败: {e}")
            else:
                print_error("无效的选择，请重新输入")
            
            if self.running:
                input("\n按回车键继续...")

if __name__ == '__main__':
    gui = DataManagerGUI()
    gui.run()