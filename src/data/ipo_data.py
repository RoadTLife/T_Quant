# -*- coding: utf-8 -*-
"""
A股新股发行数据采集 - AkShare -> MySQL

功能：
  1. 获取A股新股发行列表（首发、增发、配股等）
  2. 保存原始数据到 trade_stock_ipo_detail 表
  3. 按月份统计新股发行数量
  4. 写入 trade_stock_ipo 表

数据源：AkShare stock_ipo_review_em() - 可获取2006年至今的数据

运行：python ipo_data.py
"""
import sys
import os
import pandas as pd
import akshare as ak

# 添加项目根目录到路径
def _add_project_root():
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

_add_project_root()
from src.conf.db_config import get_connection, execute_query

if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def fetch_new_stocks():
    """获取A股新股发行数据（使用stock_ipo_review_em获取历史数据）"""
    print("采集新股数据...")
    
    # 优先使用stock_ipo_review_em获取历史数据（2006年至今）
    df = ak.stock_ipo_review_em()
    
    if df is None or len(df) == 0:
        print("  stock_ipo_review_em 返回空，尝试备用接口...")
        df = ak.stock_new_ipo_cninfo()
    
    if df is None or len(df) == 0:
        print("  stock_new_ipo_cninfo 返回空，尝试同花顺接口...")
        df = ak.stock_ipo_ths()
    
    if df is None or len(df) == 0:
        print("  所有接口都返回空")
        return pd.DataFrame()
    
    print(f"  原始数据: {len(df)} 条")
    print(f"  列名: {list(df.columns)}")
    return df


def save_ipo_detail_to_mysql(df):
    """保存原始IPO详情数据到MySQL"""
    if len(df) == 0:
        return 0
    
    conn = get_connection()
    cursor = conn.cursor()
    
    sql = """
        INSERT INTO trade_stock_ipo_detail 
        (stock_code, stock_name, listed_date, subscribe_date, issue_price,
         issue_volume, online_volume, issue_pe, subscription_rate, financing_amount,
         listing_board, underwriter, sponsor, review_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        stock_name=VALUES(stock_name),
        subscribe_date=VALUES(subscribe_date),
        issue_price=VALUES(issue_price),
        issue_volume=VALUES(issue_volume),
        online_volume=VALUES(online_volume),
        issue_pe=VALUES(issue_pe),
        subscription_rate=VALUES(subscription_rate),
        financing_amount=VALUES(financing_amount),
        listing_board=VALUES(listing_board),
        underwriter=VALUES(underwriter),
        sponsor=VALUES(sponsor),
        review_status=VALUES(review_status),
        updated_at=CURRENT_TIMESTAMP
    """
    
    count = 0
    for _, row in df.iterrows():
        # 解析日期
        listed_date = None
        if '上市日期' in df.columns and pd.notna(row['上市日期']):
            try:
                listed_date = pd.Timestamp(str(row['上市日期']).strip()[:10])
                listed_date = listed_date.strftime('%Y-%m-%d')
            except:
                pass
        
        subscribe_date = None
        if '申购日期' in df.columns and pd.notna(row['申购日期']):
            try:
                subscribe_date = pd.Timestamp(str(row['申购日期']).strip()[:10])
                subscribe_date = subscribe_date.strftime('%Y-%m-%d')
            except:
                pass
        
        # 适配不同接口的列名
        stock_code = str(row['股票代码']).strip() if '股票代码' in df.columns and pd.notna(row['股票代码']) else None
        stock_name = str(row['股票简称']).strip() if '股票简称' in df.columns and pd.notna(row['股票简称']) else None
        issue_price = float(row['发行价']) if '发行价' in df.columns and pd.notna(row['发行价']) else None
        
        # 发行数量可能是'总发行数量'或'发行数量(股)'
        issue_volume = None
        if '总发行数量' in df.columns and pd.notna(row['总发行数量']):
            issue_volume = float(row['总发行数量'])
        elif '发行数量(股)' in df.columns and pd.notna(row['发行数量(股)']):
            # 转换为万股
            issue_volume = float(row['发行数量(股)']) / 10000
        
        online_volume = float(row['上网发行数量']) if '上网发行数量' in df.columns and pd.notna(row['上网发行数量']) else None
        issue_pe = float(row['发行市盈率']) if '发行市盈率' in df.columns and pd.notna(row['发行市盈率']) else None
        subscription_rate = float(row['上网发行中签率']) if '上网发行中签率' in df.columns and pd.notna(row['上网发行中签率']) else None
        financing_amount = float(row['拟融资额(元)']) if '拟融资额(元)' in df.columns and pd.notna(row['拟融资额(元)']) else None
        listing_board = str(row['上市板块']).strip() if '上市板块' in df.columns and pd.notna(row['上市板块']) else None
        underwriter = str(row['主承销商']).strip() if '主承销商' in df.columns and pd.notna(row['主承销商']) else None
        sponsor = str(row['保荐机构']).strip() if '保荐机构' in df.columns and pd.notna(row['保荐机构']) else None
        review_status = str(row['审核状态']).strip() if '审核状态' in df.columns and pd.notna(row['审核状态']) else None
        
        cursor.execute(sql, (
            stock_code, stock_name, listed_date, subscribe_date, issue_price,
            issue_volume, online_volume, issue_pe, subscription_rate, financing_amount,
            listing_board, underwriter, sponsor, review_status
        ))
        count += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    return count


def parse_and_statistics(df):
    """解析数据并按月份统计"""
    if len(df) == 0:
        return pd.DataFrame()
    
    # 查找列名（适配不同接口）
    date_col = None
    amount_col = None
    
    for col in df.columns:
        if '上市日期' in col:
            date_col = col
        elif '拟融资额' in col:
            amount_col = col
        elif '融资额' in col:
            amount_col = col
    
    if date_col is None:
        date_col = df.columns[0]
    
    print(f"  使用列: 日期={date_col}, 融资额={amount_col}")
    
    # 解析日期
    def parse_date(s):
        if pd.isna(s):
            return pd.NaT
        s = str(s).strip()
        # 完整格式: 2026-05-27
        if len(s) >= 10 and s[4] == '-':
            try:
                return pd.Timestamp(s[:10])
            except:
                pass
        # 短格式: 06-01 周一
        if len(s) >= 5 and s[2] == '-':
            try:
                month = int(s[:2])
                day = int(s[3:5])
                return pd.Timestamp(year=pd.Timestamp.now().year, month=month, day=day)
            except:
                pass
        return pd.NaT
    
    df['trade_date'] = df[date_col].apply(parse_date)
    df_valid = df.dropna(subset=['trade_date']).copy()
    print(f"  解析日期后: {len(df_valid)} 条")
    
    # 过滤未来日期（只保留发行日期 <= 今天的）
    today = pd.Timestamp.now().normalize()
    future_count = len(df_valid[df_valid['trade_date'] > today])
    df_valid = df_valid[df_valid['trade_date'] <= today]
    print(f"  过滤未来数据（{future_count}条）后: {len(df_valid)} 条")
    
    # 计算募集资金（从拟融资额字段获取，单位转换为亿元）
    if amount_col and amount_col in df_valid.columns:
        df_valid['amount'] = pd.to_numeric(df_valid[amount_col], errors='coerce').fillna(0)
        # 转换为亿元（原单位是元）
        df_valid['amount'] = df_valid['amount'] / 100000000
        print(f"  募集资金范围: {df_valid['amount'].min():.2f} ~ {df_valid['amount'].max():.2f} 亿元")
    else:
        df_valid['amount'] = 0
        print("  未找到融资额字段")
    
    # 按月份分组统计
    df_valid['month'] = df_valid['trade_date'].dt.to_period('M').dt.to_timestamp('M')
    
    stats = df_valid.groupby('month').agg(
        ipo_count=('month', 'count'),
        total_amount=('amount', 'sum'),
        avg_amount=('amount', 'mean'),
        max_amount=('amount', 'max')
    ).reset_index()
    
    # 按月份排序
    stats = stats.sort_values('month').reset_index(drop=True)
    
    # 打印统计数据（最近12个月 + 年份汇总）
    print("\n按月份统计（最近12个月）...")
    recent_stats = stats.tail(12)
    for _, row in recent_stats.iterrows():
        month_str = row['month'].strftime('%Y-%m')
        count = row['ipo_count']
        total = row['total_amount']
        print(f"  {month_str}: {count} 只新股, 募资 {total:.2f} 亿元")
    
    # 按年份汇总
    print("\n按年份汇总...")
    stats['year'] = stats['month'].dt.year
    yearly_stats = stats.groupby('year').agg(
        month_count=('year', 'count'),
        ipo_count=('ipo_count', 'sum'),
        total_amount=('total_amount', 'sum')
    ).reset_index()
    
    for _, row in yearly_stats.iterrows():
        print(f"  {row['year']}: {row['month_count']}个月, {row['ipo_count']}只新股, 募资 {row['total_amount']:.2f} 亿元")
    
    return stats


def save_ipo_summary_to_mysql(df):
    """保存月度统计数据到MySQL"""
    if len(df) == 0:
        return 0
    
    conn = get_connection()
    cursor = conn.cursor()
    
    sql = """
        INSERT INTO trade_stock_ipo 
        (ipo_month, ipo_count, total_amount, avg_amount, max_amount)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        ipo_count=VALUES(ipo_count),
        total_amount=VALUES(total_amount),
        avg_amount=VALUES(avg_amount),
        max_amount=VALUES(max_amount),
        updated_at=CURRENT_TIMESTAMP
    """
    
    count = 0
    for _, row in df.iterrows():
        cursor.execute(sql, (
            row['month'].strftime('%Y-%m-%d'),
            row['ipo_count'],
            round(row['total_amount'], 2) if pd.notna(row['total_amount']) else None,
            round(row['avg_amount'], 2) if pd.notna(row['avg_amount']) else None,
            round(row['max_amount'], 2) if pd.notna(row['max_amount']) else None
        ))
        count += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    return count


def main():
    print("=" * 60)
    print("A股新股发行数据采集 -> MySQL")
    print("=" * 60)
    
    # 获取新股数据
    df = fetch_new_stocks()
    if len(df) == 0:
        print("\n无数据可采集")
        print("=" * 60)
        return
    
    # 保存原始数据到详情表
    print(f"\n保存原始数据到 trade_stock_ipo_detail...")
    detail_count = save_ipo_detail_to_mysql(df)
    print(f"  写入 {detail_count} 条原始数据")
    
    # 按月份统计
    stats = parse_and_statistics(df)
    if len(stats) == 0:
        print("\n无数据可统计")
        print("=" * 60)
        return
    
    # 写入月度统计数据
    print(f"\n写入 {len(stats)} 条月度统计数据")
    save_ipo_summary_to_mysql(stats)
    
    # 打印概况
    summary = execute_query("""
        SELECT COUNT(*) as cnt,
               MIN(ipo_month) as min_date, MAX(ipo_month) as max_date,
               SUM(ipo_count) as total_ipo,
               SUM(total_amount) as total_amount
        FROM trade_stock_ipo
    """)
    if summary:
        r = summary[0]
        print(f"\ntrade_stock_ipo 概况:")
        print(f"  时间范围: {r['min_date']} ~ {r['max_date']}")
        print(f"  总月份数: {r['cnt']} 个月")
        print(f"  新股总数: {r['total_ipo']} 只")
        print(f"  募资总额: {r['total_amount']:.2f} 亿元")
    
    # 打印详情表概况
    detail_summary = execute_query("""
        SELECT COUNT(*) as cnt,
               MIN(listed_date) as min_date, MAX(listed_date) as max_date
        FROM trade_stock_ipo_detail
        WHERE listed_date IS NOT NULL
    """)
    if detail_summary:
        r = detail_summary[0]
        print(f"\ntrade_stock_ipo_detail 概况:")
        print(f"  记录数: {r['cnt']} 条")
        print(f"  时间范围: {r['min_date']} ~ {r['max_date']}")
    
    print("\n" + "=" * 60)
    print("A股新股发行数据采集完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()