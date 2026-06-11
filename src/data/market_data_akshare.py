# -*- coding: utf-8 -*-
"""
行情数据采集 - 使用akshare下载全量A股日线数据存入MySQL

功能：
  1. 获取沪深A股全量股票列表（约5500只）
  2. 一次性批量查询DB中已有的最新日期，仅下载增量数据
  3. 多线程写入MySQL的trade_stock_daily表（ON DUPLICATE KEY UPDATE）

优化：
  - 批量查询DB最新日期，跳过已是最新的股票
  - 移除不必要的sleep，提升吞吐量
  - 使用akshare免费接口，无需QMT权限

运行：python market_data_akshare.py
环境：pip install pymysql python-dotenv akshare
"""
import sys
import os
import time
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

import akshare as ak
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

def get_existing_latest_dates():
    """一次性查询所有股票在DB中的最新交易日，返回 {stock_code: 'YYYYMMDD'}"""
    rows = execute_query(
        "SELECT stock_code, MAX(trade_date) AS max_date FROM trade_stock_daily GROUP BY stock_code"
    )
    result = {}
    for r in rows:
        if r['max_date']:
            result[r['stock_code']] = r['max_date'].strftime('%Y%m%d')
    return result


def get_stock_list():
    """获取A股股票列表"""
    try:
        stocks_df = ak.stock_info_a_code_name()
        a_stock_pattern = r'^(000|001|002|003|600|601|603|605|688)\d{4}$'
        stocks_df = stocks_df[stocks_df['code'].str.match(a_stock_pattern, na=False)]
        return stocks_df['code'].tolist()
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return []


# ============================================================
# 核心逻辑
# ============================================================

INSERT_SQL = """
    INSERT INTO trade_stock_daily
    (stock_code, trade_date, open_price, high_price, low_price, close_price, volume, amount, turnover_rate)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    open_price=VALUES(open_price), high_price=VALUES(high_price),
    low_price=VALUES(low_price), close_price=VALUES(close_price),
    volume=VALUES(volume), amount=VALUES(amount),
    turnover_rate=VALUES(turnover_rate)
"""


def download_and_save(stock_code, start_date, adjust_type):
    """增量下载单只股票的日线数据并写入MySQL"""
    try:
        # akshare的stock_zh_a_hist接口
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period='daily',
            start_date=start_date,
            adjust=adjust_type
        )

        if df is None or len(df) == 0:
            return stock_code, 0

        rows = []
        for _, row in df.iterrows():
            trade_date = row['日期']
            vol = int(row['成交量'])
            vol_hands = vol // 100 if vol > 0 else 0

            rows.append((
                stock_code, trade_date,
                float(row['开盘']), float(row['收盘']),
                float(row['最高']), float(row['最低']),
                vol_hands, float(row['成交额']),
                float(row['换手率']) if pd.notna(row['换手率']) else None,
            ))

        if rows:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.executemany(INSERT_SQL, rows)
            conn.commit()
            cursor.close()
            conn.close()

        return stock_code, len(rows)

    except Exception as e:
        print(f"\n  下载 {stock_code} 失败: {e}")
        return stock_code, -1


# ============================================================
# 主流程
# ============================================================

def main():
    # 从配置文件读取参数
    market_data_config = get_main_config('market_data')
    TEST_MODE = market_data_config.get('test_mode', False)
    TEST_STOCK = market_data_config.get('test_stock', '600519')
    NUM_WORKERS = market_data_config.get('num_workers', 8)
    DATA_START = market_data_config.get('data_start', '20230101')
    ADJUST_TYPE = market_data_config.get('adjust_type', 'qfq')  # 默认前复权

    print("=" * 60)
    print("行情数据采集 (akshare -> MySQL)")
    print(f"复权类型: {'前复权' if ADJUST_TYPE == 'qfq' else '后复权' if ADJUST_TYPE == 'hfq' else '不复权'}")
    if TEST_MODE:
        print("[测试模式] 只采集贵州茅台")
    else:
        print(f"[全量模式] 采集沪深A股, {NUM_WORKERS}线程并行")
    print("=" * 60)

    # 获取股票列表
    if TEST_MODE:
        all_codes = [TEST_STOCK]
        print(f"\n[测试模式] 只采集 {TEST_STOCK}")
    else:
        print(f"\n获取A股股票列表...")
        all_codes = get_stock_list()
        print(f"  共 {len(all_codes)} 只股票")

    if not all_codes:
        print("\n未获取到股票列表，退出")
        return

    # 批量查询DB中已有的最新日期
    print("查询数据库已有数据...")
    existing = get_existing_latest_dates()
    recent_cutoff = date.today().strftime('%Y%m%d')

    tasks = []
    skip_count = 0
    for code in all_codes:
        latest = existing.get(code)
        if latest and latest >= recent_cutoff:
            skip_count += 1
            continue
        start = latest if latest else DATA_START
        tasks.append((code, start))

    print(f"  需更新: {len(tasks)} 只, 跳过(今日已有数据): {skip_count} 只")

    if not tasks:
        print("\n全部已是最新，无需更新")
        _print_summary()
        return

    total = len(tasks)
    total_rows = 0
    success_count = 0
    fail_list = []
    start_time = time.time()

    if total <= 5:
        for i, (code, start) in enumerate(tasks, 1):
            print(f"\n[{i}/{total}] {code} (从 {start} 开始)")
            _, count = download_and_save(code, start, ADJUST_TYPE)
            if count >= 0:
                print(f"  写入 {count} 条")
                success_count += 1
                total_rows += max(count, 0)
            else:
                print(f"  失败")
                fail_list.append(code)
    else:
        print(f"\n并行下载（{NUM_WORKERS} 线程）...")

        def _worker(args):
            code, start = args
            try:
                return download_and_save(code, start, ADJUST_TYPE)
            except Exception:
                return code, -1

        with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            futures = {executor.submit(_worker, t): t[0] for t in tasks}
            done = 0
            for future in as_completed(futures):
                code, count = future.result()
                done += 1

                if count >= 0:
                    success_count += 1
                    total_rows += max(count, 0)
                else:
                    fail_list.append(code)

                elapsed = time.time() - start_time
                speed = done / elapsed if elapsed > 0 else 0
                eta = (total - done) / speed if speed > 0 else 0
                sys.stdout.write(
                    f"\r  进度 {done}/{total} ({done*100/total:.1f}%) | "
                    f"{speed:.1f} 只/秒 | 剩余约 {eta:.0f}秒 | "
                    f"成功 {success_count} 失败 {len(fail_list)}    "
                )
                sys.stdout.flush()

        print()

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"采集完成! 耗时 {elapsed:.1f} 秒")
    print(f"  成功: {success_count}/{total} 只股票")
    print(f"  总写入: {total_rows:,} 条记录")

    if fail_list:
        print(f"  失败 {len(fail_list)} 只: {fail_list[:20]}{'...' if len(fail_list) > 20 else ''}")

    _print_summary()


def _print_summary():
    summary = execute_query("""
        SELECT COUNT(DISTINCT stock_code) as stock_cnt,
               COUNT(*) as row_cnt,
               MIN(trade_date) as min_date, MAX(trade_date) as max_date
        FROM trade_stock_daily
    """)
    if summary:
        row = summary[0]
        print(f"\n数据库 trade_stock_daily 概况:")
        print(f"  {row['stock_cnt']} 只股票, {row['row_cnt']:,} 条记录")
        print(f"  日期范围: {row['min_date']} ~ {row['max_date']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
