# 数据采集模块文档

## 概述

本文档介绍 `src/data/` 目录下所有数据采集模块的功能、数据特点、存储目标及建议的定时任务执行时间。

---

## 模块总览

| 模块名称 | 文件 | 功能描述 | 数据源 | 更新频率 | 建议执行时间 |
|---------|------|---------|--------|---------|------------|
| 行情数据 | `market_data.py` | A股日线行情数据 | MiniQMT | 交易日增量 | 交易日 16:30 |
| 财务数据 | `financial_data.py` | 财务报表指标 | MiniQMT | 季度 | 交易日 17:00 或周末 |
| 宏观数据 | `macro_data.py` | CPI/PPI/PMI等宏观指标 | AkShare | 月频 | 每月10日 09:00 |
| IPO数据 | `ipo_data.py` | 新股发行数据 | AkShare | 周频 | 每周一 09:30 |
| 新闻事件 | `news_events.py` | 个股新闻事件 | AkShare | 日频 | 交易日 16:00 |
| 研报数据 | `research_reports.py` | 机构评级/盈利预测 | AkShare | 周频 | 每周一 10:00 |
| 财经日历 | `calendar_data.py` | 全球经济事件 | AkShare | 日频 | 每日 08:00 |
| 催化剂事件 | `catalysts.py` | AI搜索催化剂事件 | Qwen Max API | 周频 | 每周一 08:30 |
| 市场情绪 | `market_sentiment.py` | 涨跌停/情绪指标 | AkShare | 日频 | 交易日 15:30 |

---

## 1. 行情数据采集 (market_data.py)

### 功能描述
使用 MiniQMT (xtquant) 连接本地QMT交易终端，采集沪深A股全量股票的日线行情数据。

### 采集指标
- **基础行情**：开盘价、最高价、最低价、收盘价
- **成交量**：成交量、成交额
- **换手率**：基于流通股本计算的换手率

### 数据存储
- **表名**：`trade_stock_daily`
- **字段**：stock_code, trade_date, open_price, high_price, low_price, close_price, volume, amount, turnover_rate

### 数据特点
- **数据量**：约5000只股票，每日约5000条记录
- **时效性**：T日收盘后更新
- **增量更新**：仅下载数据库中不存在的最新日期数据

### 定时任务配置
```yaml
market_data:
  module: "market_data"
  function: "main"
  cron: "0 16 * * 1-5"  # 每周一至周五 16:30
  description: "A股日线行情数据采集"
  priority: 1
  dependencies: []
```

---

## 2. 财务数据采集 (financial_data.py)

### 功能描述
使用 MiniQMT (xtquant) 采集A股全量股票的财务数据，包括资产负债表、利润表、现金流量表等。

### 采集指标
- **盈利能力**：营业收入、净利润、EPS、ROE、ROA
- **毛利率/净利率**：销售毛利率、净利润率
- **偿债能力**：资产负债率、流动比率
- **现金流**：经营活动现金流
- **资产规模**：总资产、总权益

### 数据存储
- **表名**：`trade_stock_financial`
- **字段**：stock_code, report_date, revenue, net_profit, eps, roe, roa, gross_margin, net_margin, debt_ratio, current_ratio, operating_cashflow, total_assets, total_equity

### 数据特点
- **数据频率**：季度报告，每年4次（4月、8月、10月、年报）
- **批量下载**：每批50只股票，提高下载效率
- **断点续传**：跳过已采集的股票，重启后可继续

### 定时任务配置
```yaml
financial_data:
  module: "financial_data"
  function: "main"
  cron: "0 17 * * 1-5"  # 每周一至周五 17:00
  description: "A股财务数据采集"
  priority: 2
  dependencies: ["market_data"]
  # 或者周末执行
  # cron: "0 10 * * 6-7"
```

---

## 3. 宏观数据采集 (macro_data.py)

### 功能描述
使用 AkShare 采集宏观经济指标，包括通胀、景气、流动性、利率等多维度数据。

### 采集指标
| 类别 | 指标 | 说明 |
|-----|------|------|
| 通胀指标 | CPI同比、PPI同比 | 反映物价水平变化 |
| 景气指标 | PMI(制造业) | 反映经济景气度 |
| 流动性 | M2同比、社融规模增量 | 反映货币供应和信用派生 |
| 利率 | LPR(1年/5年)、10年期国债收益率 | 反映利率水平，中美利差 |

### 数据存储
- **表名**：`trade_macro_indicator`（月度指标）
- **表名**：`trade_rate_daily`（日频利率）
- **字段**：
  - trade_macro_indicator: indicator_date, cpi_yoy, ppi_yoy, pmi, m2_yoy, shrzgm, lpr_1y, lpr_5y
  - trade_rate_daily: rate_date, cn_bond_10y, us_bond_10y

### 数据特点
- **发布规律**：CPI/PPI每月9-12日发布，PMI每月最后一天发布
- **历史数据**：CPI/PPI可追溯至2006年
- **时区注意**：部分数据为美东时间发布

### 定时任务配置
```yaml
macro_data:
  module: "macro_data"
  function: "main"
  cron: "0 9 10-15 * *"  # 每月10-15日 09:00
  description: "宏观经济数据采集"
  priority: 3
  dependencies: []
  notes: "月初数据发布后采集"
```

---

## 4. IPO数据采集 (ipo_data.py)

### 功能描述
使用 AkShare 采集A股新股发行数据，包括发行价、发行PE、募集资金、上市日期等。

### 采集指标
- **基本信息**：股票代码、股票简称、上市日期、申购日期
- **发行信息**：发行价、发行数量、发行PE、上网发行中签率
- **融资信息**：拟融资额、募集资金
- **审核信息**：审核状态、主承销商、保荐机构、上市板块

### 数据存储
- **表名**：`trade_stock_ipo_detail`（原始详情）
- **表名**：`trade_stock_ipo`（月度统计）
- **字段**：
  - trade_stock_ipo_detail: stock_code, stock_name, listed_date, issue_price, issue_volume, issue_pe, subscription_rate, financing_amount
  - trade_stock_ipo: ipo_month, ipo_count, total_amount, avg_amount, max_amount

### 数据特点
- **数据源**：东方财富、同花顺（备用接口）
- **历史数据**：可追溯至2006年
- **更新频率**：每周有新的IPO数据

### 定时任务配置
```yaml
ipo_data:
  module: "ipo_data"
  function: "main"
  cron: "0 9 * * 1"  # 每周一 09:30
  description: "新股发行数据采集"
  priority: 4
  dependencies: []
```

---

## 5. 新闻事件采集 (news_events.py)

### 功能描述
使用 AkShare 采集全量A股个股新闻事件，进行情感分析和重要性标注。

### 采集指标
- **基础信息**：新闻标题、内容、发布时间、来源
- **情感分析**：正面/负面/中性
- **重要性标注**：是否包含重大事件关键词

### 关键词分类
| 类型 | 关键词 |
|-----|--------|
| 正面 | 涨停、大涨、利好、增长、突破、新高、预增、增持、盈利 |
| 负面 | 跌停、大跌、利空、下降、跌破、新低、预减、减持、亏损 |
| 重要 | 资产重组、业绩预增/预减、高送转、股权激励、定向增发、回购 |

### 数据存储
- **表名**：`trade_stock_news`
- **字段**：stock_code, news_type, title, content, source, sentiment, is_important, published_at

### 数据特点
- **全量覆盖**：覆盖trade_stock_basic表中的所有股票
- **去重机制**：基于标题去重，批量预加载已有标题到内存
- **当日跳过**：当日已采集的股票自动跳过

### 定时任务配置
```yaml
news_events:
  module: "news_events"
  function: "main"
  cron: "0 16 * * 1-5"  # 每周一至周五 16:00
  description: "个股新闻事件采集"
  priority: 5
  dependencies: ["market_data"]
```

---

## 6. 研报数据采集 (research_reports.py)

### 功能描述
使用 AkShare 采集机构研报数据，包括东方财富机构评级明细和同花顺盈利预测。

### 采集指标
- **机构评级**：券商名称、评级、目标价、分析师、报告日期
- **盈利预测**：一致预期EPS、一致预期净利润、分析师数量

### 智能去重策略
- 同一券商对同一股票的多次评级记录，只保留"观点变化"时的记录
- 按时间从旧到新遍历，评级或目标价变化时才写入

### 数据存储
- **表名**：`trade_report_consensus`
- **字段**：stock_code, broker, report_date, rating, target_price, eps_forecast_current, eps_forecast_next, revenue_forecast

### 数据特点
- **双数据源**：东方财富(评级) + 同花顺(盈利预测)
- **7天跳过**：近7天已采集的股票自动跳过
- **周频更新**：机构通常周末发布研报

### 定时任务配置
```yaml
research_reports:
  module: "research_reports"
  function: "main"
  cron: "0 10 * * 1"  # 每周一 10:00
  description: "研报数据采集(机构评级/盈利预测)"
  priority: 6
  dependencies: ["market_data"]
```

---

## 7. 财经日历采集 (calendar_data.py)

### 功能描述
使用 AkShare (百度财经日历) 采集全球重要经济事件日历。

### 采集指标
| 字段 | 说明 |
|-----|------|
| event_date | 事件日期 |
| event_time | 事件时间 |
| title | 事件标题 |
| country | 涉及国家 |
| category | 事件类别 |
| importance | 重要性等级 |
| forecast_value | 预期值 |
| actual_value | 实际值 |
| previous_value | 前值 |

### 事件类别
- interest_rate：利率决议（FOMC、LPR等）
- inflation：通胀数据（CPI、PPI）
- employment：就业数据（非农、ADP）
- pmi：采购经理指数
- gdp：国内生产总值
- trade：贸易数据
- monetary：货币供应
- housing：房地产数据
- retail：零售数据
- industry：工业产出

### 数据存储
- **表名**：`trade_calendar_event`
- **字段**：event_date, event_time, title, country, category, importance, forecast_value, actual_value, previous_value

### 数据特点
- **覆盖范围**：中国、美国、欧元区、日本、英国
- **时间跨度**：前7天到后30天
- **日频更新**：每天更新一次

### 定时任务配置
```yaml
calendar_data:
  module: "calendar_data"
  function: "main"
  cron: "0 8 * * *"  # 每天 08:00
  description: "财经日历采集"
  priority: 7
  dependencies: []
```

---

## 8. 催化剂事件采集 (catalysts.py)

### 功能描述
使用 Qwen Max API 联网搜索未来6个月对A股有重大影响的催化剂事件。

### 采集指标
- **事件信息**：日期、标题、国家、类别
- **重要性**：1-3星评级
- **AI提示词**：用于后续AI分析

### 数据源
- **AI模型**：通义千问 Max (Qwen Max)
- **联网搜索**：启用搜索增强

### 数据存储
- **表名**：`trade_calendar_event`（与财经日历共用，source='qwen_search'）
- **字段**：event_date, title, country, category, importance, source, ai_prompt

### 数据特点
- **AI驱动**：使用大模型联网搜索，比规则更全面
- **未来预测**：覆盖未来6个月
- **周频更新**：每周更新一次

### 定时任务配置
```yaml
catalysts:
  module: "catalysts"
  function: "main"
  cron: "0 8 10 * 1"  # 每月10日及每周一 08:30
  description: "催化剂事件AI搜索"
  priority: 8
  dependencies: ["calendar_data"]
  requires_api: true
  api_config: "dashscope"
```

---

## 9. 市场情绪采集 (market_sentiment.py)

### 功能描述
采集每日市场情绪核心指标，包括涨跌停、市场广度、封板质量等多维度数据。

### 采集指标

#### 涨跌停数据
| 指标 | 说明 |
|-----|------|
| limit_up_count | 涨停家数 |
| limit_down_count | 跌停家数 |
| limit_up_amount | 涨停金额 |
| consecutive_limit_up_count | 连板股票数 |
| max_consecutive_limit_up | 最高连板数 |

#### 市场广度
| 指标 | 说明 |
|-----|------|
| up_count | 上涨家数 |
| down_count | 下跌家数 |
| flat_count | 平盘家数 |
| up_down_ratio | 涨跌比 |
| up_ratio | 上涨比例(%) |

#### 封板质量
| 指标 | 说明 |
|-----|------|
| board_rate | 封板率(%) |
| zaba_rate | 炸板率(%) |
| order_amount | 封单金额 |
| order_volume | 封单量 |

#### 指数数据
- 上证指数、深证成指、创业板指、科创50、沪深300

#### 情绪评分
- 综合评分(0-100)：基于涨停情绪(30%)、市场广度(25%)、指数表现(20%)、资金流向(15%)、海外影响(10%)

### 数据存储
- **表名**：`trade_market_sentiment`
- **字段**：collect_time, sentiment_score, sentiment_level, limit_up_count, up_count, down_count, board_rate, 等

### 定时任务配置
```yaml
market_sentiment:
  module: "market_sentiment"
  function: "collect_all"
  cron: "0 15 * * 1-5"  # 每周一至周五 15:30
  description: "市场情绪指标采集"
  priority: 9
  dependencies: []
```

---

## 定时任务配置示例

在 `config.yaml` 中添加定时任务配置：

```yaml
# 定时任务配置
scheduled_tasks:
  enabled: true
  
  tasks:
    - id: "market_data"
      name: "行情数据采集"
      module: "market_data"
      function: "main"
      cron: "0 16 * * 1-5"
      description: "A股日线行情数据采集(MiniQMT)"
      priority: 1
      enabled: true
      
    - id: "financial_data"
      name: "财务数据采集"
      module: "financial_data"
      function: "main"
      cron: "0 17 * * 1-5"
      description: "A股财务数据采集(MiniQMT)"
      priority: 2
      enabled: true
      
    - id: "macro_data"
      name: "宏观数据采集"
      module: "macro_data"
      function: "main"
      cron: "0 9 10-15 * *"
      description: "宏观经济指标采集(AkShare)"
      priority: 3
      enabled: true
      
    - id: "ipo_data"
      name: "IPO数据采集"
      module: "ipo_data"
      function: "main"
      cron: "0 9 * * 1"
      description: "新股发行数据采集(AkShare)"
      priority: 4
      enabled: true
      
    - id: "news_events"
      name: "新闻事件采集"
      module: "news_events"
      function: "main"
      cron: "0 16 * * 1-5"
      description: "个股新闻事件采集(AkShare)"
      priority: 5
      enabled: true
      
    - id: "research_reports"
      name: "研报数据采集"
      module: "research_reports"
      function: "main"
      cron: "0 10 * * 1"
      description: "机构评级/盈利预测采集(AkShare)"
      priority: 6
      enabled: true
      
    - id: "calendar_data"
      name: "财经日历采集"
      module: "calendar_data"
      function: "main"
      cron: "0 8 * * *"
      description: "全球经济事件日历(AkShare)"
      priority: 7
      enabled: true
      
    - id: "catalysts"
      name: "催化剂事件采集"
      module: "catalysts"
      function: "main"
      cron: "0 8 * * 1"
      description: "AI联网搜索催化剂事件(Qwen Max)"
      priority: 8
      enabled: true
      requires_api: true
      
    - id: "market_sentiment"
      name: "市场情绪采集"
      module: "market_sentiment"
      function: "collect_all"
      cron: "0 15 * * 1-5"
      description: "市场情绪指标采集(AkShare)"
      priority: 9
      enabled: true
```

---

## 依赖关系图

```
                        ┌─────────────────┐
                        │   财经日历采集    │
                        │  calendar_data   │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │  催化剂事件采集   │
                        │    catalysts     │
                        └────────┬────────┘
                                 │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
    ┌───────▼───────┐     ┌───────▼───────┐     ┌───────▼───────┐
    │   行情数据采集  │     │   IPO数据采集  │     │  市场情绪采集  │
    │  market_data  │     │   ipo_data    │     │market_sentiment│
    └───────┬───────┘     └───────────────┘     └───────────────┘
            │
    ┌───────┴───────┐
    │               │
┌───▼───┐     ┌─────▼─────┐
│财务数据│     │ 新闻事件   │
│       │     │           │
│financial│   │news_events │
└────────┘     └─────┬─────┘
                     │
              ┌──────▼──────┐
              │   研报数据   │
              │             │
              │research_reports│
              └─────────────┘
```

---

## 执行时间总览

| 时间 | 周一 | 周二 | 周三 | 周四 | 周五 | 周六 | 周日 |
|------|------|------|------|------|------|------|------|
| 08:00 | ✅财经日历 | ✅财经日历 | ✅财经日历 | ✅财经日历 | ✅财经日历 | ✅财经日历 | ✅财经日历 |
| 08:30 | ✅催化剂 | - | - | - | - | - | - |
| 09:00 | ✅IPO数据 | - | - | - | - | - | - |
| 09:30 | ✅IPO数据 | - | - | - | - | - | - |
| 10:00 | ✅研报数据 | - | - | - | - | - | - |
| 15:30 | ✅市场情绪 | ✅市场情绪 | ✅市场情绪 | ✅市场情绪 | ✅市场情绪 | - | - |
| 16:00 | ✅新闻事件 | ✅新闻事件 | ✅新闻事件 | ✅新闻事件 | ✅新闻事件 | - | - |
| 16:30 | ✅行情数据 | ✅行情数据 | ✅行情数据 | ✅行情数据 | ✅行情数据 | - | - |
| 17:00 | ✅财务数据 | ✅财务数据 | ✅财务数据 | ✅财务数据 | ✅财务数据 | - | - |

---

## 数据源依赖

| 数据模块 | 主要依赖 | 备用接口 |
|---------|---------|---------|
| market_data | MiniQMT (xtquant) | 无 |
| financial_data | MiniQMT (xtquant) | 无 |
| macro_data | AkShare | 无 |
| ipo_data | AkShare (东方财富) | 同花顺、巨潮 |
| news_events | AkShare (东方财富) | 无 |
| research_reports | AkShare (东方财富+同花顺) | 无 |
| calendar_data | AkShare (百度财经) | 无 |
| catalysts | Qwen Max API | 无 |
| market_sentiment | AkShare | 无 |
