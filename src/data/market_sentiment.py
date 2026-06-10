# -*- coding: utf-8 -*-
"""
市场情绪核心指标采集模块

根据文档需求采集以下指标：
1. 涨跌停数据（涨停家数、跌停家数、涨停金额、跌停金额、连板股票数、最高连板数）
2. 涨跌家数对比（上涨家数、下跌家数、平盘家数、涨跌比、上涨比例）
3. 封板质量指标（封板率、炸板率、封单金额、封单量）
4. 量能指标（集合竞价成交量、成交额、量比、资金流入额）

数据源(AkShare):
- stock_zt_pool_em(): 涨停池
- stock_zt_pool_zbgc_em(): 炸板股池
- stock_hot_up_em(): 上涨家数统计
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


class MarketSentimentCollector:
    """市场情绪数据采集器"""
    
    def __init__(self):
        self.data = {}
    
    def fetch_limit_up_down_data(self):
        """
        采集涨跌停数据
        返回: 包含涨停和跌停信息的字典
        """
        try:
            # 获取涨停池数据
            zt_df = ak.stock_zt_pool_em()
            
            # 获取炸板股池数据
            zbgc_df = ak.stock_zt_pool_zbgc_em()
            
            # 获取上涨家数统计
            hot_up_df = ak.stock_hot_up_em()
            
            # 提取涨停数据
            limit_up_count = len(zt_df) if not zt_df.empty else 0
            limit_up_amount = zt_df['最新价'].sum() * zt_df['流通市值'].sum() / 10000 if not zt_df.empty else 0
            
            # 提取连板数据
            consecutive_limit_up = zt_df[zt_df['连板数'] >= 2]
            consecutive_count = len(consecutive_limit_up) if not consecutive_limit_up.empty else 0
            max_consecutive = zt_df['连板数'].max() if not zt_df.empty else 0
            
            # 提取炸板数据
            zaba_count = len(zbgc_df) if not zbgc_df.empty else 0
            
            # 提取涨跌家数
            up_count = hot_up_df['上涨家数'].iloc[0] if not hot_up_df.empty else 0
            down_count = hot_up_df['下跌家数'].iloc[0] if not hot_up_df.empty else 0
            flat_count = hot_up_df['平盘家数'].iloc[0] if not hot_up_df.empty else 0
            
            return {
                'limit_up_count': limit_up_count,           # 涨停家数
                'limit_up_amount': limit_up_amount,         # 涨停金额
                'limit_down_count': 0,                      # 跌停家数（需其他接口）
                'limit_down_amount': 0,                     # 跌停金额
                'consecutive_limit_up_count': consecutive_count,  # 连板股票数
                'max_consecutive_limit_up': max_consecutive,       # 最高连板数
                'up_count': up_count,                      # 上涨家数
                'down_count': down_count,                  # 下跌家数
                'flat_count': flat_count,                  # 平盘家数
                'zaba_count': zaba_count,                  # 炸板数
                'raw_zt_data': zt_df,
                'raw_zbgc_data': zbgc_df,
                'raw_hot_up_data': hot_up_df
            }
        except Exception as e:
            print(f"采集涨跌停数据失败: {e}")
            return {
                'limit_up_count': 0,
                'limit_up_amount': 0,
                'limit_down_count': 0,
                'limit_down_amount': 0,
                'consecutive_limit_up_count': 0,
                'max_consecutive_limit_up': 0,
                'up_count': 0,
                'down_count': 0,
                'flat_count': 0,
                'zaba_count': 0,
                'raw_zt_data': None,
                'raw_zbgc_data': None,
                'raw_hot_up_data': None
            }
    
    def calculate_market_breadth(self, data):
        """
        计算市场广度指标
        :param data: fetch_limit_up_down_data 返回的数据
        """
        up_count = data.get('up_count', 0)
        down_count = data.get('down_count', 0)
        flat_count = data.get('flat_count', 0)
        total_count = up_count + down_count + flat_count
        
        # 涨跌比
        up_down_ratio = up_count / down_count if down_count > 0 else 0
        
        # 上涨比例
        up_ratio = up_count / total_count if total_count > 0 else 0
        
        return {
            'up_down_ratio': round(up_down_ratio, 2),     # 涨跌比
            'up_ratio': round(up_ratio * 100, 2),         # 上涨比例(%)
            'total_count': total_count                    # 总家数
        }
    
    def calculate_board_quality(self, data):
        """
        计算封板质量指标
        :param data: fetch_limit_up_down_data 返回的数据
        """
        limit_up_count = data.get('limit_up_count', 0)
        zaba_count = data.get('zaba_count', 0)
        ever_limit_up_count = limit_up_count + zaba_count
        
        # 封板率 = 最终封板数 / 曾涨停数
        board_rate = limit_up_count / ever_limit_up_count if ever_limit_up_count > 0 else 0
        
        # 炸板率 = 炸板数 / 曾涨停数
        zaba_rate = zaba_count / ever_limit_up_count if ever_limit_up_count > 0 else 0
        
        # 估算封单金额和封单量（需要更详细的数据）
        zt_df = data.get('raw_zt_data')
        if zt_df is not None and not zt_df.empty:
            # 假设封单金额约等于涨停价 * 封单量（估算）
            estimated_order_amount = zt_df['最新价'].sum() * 1000  # 估算值
            estimated_order_volume = len(zt_df) * 1000             # 估算值
        else:
            estimated_order_amount = 0
            estimated_order_volume = 0
        
        return {
            'board_rate': round(board_rate * 100, 2),        # 封板率(%)
            'zaba_rate': round(zaba_rate * 100, 2),          # 炸板率(%)
            'order_amount': estimated_order_amount,          # 封单金额
            'order_volume': estimated_order_volume           # 封单量
        }
    
    def fetch_volume_data(self):
        """
        采集量能指标（需要实时行情接口支持）
        """
        try:
            # 北向资金数据
            north_money_df = ak.stock_hsgt_north_net_flow_em()
            
            north_inflow = 0
            if not north_money_df.empty:
                north_inflow = north_money_df['北向资金净流入'].iloc[-1] if '北向资金净流入' in north_money_df.columns else 0
            
            return {
                'north_money_inflow': north_inflow,          # 北向资金净流入
                'settle_volume': 0,                          # 集合竞价成交量（需要实时接口）
                'settle_amount': 0,                          # 集合竞价成交额
                'volume_ratio': 0                            # 量比（需要实时接口）
            }
        except Exception as e:
            print(f"采集量能数据失败: {e}")
            return {
                'north_money_inflow': 0,
                'settle_volume': 0,
                'settle_amount': 0,
                'volume_ratio': 0
            }
    
    def fetch_a_share_indexes(self):
        """
        采集A股主要指数数据
        """
        try:
            # 获取上证指数
            sh_df = ak.stock_zh_index_daily(symbol="sh000001")
            # 获取深证成指
            sz_df = ak.stock_zh_index_daily(symbol="sz399001")
            # 获取创业板指
            cyb_df = ak.stock_zh_index_daily(symbol="sz399006")
            # 获取科创50
            kc_df = ak.stock_zh_index_daily(symbol="sh000688")
            # 获取沪深300
            hs300_df = ak.stock_zh_index_daily(symbol="sh000300")
            
            def get_last_price_change(df):
                if df is None or df.empty or len(df) < 2:
                    return {'price': 0, 'change': 0, 'change_pct': 0}
                last_row = df.iloc[-1]
                prev_row = df.iloc[-2]
                price = last_row['close']
                change = price - prev_row['close']
                change_pct = (change / prev_row['close']) * 100
                return {
                    'price': round(price, 2),
                    'change': round(change, 2),
                    'change_pct': round(change_pct, 2)
                }
            
            return {
                'shanghai': get_last_price_change(sh_df),     # 上证指数
                'shenzhen': get_last_price_change(sz_df),     # 深证成指
                'chuangye': get_last_price_change(cyb_df),    # 创业板指
                'kechuang': get_last_price_change(kc_df),     # 科创50
                'hs300': get_last_price_change(hs300_df)      # 沪深300
            }
        except Exception as e:
            print(f"采集指数数据失败: {e}")
            return {
                'shanghai': {'price': 0, 'change': 0, 'change_pct': 0},
                'shenzhen': {'price': 0, 'change': 0, 'change_pct': 0},
                'chuangye': {'price': 0, 'change': 0, 'change_pct': 0},
                'kechuang': {'price': 0, 'change': 0, 'change_pct': 0},
                'hs300': {'price': 0, 'change': 0, 'change_pct': 0}
            }
    
    def fetch_hot_sectors(self):
        """
        采集热点板块数据
        """
        try:
            # 获取板块涨幅榜
            sector_df = ak.stock_sector_index_em()
            
            if sector_df.empty:
                return {'top_sectors': [], 'bottom_sectors': [], 'sector_funds': []}
            
            # 领涨板块（涨幅前5）
            top_sectors = sector_df.sort_values('涨跌幅', ascending=False).head(5)
            top_list = []
            for _, row in top_sectors.iterrows():
                top_list.append({
                    'name': row.get('名称', ''),
                    'change': row.get('涨跌幅', 0),
                    'volume': row.get('成交量', 0),
                    'amount': row.get('成交额', 0)
                })
            
            # 领跌板块（涨幅后5）
            bottom_sectors = sector_df.sort_values('涨跌幅', ascending=True).head(5)
            bottom_list = []
            for _, row in bottom_sectors.iterrows():
                bottom_list.append({
                    'name': row.get('名称', ''),
                    'change': row.get('涨跌幅', 0),
                    'volume': row.get('成交量', 0),
                    'amount': row.get('成交额', 0)
                })
            
            return {
                'top_sectors': top_list,      # 领涨板块
                'bottom_sectors': bottom_list, # 领跌板块
                'sector_funds': []            # 板块资金流向（需要其他接口）
            }
        except Exception as e:
            print(f"采集热点板块数据失败: {e}")
            return {'top_sectors': [], 'bottom_sectors': [], 'sector_funds': []}
    
    def calculate_sentiment_score(self, limit_data, breadth_data, volume_data, index_data):
        """
        计算综合情绪评分（0-100分）
        :param limit_data: 涨跌停数据
        :param breadth_data: 市场广度数据
        :param volume_data: 量能数据
        :param index_data: 指数数据
        """
        score = 0
        
        # 涨跌停情绪（30%权重）
        limit_up_count = limit_data.get('limit_up_count', 0)
        limit_down_count = limit_data.get('limit_down_count', 0)
        consecutive_count = limit_data.get('consecutive_limit_up_count', 0)
        board_rate = breadth_data.get('board_rate', 0)
        
        # 涨停得分（最多30分）
        limit_score = min(limit_up_count * 0.5, 15)  # 涨停家数得分
        limit_score += min(consecutive_count * 1, 10)  # 连板数得分
        limit_score += board_rate * 0.05  # 封板率得分
        limit_score = min(limit_score, 30)
        
        # 市场广度（25%权重）
        up_down_ratio = breadth_data.get('up_down_ratio', 0)
        up_ratio = breadth_data.get('up_ratio', 0)
        
        breadth_score = min(up_down_ratio * 10, 15)  # 涨跌比得分
        breadth_score += up_ratio * 0.1  # 上涨比例得分
        breadth_score = min(breadth_score, 25)
        
        # 指数表现（20%权重）
        sh_change = index_data.get('shanghai', {}).get('change_pct', 0)
        sz_change = index_data.get('shenzhen', {}).get('change_pct', 0)
        avg_change = (sh_change + sz_change) / 2
        
        index_score = max(-20, min(avg_change * 2, 20)) + 10  # 转换为0-20分
        
        # 资金流向（15%权重）
        north_inflow = volume_data.get('north_money_inflow', 0)
        
        fund_score = min(north_inflow / 10, 15) if north_inflow > 0 else 0
        fund_score = max(fund_score, 0)
        
        # 海外影响（10%权重）- 暂时使用A50期货替代
        a50_score = 5  # 默认中性
        
        # 综合得分
        score = limit_score + breadth_score + index_score + fund_score + a50_score
        score = max(0, min(100, round(score, 2)))
        
        return score
    
    def get_sentiment_level(self, score):
        """
        根据评分获取情绪等级
        :param score: 综合情绪评分
        """
        if score >= 80:
            return {'level': '极度亢奋', 'advice': '谨慎追高，注意回调风险'}
        elif score >= 60:
            return {'level': '偏乐观', 'advice': '可适度参与强势板块'}
        elif score >= 40:
            return {'level': '中性', 'advice': '观望为主，等待明确信号'}
        elif score >= 20:
            return {'level': '偏悲观', 'advice': '控制仓位，防御为主'}
        else:
            return {'level': '极度恐慌', 'advice': '关注超跌机会，分批低吸'}
    
    def collect_all(self):
        """
        采集所有市场情绪指标并生成综合报告
        """
        # 采集各类数据
        limit_data = self.fetch_limit_up_down_data()
        breadth_data = self.calculate_market_breadth(limit_data)
        board_quality_data = self.calculate_board_quality(limit_data)
        volume_data = self.fetch_volume_data()
        index_data = self.fetch_a_share_indexes()
        sector_data = self.fetch_hot_sectors()
        
        # 计算综合评分
        sentiment_score = self.calculate_sentiment_score(
            limit_data, breadth_data, volume_data, index_data
        )
        sentiment_level = self.get_sentiment_level(sentiment_score)
        
        # 构建综合报告
        report = {
            'collect_time': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sentiment_score': sentiment_score,
            'sentiment_level': sentiment_level['level'],
            'advice': sentiment_level['advice'],
            
            # 涨跌停数据
            'limit_up_down': {
                'limit_up_count': limit_data.get('limit_up_count', 0),
                'limit_up_amount': limit_data.get('limit_up_amount', 0),
                'limit_down_count': limit_data.get('limit_down_count', 0),
                'limit_down_amount': limit_data.get('limit_down_amount', 0),
                'consecutive_limit_up_count': limit_data.get('consecutive_limit_up_count', 0),
                'max_consecutive_limit_up': limit_data.get('max_consecutive_limit_up', 0)
            },
            
            # 市场广度
            'market_breadth': {
                'up_count': limit_data.get('up_count', 0),
                'down_count': limit_data.get('down_count', 0),
                'flat_count': limit_data.get('flat_count', 0),
                'up_down_ratio': breadth_data.get('up_down_ratio', 0),
                'up_ratio': breadth_data.get('up_ratio', 0)
            },
            
            # 封板质量
            'board_quality': {
                'board_rate': board_quality_data.get('board_rate', 0),
                'zaba_rate': board_quality_data.get('zaba_rate', 0),
                'order_amount': board_quality_data.get('order_amount', 0),
                'order_volume': board_quality_data.get('order_volume', 0)
            },
            
            # 量能指标
            'volume': volume_data,
            
            # 指数数据
            'indexes': index_data,
            
            # 板块数据
            'sectors': sector_data
        }
        
        return report
    
    def save_to_db(self, report):
        """
        将情绪报告保存到数据库
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # 创建表（如果不存在）
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS trade_market_sentiment (
                id INT AUTO_INCREMENT PRIMARY KEY,
                collect_time DATETIME NOT NULL,
                sentiment_score DECIMAL(5,2) NOT NULL,
                sentiment_level VARCHAR(20) NOT NULL,
                advice TEXT,
                limit_up_count INT DEFAULT 0,
                limit_down_count INT DEFAULT 0,
                consecutive_limit_up_count INT DEFAULT 0,
                max_consecutive_limit_up INT DEFAULT 0,
                up_count INT DEFAULT 0,
                down_count INT DEFAULT 0,
                up_down_ratio DECIMAL(5,2) DEFAULT 0,
                up_ratio DECIMAL(5,2) DEFAULT 0,
                board_rate DECIMAL(5,2) DEFAULT 0,
                zaba_rate DECIMAL(5,2) DEFAULT 0,
                north_money_inflow DECIMAL(15,2) DEFAULT 0,
                shanghai_price DECIMAL(10,2) DEFAULT 0,
                shanghai_change_pct DECIMAL(5,2) DEFAULT 0,
                shenzhen_price DECIMAL(10,2) DEFAULT 0,
                shenzhen_change_pct DECIMAL(5,2) DEFAULT 0,
                chuangye_price DECIMAL(10,2) DEFAULT 0,
                chuangye_change_pct DECIMAL(5,2) DEFAULT 0,
                hs300_price DECIMAL(10,2) DEFAULT 0,
                hs300_change_pct DECIMAL(5,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            cursor.execute(create_table_sql)
            
            # 插入数据
            insert_sql = """
            INSERT INTO trade_market_sentiment (
                collect_time, sentiment_score, sentiment_level, advice,
                limit_up_count, limit_down_count, consecutive_limit_up_count,
                max_consecutive_limit_up, up_count, down_count, up_down_ratio,
                up_ratio, board_rate, zaba_rate, north_money_inflow,
                shanghai_price, shanghai_change_pct, shenzhen_price,
                shenzhen_change_pct, chuangye_price, chuangye_change_pct,
                hs300_price, hs300_change_pct
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                report['collect_time'],
                report['sentiment_score'],
                report['sentiment_level'],
                report['advice'],
                report['limit_up_down']['limit_up_count'],
                report['limit_up_down']['limit_down_count'],
                report['limit_up_down']['consecutive_limit_up_count'],
                report['limit_up_down']['max_consecutive_limit_up'],
                report['market_breadth']['up_count'],
                report['market_breadth']['down_count'],
                report['market_breadth']['up_down_ratio'],
                report['market_breadth']['up_ratio'],
                report['board_quality']['board_rate'],
                report['board_quality']['zaba_rate'],
                report['volume']['north_money_inflow'],
                report['indexes']['shanghai']['price'],
                report['indexes']['shanghai']['change_pct'],
                report['indexes']['shenzhen']['price'],
                report['indexes']['shenzhen']['change_pct'],
                report['indexes']['chuangye']['price'],
                report['indexes']['chuangye']['change_pct'],
                report['indexes']['hs300']['price'],
                report['indexes']['hs300']['change_pct']
            )
            
            cursor.execute(insert_sql, params)
            conn.commit()
            print(f"情绪数据已保存到数据库，ID: {cursor.lastrowid}")
            
        except Exception as e:
            print(f"保存数据失败: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    def generate_text_report(self, report):
        """
        生成文本格式的情绪报告
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"市场情绪报告 - {report['collect_time']}")
        lines.append("=" * 60)
        lines.append("")
        
        # 综合评分
        lines.append(f"【综合情绪评分】: {report['sentiment_score']} 分")
        lines.append(f"【情绪等级】: {report['sentiment_level']}")
        lines.append(f"【操作建议】: {report['advice']}")
        lines.append("")
        
        # 涨跌停数据
        lines.append("一、涨跌停数据")
        lines.append(f"  涨停家数: {report['limit_up_down']['limit_up_count']}")
        lines.append(f"  跌停家数: {report['limit_up_down']['limit_down_count']}")
        lines.append(f"  连板股票数: {report['limit_up_down']['consecutive_limit_up_count']}")
        lines.append(f"  最高连板数: {report['limit_up_down']['max_consecutive_limit_up']}")
        lines.append("")
        
        # 市场广度
        lines.append("二、市场广度")
        lines.append(f"  上涨家数: {report['market_breadth']['up_count']}")
        lines.append(f"  下跌家数: {report['market_breadth']['down_count']}")
        lines.append(f"  涨跌比: {report['market_breadth']['up_down_ratio']}")
        lines.append(f"  上涨比例: {report['market_breadth']['up_ratio']}%")
        lines.append("")
        
        # 封板质量
        lines.append("三、封板质量")
        lines.append(f"  封板率: {report['board_quality']['board_rate']}%")
        lines.append(f"  炸板率: {report['board_quality']['zaba_rate']}%")
        lines.append("")
        
        # 量能指标
        lines.append("四、量能指标")
        lines.append(f"  北向资金净流入: {report['volume']['north_money_inflow']:.2f} 亿元")
        lines.append("")
        
        # 指数表现
        lines.append("五、指数表现")
        lines.append(f"  上证指数: {report['indexes']['shanghai']['price']} ({report['indexes']['shanghai']['change_pct']}%)")
        lines.append(f"  深证成指: {report['indexes']['shenzhen']['price']} ({report['indexes']['shenzhen']['change_pct']}%)")
        lines.append(f"  创业板指: {report['indexes']['chuangye']['price']} ({report['indexes']['chuangye']['change_pct']}%)")
        lines.append(f"  沪深300: {report['indexes']['hs300']['price']} ({report['indexes']['hs300']['change_pct']}%)")
        lines.append("")
        
        # 热点板块
        lines.append("六、热点板块")
        lines.append("  领涨板块:")
        for sector in report['sectors']['top_sectors'][:3]:
            lines.append(f"    - {sector['name']}: {sector['change']}%")
        lines.append("  领跌板块:")
        for sector in report['sectors']['bottom_sectors'][:3]:
            lines.append(f"    - {sector['name']}: {sector['change']}%")
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)


# 模块级函数供外部调用
def fetch_market_sentiment():
    """采集市场情绪数据"""
    collector = MarketSentimentCollector()
    return collector.collect_all()

def save_market_sentiment():
    """采集并保存市场情绪数据"""
    collector = MarketSentimentCollector()
    report = collector.collect_all()
    collector.save_to_db(report)
    return report

def generate_sentiment_report():
    """生成市场情绪报告"""
    collector = MarketSentimentCollector()
    report = collector.collect_all()
    return collector.generate_text_report(report)


if __name__ == "__main__":
    # 测试采集功能
    collector = MarketSentimentCollector()
    report = collector.collect_all()
    
    # 打印文本报告
    print(collector.generate_text_report(report))
    
    # 保存到数据库
    # collector.save_to_db(report)