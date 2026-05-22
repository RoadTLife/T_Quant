import akshare as ak
import pandas as pd
import time
import os
from tqdm import tqdm
from datetime import datetime

def get_all_a_stock_daily_data(
    start_date="20180101", 
    end_date=None,
    adjust="qfq",  # "qfq":前复权, "hfq":后复权, "":不复权
    save_dir="stock_data",
    sleep_time=0.5,
    merge_to_one_file=False
):
    """
    获取所有A股日线数据
    
    参数:
    start_date: 开始日期，格式"YYYYMMDD"，默认"20180101"
    end_date: 结束日期，格式"YYYYMMDD"，默认今天
    adjust: 复权方式，"qfq"(前复权，推荐), "hfq"(后复权), ""(不复权)
    save_dir: 数据保存目录
    sleep_time: 请求间隔时间(秒)，避免被封IP
    merge_to_one_file: 是否合并所有数据到一个文件
    """
    
    # 1. 设置结束日期（默认为今天）
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    
    # 2. 创建保存目录
    os.makedirs(save_dir, exist_ok=True)
    
    # 3. 获取所有A股股票列表 [1,4](@ref)
    print("正在获取A股股票列表...")
    try:
        stock_list_df = ak.stock_info_a_code_name()
        stock_list_df.columns = ["symbol", "name"]
        print(f"共获取到 {len(stock_list_df)} 只A股股票")
        
        # 保存股票列表
        stock_list_df.to_csv(f"{save_dir}/all_a_stocks.csv", index=False, encoding='utf-8-sig')
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        # 备用方法：从文件读取（如果之前已保存）
        if os.path.exists(f"{save_dir}/all_a_stocks.csv"):
            stock_list_df = pd.read_csv(f"{save_dir}/all_a_stocks.csv")
            print(f"从本地文件读取到 {len(stock_list_df)} 只股票")
        else:
            return
    
    # 4. 批量下载日线数据
    print(f"开始下载日线数据 ({start_date} 至 {end_date})...")
    print(f"复权方式: {adjust if adjust else '不复权'}")
    print(f"请求间隔: {sleep_time}秒")
    
    failed_stocks = []  # 记录失败的股票
    all_data_frames = []  # 用于合并所有数据
    
    # 使用进度条
    for idx, row in tqdm(stock_list_df.iterrows(), total=len(stock_list_df), desc="下载进度"):
        symbol = row["symbol"]
        stock_name = row["name"]
        
        # 检查是否已下载（断点续传）
        file_path = f"{save_dir}/{symbol}_{stock_name}.csv"
        
        if os.path.exists(file_path):
            # 如果文件已存在，读取并添加到合并列表
            try:
                existing_df = pd.read_csv(file_path)
                existing_df["symbol"] = symbol
                existing_df["name"] = stock_name
                all_data_frames.append(existing_df)
                continue
            except:
                pass  # 文件损坏，重新下载
        
        try:
            # 获取单只股票日线数据 [2,3](@ref)
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            
            if df is not None and not df.empty:
                # 添加股票代码和名称
                df["symbol"] = symbol
                df["name"] = stock_name
                
                # 重命名列（中英文对照）
                column_mapping = {
                    "日期": "date",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "amount",
                    "振幅": "amplitude",
                    "涨跌幅": "change_pct",
                    "涨跌额": "change_amt",
                    "换手率": "turnover"
                }
                df = df.rename(columns=column_mapping)
                
                # 保存单只股票数据
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                
                # 添加到合并列表
                all_data_frames.append(df)
                
                # 显示进度
                if idx % 100 == 0:
                    print(f"已处理 {idx+1}/{len(stock_list_df)}: {symbol} {stock_name}")
            else:
                failed_stocks.append((symbol, stock_name, "无数据"))
                
        except Exception as e:
            failed_stocks.append((symbol, stock_name, str(e)))
            print(f"股票 {symbol} {stock_name} 下载失败: {e}")
        
        # 礼貌等待，避免请求过快 [3,4](@ref)
        time.sleep(sleep_time)
    
    # 5. 合并所有数据（可选）
    if merge_to_one_file and all_data_frames:
        print("正在合并所有数据...")
        try:
            merged_df = pd.concat(all_data_frames, ignore_index=True)
            
            # 按日期和股票代码排序
            merged_df["date"] = pd.to_datetime(merged_df["date"])
            merged_df = merged_df.sort_values(["date", "symbol"])
            
            # 保存合并文件
            merged_file = f"{save_dir}/all_stocks_daily_{start_date}_{end_date}.csv"
            merged_df.to_csv(merged_file, index=False, encoding='utf-8-sig')
            print(f"所有数据已合并保存到: {merged_file}")
            print(f"合并文件大小: {len(merged_df):,} 行")
        except Exception as e:
            print(f"合并数据失败: {e}")
    
    # 6. 输出统计信息
    print("\n" + "="*50)
    print("下载完成！")
    print(f"成功下载: {len(all_data_frames)} 只股票")
    print(f"失败: {len(failed_stocks)} 只股票")
    
    if failed_stocks:
        print("\n失败的股票列表:")
        for symbol, name, reason in failed_stocks[:10]:  # 只显示前10个
            print(f"  {symbol} {name}: {reason}")
        if len(failed_stocks) > 10:
            print(f"  ... 还有 {len(failed_stocks)-10} 只失败")
        
        # 保存失败列表
        failed_df = pd.DataFrame(failed_stocks, columns=["symbol", "name", "reason"])
        failed_df.to_csv(f"{save_dir}/failed_stocks.csv", index=False, encoding='utf-8-sig')
    
    return all_data_frames

# 7. 使用示例
if __name__ == "__main__":
    # 示例1：获取最近一年的数据（推荐初次使用）
    print("示例1：获取最近一年的数据")
    get_all_a_stock_daily_data(
        start_date="20250101",  # 2025年1月1日开始
        end_date="20251231",    # 2025年12月31日结束
        adjust="qfq",           # 使用前复权（量化分析标准）
        save_dir="stock_data_2025",
        sleep_time=0.8,         # 稍微长一点的间隔
        merge_to_one_file=True  # 合并到一个文件
    )
    
    # 示例2：获取全部历史数据（数据量很大，需要较长时间）
    # print("\n示例2：获取全部历史数据")
    # get_all_a_stock_daily_data(
    #     start_date="19901219",  # A股开市日期
    #     adjust="qfq",
    #     save_dir="stock_data_full",
    #     sleep_time=1.0,         # 更长的间隔避免被封
    #     merge_to_one_file=False # 不合并，每只股票单独文件
    # )