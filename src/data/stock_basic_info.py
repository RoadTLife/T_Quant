# -*- coding: utf-8 -*-
"""
股票基础信息采集 - 高效完整版

功能：
  1. 使用 stock_info_a_code_name 批量获取股票代码和名称
  2. 使用 stock_board_industry_cons_em 获取行业板块成分股
  3. 写入 MySQL 的 trade_stock_basic 表

策略：
  - 先批量获取所有股票列表
  - 再获取行业板块成分股映射
  - 最后批量写入数据库

运行：python stock_basic_info.py
环境：pip install pymysql python-dotenv akshare pandas
"""
import sys
import os
import time
import pandas as pd

# 添加项目根目录到路径
def _add_project_root():
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

_add_project_root()
from src.conf.db_config import get_connection, execute_query
from src.utils.config_loader import get_main_config

if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# ============================================================
# 数据库辅助
# ============================================================

def get_existing_stocks():
    """查询数据库中已有的股票代码"""
    rows = execute_query("SELECT stock_code FROM trade_stock_basic")
    return {r['stock_code'] for r in rows} if rows else set()


# ============================================================
# 核心逻辑
# ============================================================

INSERT_SQL = """
    INSERT INTO trade_stock_basic
    (stock_code, stock_name, exchange, industry, sector, listed_date, total_shares, float_shares, is_st, is_hk, data_source)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    stock_name=VALUES(stock_name), exchange=VALUES(exchange),
    industry=VALUES(industry), sector=VALUES(sector),
    listed_date=VALUES(listed_date), total_shares=VALUES(total_shares),
    float_shares=VALUES(float_shares), is_st=VALUES(is_st),
    updated_at=NOW()
"""


def get_stock_list_from_akshare():
    """批量获取 A 股股票列表（过滤空名称）"""
    print("使用 akshare 获取股票列表...")
    try:
        import akshare as ak
        df = ak.stock_info_a_code_name()
        if df is None or len(df) == 0:
            print("  获取失败")
            return None
        
        # 过滤空名称的股票
        original_count = len(df)
        df = df[df['name'].notna() & (df['name'] != '')]
        filtered_count = original_count - len(df)
        
        print(f"  共 {len(df)} 只 A 股 (过滤空名称 {filtered_count} 只)")
        return df
    
    except Exception as e:
        print(f"  获取失败：{e}")
        return None


def get_industry_mapping():
    """获取行业板块映射（使用baostock）"""
    print("获取行业板块映射...")
    stock_industry_map = {}
    
    try:
        import baostock as bs
        
        lg = bs.login()
        if lg.error_code != '0':
            print(f"  登录失败：{lg.error_msg}")
            return {}
        
        rs = bs.query_stock_industry()
        if rs.error_code != '0':
            print(f"  获取行业数据失败：{rs.error_msg}")
            bs.logout()
            return {}
        
        industry_df = rs.get_data()
        if industry_df is None or len(industry_df) == 0:
            print("  获取行业板块列表失败")
            bs.logout()
            return {}
        
        total = len(industry_df)
        print(f"  共 {total} 条行业记录")
        
        for i, (_, row) in enumerate(industry_df.iterrows(), 1):
            code = str(row.get('code', ''))
            industry_name = row.get('industry', '')
            
            if pd.isna(industry_name) or not industry_name:
                industry_name = '未分类'
            
            if '.' in code:
                code = code.split('.')[1]
            if not code or len(code) != 6:
                continue
            if code not in stock_industry_map:
                stock_industry_map[code] = industry_name
            
            if i % 1000 == 0:
                print(f"    已处理 {i}/{total} 条记录，已映射 {len(stock_industry_map)} 只股票")
        
        bs.logout()
        print(f"  完成！共映射 {len(stock_industry_map)} 只股票到行业板块")
        return stock_industry_map
    
    except Exception as e:
        print(f"  获取行业板块映射失败：{e}")
        return {}


def main():
    # 从配置文件读取参数
    stock_basic_config = get_main_config('stock_basic')
    TEST_MODE = stock_basic_config.get('test_mode', False)
    TEST_STOCK = stock_basic_config.get('test_stock', '600519')
    REQUEST_DELAY = stock_basic_config.get('request_delay', 0.5)
    
    print("=" * 60)
    print("股票基础信息采集 (高效完整版)")
    if TEST_MODE:
        print("[测试模式] 只采集贵州茅台")
    else:
        print("[全量模式] 采集沪深 A 股全量股票")
    print("=" * 60)
    
    # 获取股票列表
    stock_list_df = None
    if TEST_MODE:
        stock_list_df = pd.DataFrame({'code': ['600519'], 'name': ['贵州茅台']})
        print(f"\n[测试模式] 只采集 {TEST_STOCK}")
    else:
        stock_list_df = get_stock_list_from_akshare()
    
    if stock_list_df is None or len(stock_list_df) == 0:
        print("\n未获取到股票列表，退出")
        return
    
    # 查询已有数据
    print("\n查询数据库已有数据...")
    existing = get_existing_stocks()
    print(f"  已有 {len(existing)} 只股票")
    
    # 获取行业板块映射
    industry_map = get_industry_mapping()
    
    total = len(stock_list_df)
    start_time = time.time()
    
    print(f"\n开始写入数据库...")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    rows = []
    for _, row in stock_list_df.iterrows():
        stock_code = str(row['code'])
        stock_name = str(row.get('name', ''))
        
        # 判断交易所
        exchange = 'SSE' if stock_code.startswith('6') else 'SZSE'
        
        # 判断是否 ST
        is_st = 1 if 'ST' in stock_name else 0
        
        # 获取行业信息
        industry = industry_map.get(stock_code, '')
        
        rows.append((
            stock_code,
            stock_name,
            exchange,
            industry,  # industry
            industry,  # sector
            None,  # listed_date
            None,  # total_shares
            None,  # float_shares
            is_st,
            0,  # is_hk
            'akshare_industry',
        ))
        
        # 批量提交
        if len(rows) >= 500:
            cursor.executemany(INSERT_SQL, rows)
            conn.commit()
            rows = []
    
    # 写入剩余数据
    if rows:
        cursor.executemany(INSERT_SQL, rows)
        conn.commit()
    
    cursor.close()
    conn.close()
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"采集完成！耗时 {elapsed:.1f} 秒")
    print(f"  写入 {total} 只股票")
    
    _print_summary()


def _print_summary():
    """打印数据库概况"""
    summary = execute_query("""
        SELECT COUNT(*) as stock_cnt,
               COUNT(stock_name) as has_name,
               COUNT(industry) as has_industry,
               COUNT(listed_date) as has_listed_date,
               COUNT(total_shares) as has_shares
        FROM trade_stock_basic
    """)
    if summary:
        row = summary[0]
        print(f"\n数据库 trade_stock_basic 概况:")
        print(f"  总股票数：{row['stock_cnt']}")
        print(f"  有名称：{row['has_name']}")
        print(f"  有行业信息：{row['has_industry']}")
        print(f"  有上市日期：{row['has_listed_date']}")
        print(f"  有股本数据：{row['has_shares']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
