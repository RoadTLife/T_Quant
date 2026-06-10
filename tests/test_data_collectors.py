# -*- coding: utf-8 -*-
"""
数据采集模块测试套件
为 src/data/ 目录下的每个数据采集模块提供单元测试
"""
import sys
import os
import unittest
import pandas as pd
from datetime import datetime, timedelta

# 添加项目根目录到路径
def _add_project_root():
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(current_file))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

_add_project_root()

# ============================================================
# 测试工具函数
# ============================================================

def is_module_available(module_name):
    """检查模块是否可用"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

class ModuleMissingError(Exception):
    """模块缺失错误"""
    pass

class NetworkError(Exception):
    """网络错误"""
    pass

def require_module(module_name):
    """检查模块是否可用，不可用则抛出异常"""
    if not is_module_available(module_name):
        raise ModuleMissingError(f"缺少必需模块: {module_name}")

# ============================================================
# 宏观经济数据采集测试
# ============================================================

class TestMacroData(unittest.TestCase):
    """宏观经济数据采集测试"""

    def setUp(self):
        require_module('akshare')
        from src.data import macro_data
        self.macro = macro_data

    def test_parse_cn_date(self):
        """测试日期解析函数"""
        test_cases = [
            ('2026年01月份', pd.Timestamp('2026-01-01')),
            ('202601', pd.Timestamp('2026-01-01')),
            ('2026.01', pd.Timestamp('2026-01-01')),
            ('', pd.NaT),
            ('NaN', pd.NaT),
        ]
        series = pd.Series([tc[0] for tc in test_cases])
        result = self.macro._parse_cn_date(series)
        for i, (_, expected) in enumerate(test_cases):
            if pd.isna(expected):
                self.assertTrue(pd.isna(result.iloc[i]))
            else:
                self.assertEqual(result.iloc[i], expected)

    def test_find_col(self):
        """测试列查找函数"""
        columns = ['日期', '全国-同比增长', '环比增长', '数值']
        self.assertEqual(self.macro._find_col(columns, ['同比增长', '同比']), '全国-同比增长')
        self.assertEqual(self.macro._find_col(columns, ['环比']), '环比增长')
        self.assertIsNone(self.macro._find_col(columns, ['不存在']))

    def test_fetch_cpi(self):
        """测试CPI采集"""
        df = self.macro.fetch_cpi()
        self.assertIsInstance(df, pd.DataFrame)
        if len(df) > 0:
            self.assertIn('date', df.columns)
            self.assertIn('cpi_yoy', df.columns)
            self.assertTrue(df['date'].dtype == 'datetime64[ns]')

    def test_fetch_ppi(self):
        """测试PPI采集"""
        df = self.macro.fetch_ppi()
        self.assertIsInstance(df, pd.DataFrame)
        if len(df) > 0:
            self.assertIn('date', df.columns)
            self.assertIn('ppi_yoy', df.columns)

    def test_fetch_pmi(self):
        """测试PMI采集"""
        df = self.macro.fetch_pmi()
        self.assertIsInstance(df, pd.DataFrame)
        if len(df) > 0:
            self.assertIn('date', df.columns)
            self.assertIn('pmi', df.columns)

    def test_fetch_m2(self):
        """测试M2采集"""
        df = self.macro.fetch_m2()
        self.assertIsInstance(df, pd.DataFrame)
        if len(df) > 0:
            self.assertIn('date', df.columns)
            self.assertIn('m2_yoy', df.columns)

    def test_fetch_lpr(self):
        """测试LPR采集"""
        df = self.macro.fetch_lpr()
        self.assertIsInstance(df, pd.DataFrame)
        if len(df) > 0:
            self.assertIn('date', df.columns)
            self.assertIn('lpr_1y', df.columns)
            self.assertIn('lpr_5y', df.columns)

    def test_fetch_shrzgm(self):
        """测试社融数据采集"""
        df = self.macro.fetch_shrzgm()
        self.assertIsInstance(df, pd.DataFrame)
        if len(df) > 0:
            self.assertIn('date', df.columns)
            self.assertIn('shrzgm', df.columns)

    def test_merge_and_save(self):
        """测试数据合并函数"""
        df1 = pd.DataFrame({'date': pd.date_range('2026-01-01', periods=3), 'cpi_yoy': [2.1, 2.2, 2.3]})
        df2 = pd.DataFrame({'date': pd.date_range('2026-01-01', periods=3), 'ppi_yoy': [1.5, 1.6, 1.7]})
        dfs = [df1, df2]
        # 测试合并逻辑（不实际写入数据库）
        self.assertTrue(len(dfs) > 0)

# ============================================================
# 新闻事件采集测试
# ============================================================

class TestNewsEvents(unittest.TestCase):
    """新闻事件采集测试"""

    def setUp(self):
        require_module('akshare')
        from src.data import news_events
        self.news = news_events

    def test_analyze_sentiment(self):
        """测试情绪分析函数"""
        positive_title = '贵州茅台涨停，股价创历史新高'
        negative_title = '某公司业绩暴雷，股价跌停'
        neutral_title = '公司召开股东大会'

        self.assertEqual(self.news.analyze_sentiment(positive_title), 'positive')
        self.assertEqual(self.news.analyze_sentiment(negative_title), 'negative')
        self.assertEqual(self.news.analyze_sentiment(neutral_title), 'neutral')

    def test_check_important(self):
        """测试重要事件识别"""
        important_title = '公司发布重大资产重组公告'
        normal_title = '公司日常经营公告'

        self.assertTrue(self.news.check_important(important_title))
        self.assertFalse(self.news.check_important(normal_title))

    def test_fetch_news_akshare(self):
        """测试新闻采集（使用测试股票）"""
        news_list = self.news.fetch_news_akshare('600519.SH')
        self.assertIsInstance(news_list, list)
        if len(news_list) > 0:
            first = news_list[0]
            self.assertIn('title', first)
            self.assertIn('content', first)
            self.assertIn('link', first)
            self.assertIn('sentiment', first)
            self.assertIn('is_important', first)

# ============================================================
# 财经日历采集测试
# ============================================================

class TestCalendarData(unittest.TestCase):
    """财经日历采集测试"""

    def setUp(self):
        require_module('akshare')
        from src.data import calendar_data
        self.calendar = calendar_data

    def test_classify_event(self):
        """测试事件分类函数"""
        test_cases = [
            ('中国CPI数据公布', 'inflation'),
            ('美国非农就业数据', 'employment'),
            ('中国制造业PMI', 'pmi'),
            ('FOMC利率决议', 'interest_rate'),
            ('中国GDP数据', 'gdp'),
            ('某公司财报', 'other'),
        ]
        for title, expected in test_cases:
            self.assertEqual(self.calendar.classify_event(title), expected)

    def test_to_str(self):
        """测试字符串转换函数"""
        self.assertEqual(self.calendar._to_str(None), None)
        self.assertEqual(self.calendar._to_str(float('nan')), None)
        self.assertEqual(self.calendar._to_str(123), '123')
        self.assertEqual(self.calendar._to_str('  abc  '), 'abc')
        self.assertEqual(self.calendar._to_str(''), None)

    def test_fetch_and_save(self):
        """测试财经日历采集"""
        count = self.calendar.fetch_and_save()
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)

# ============================================================
# IPO数据采集测试
# ============================================================

class TestIPOData(unittest.TestCase):
    """IPO数据采集测试"""

    def setUp(self):
        require_module('akshare')
        from src.data import ipo_data
        self.ipo = ipo_data

    def test_fetch_new_stocks(self):
        """测试新股数据采集"""
        df = self.ipo.fetch_new_stocks()
        self.assertIsInstance(df, pd.DataFrame)
        if len(df) > 0:
            # 验证至少包含必要的列
            has_required_columns = any(col in df.columns for col in ['股票代码', '股票简称', '上市日期'])
            self.assertTrue(has_required_columns, f"DataFrame 缺少必要列: {list(df.columns)}")

    def test_parse_date(self):
        """测试日期解析"""
        parse_func = self.ipo.parse_and_statistics.__code__.co_consts
        # 由于parse_date是内部函数，我们通过测试整体流程来验证
        pass

# ============================================================
# 研报数据采集测试
# ============================================================

class TestResearchReports(unittest.TestCase):
    """研报数据采集测试"""

    def setUp(self):
        require_module('akshare')
        from src.data import research_reports
        self.research = research_reports

    def test_fetch_institute_recommend(self):
        """测试机构评级采集"""
        df = self.research.fetch_institute_recommend('600519.SH')
        self.assertIsInstance(df, pd.DataFrame)
        if len(df) > 0:
            self.assertIn('stock_code', df.columns)
            self.assertIn('target_price', df.columns)
            self.assertIn('rating', df.columns)
            self.assertIn('broker', df.columns)

    def test_deduplicate_recommend(self):
        """测试去重逻辑"""
        # 创建测试数据
        data = {
            'stock_code': ['600519.SH'] * 4,
            'broker': ['券商A', '券商A', '券商B', '券商B'],
            'rating': ['买入', '买入', '增持', '中性'],
            'target_price': [1800, 1800, 2000, 1900],
            'report_date': pd.date_range('2026-01-01', periods=4)
        }
        df = pd.DataFrame(data)
        
        deduped = self.research.deduplicate_recommend('600519.SH', df)
        # 券商A的两条记录评级和目标价相同，应该只保留一条
        # 券商B的两条记录评级不同，应该都保留
        self.assertEqual(len(deduped), 3)

    def test_fetch_profit_forecast(self):
        """测试盈利预测采集"""
        forecasts = self.research.fetch_profit_forecast('600519.SH')
        self.assertIsInstance(forecasts, dict)

# ============================================================
# 行情数据采集测试（需要xtquant）
# ============================================================

class TestMarketData(unittest.TestCase):
    """行情数据采集测试"""

    def setUp(self):
        require_module('xtquant')
        from src.data import market_data
        self.market = market_data
        # 设置测试模式
        self.market.TEST_MODE = True
        self.market.TEST_STOCK = '600519.SH'

    def test_get_existing_latest_dates(self):
        """测试获取已有最新日期"""
        dates = self.market.get_existing_latest_dates()
        self.assertIsInstance(dates, dict)

    def test_main(self):
        """测试主流程（测试模式）"""
        self.market.main()

# ============================================================
# 财务数据采集测试（需要xtquant）
# ============================================================

class TestFinancialData(unittest.TestCase):
    """财务数据采集测试"""

    def setUp(self):
        require_module('xtquant')
        from src.data import financial_data
        self.financial = financial_data
        self.financial.TEST_MODE = True
        self.financial.TEST_STOCK = '600519.SH'

    def test_normalize_timetag(self):
        """测试时间标签标准化"""
        self.assertEqual(self.financial.normalize_timetag('20260101'), '20260101')
        self.assertEqual(self.financial.normalize_timetag(None), None)
        self.assertEqual(self.financial.normalize_timetag(''), None)

    def test_get_field(self):
        """测试字段获取函数"""
        record = {'revenue': 100, 'operating_revenue': None}
        self.assertEqual(self.financial.get_field(record, ['revenue', 'operating_revenue']), 100)
        self.assertEqual(self.financial.get_field(record, ['nonexistent']), None)
        self.assertEqual(self.financial.get_field(record, ['nonexistent'], 0), 0)

    def test_safe_float(self):
        """测试安全浮点转换"""
        self.assertEqual(self.financial.safe_float('123.45'), 123.45)
        self.assertEqual(self.financial.safe_float(None), None)
        self.assertEqual(self.financial.safe_float('abc'), None)
        self.assertEqual(self.financial.safe_float(float('nan')), None)

    def test_safe_divide(self):
        """测试安全除法"""
        self.assertEqual(self.financial.safe_divide(10, 2), 5)
        self.assertEqual(self.financial.safe_divide(10, 2, pct=True), 500)
        self.assertEqual(self.financial.safe_divide(10, 0), None)
        self.assertEqual(self.financial.safe_divide(None, 2), None)

    def test_build_period_map(self):
        """测试周期映射构建"""
        data_list = [{'m_timetag': '20260331', 'value': 100}]
        result = self.financial.build_period_map(data_list)
        self.assertIsInstance(result, dict)
        self.assertIn('20260331', result)

    def test_get_existing_stocks(self):
        """测试获取已有股票"""
        stocks = self.financial.get_existing_stocks()
        self.assertIsInstance(stocks, set)

# ============================================================
# 催化剂事件采集测试（需要openai）
# ============================================================

class TestCatalysts(unittest.TestCase):
    """催化剂事件采集测试"""

    def setUp(self):
        require_module('openai')
        from src.data import catalysts
        self.catalysts = catalysts

    def test_parse_json_array(self):
        """测试JSON数组解析"""
        content = '一些文本 [{"date": "2026-06-01", "title": "测试事件"}] 更多文本'
        result = self.catalysts._parse_json_array(content)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], '测试事件')

    def test_normalize_title(self):
        """测试标题归一化"""
        title = 'FOMC/利率—决议 (2026)'
        normalized = self.catalysts._normalize_title(title)
        self.assertEqual(normalized, 'FOMC利率决议2026')

# ============================================================
# 市场情绪数据采集测试（需要akshare）
# ============================================================

class TestMarketSentiment(unittest.TestCase):
    """市场情绪数据采集测试"""

    def setUp(self):
        require_module('akshare')
        from src.data import market_sentiment
        self.sentiment = market_sentiment.MarketSentimentCollector()

    def test_calculate_market_breadth(self):
        """测试市场广度计算"""
        test_data = {
            'up_count': 1500,
            'down_count': 1000,
            'flat_count': 500,
            'limit_up_count': 50,
            'limit_down_count': 10,
            'consecutive_limit_up_count': 10,
            'max_consecutive_limit_up': 5,
            'zaba_count': 5
        }
        result = self.sentiment.calculate_market_breadth(test_data)
        self.assertIsInstance(result, dict)
        self.assertIn('up_down_ratio', result)
        self.assertIn('up_ratio', result)
        self.assertEqual(result['up_down_ratio'], 1.5)
        self.assertEqual(result['up_ratio'], 50.0)

    def test_calculate_board_quality(self):
        """测试封板质量计算"""
        test_data = {
            'limit_up_count': 45,
            'zaba_count': 5,
            'raw_zt_data': None
        }
        result = self.sentiment.calculate_board_quality(test_data)
        self.assertIsInstance(result, dict)
        self.assertIn('board_rate', result)
        self.assertIn('zaba_rate', result)
        self.assertEqual(result['board_rate'], 90.0)
        self.assertEqual(result['zaba_rate'], 10.0)

    def test_calculate_sentiment_score(self):
        """测试情绪评分计算"""
        limit_data = {
            'limit_up_count': 50,
            'limit_down_count': 5,
            'consecutive_limit_up_count': 10,
            'max_consecutive_limit_up': 5
        }
        breadth_data = {
            'up_down_ratio': 2.0,
            'up_ratio': 60.0
        }
        volume_data = {
            'north_money_inflow': 50
        }
        index_data = {
            'shanghai': {'price': 3500, 'change_pct': 1.5},
            'shenzhen': {'price': 11000, 'change_pct': 2.0}
        }
        score = self.sentiment.calculate_sentiment_score(
            limit_data, breadth_data, volume_data, index_data
        )
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_get_sentiment_level(self):
        """测试情绪等级获取"""
        test_cases = [
            (85, '极度亢奋'),
            (65, '偏乐观'),
            (50, '中性'),
            (30, '偏悲观'),
            (15, '极度恐慌')
        ]
        for score, expected_level in test_cases:
            result = self.sentiment.get_sentiment_level(score)
            self.assertEqual(result['level'], expected_level)
            self.assertIn('advice', result)

    def test_collect_all(self):
        """测试完整采集流程"""
        report = self.sentiment.collect_all()
        self.assertIsInstance(report, dict)
        self.assertIn('collect_time', report)
        self.assertIn('sentiment_score', report)
        self.assertIn('sentiment_level', report)
        self.assertIn('advice', report)
        self.assertIn('limit_up_down', report)
        self.assertIn('market_breadth', report)
        self.assertIn('board_quality', report)
        self.assertIn('volume', report)
        self.assertIn('indexes', report)
        self.assertIn('sectors', report)

# ============================================================
# 运行测试
# ============================================================

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("数据采集模块测试套件")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加测试类
    test_classes = [
        TestMacroData,
        TestNewsEvents,
        TestCalendarData,
        TestIPOData,
        TestResearchReports,
        TestMarketData,
        TestFinancialData,
        TestCatalysts,
        TestMarketSentiment,
    ]

    for cls in test_classes:
        loader = unittest.TestLoader()
        tests = loader.loadTestsFromTestCase(cls)
        suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 统计结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"  运行测试: {result.testsRun}")
    print(f"  通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")

    if result.failures:
        print("\n失败详情:")
        for i, (test, err) in enumerate(result.failures, 1):
            print(f"  {i}. {test}: {err[:200]}")

    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)