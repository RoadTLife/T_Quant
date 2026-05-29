CREATE DATABASE IF NOT EXISTS trade DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE trade;

CREATE TABLE IF NOT EXISTS trade_stock_daily (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open_price DECIMAL(10,2) COMMENT '开盘价',
    high_price DECIMAL(10,2) COMMENT '最高价',
    low_price DECIMAL(10,2) COMMENT '最低价',
    close_price DECIMAL(10,2) COMMENT '收盘价(前复权)',
    volume BIGINT COMMENT '成交量(股)',
    amount DECIMAL(20,2) COMMENT '成交额(元)',
    turnover_rate DECIMAL(10,4) COMMENT '换手率',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY idx_stock_daily_code_date (stock_code, trade_date),
    KEY idx_stock_daily_code (stock_code),
    KEY idx_stock_daily_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='日K线数据';

CREATE TABLE IF NOT EXISTS trade_stock_news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(20) COMMENT '股票代码',
    sector_code VARCHAR(20) COMMENT '板块代码',
    news_type VARCHAR(20) NOT NULL COMMENT 'announcement/news/report',
    title VARCHAR(500) NOT NULL,
    content TEXT,
    summary TEXT,
    source VARCHAR(50) COMMENT 'eastmoney/cailianshe/kimi',
    source_url VARCHAR(500),
    published_at DATETIME,
    sentiment VARCHAR(20) COMMENT 'positive/negative/neutral',
    sentiment_score DECIMAL(5,2) COMMENT '-1到1',
    is_important TINYINT DEFAULT 0,
    is_read TINYINT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_stock_news_code (stock_code),
    KEY idx_stock_news_published (published_at),
    KEY idx_stock_news_type (news_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='新闻事件';

CREATE TABLE IF NOT EXISTS trade_stock_financial (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    report_date DATE NOT NULL COMMENT '报告期',
    revenue DECIMAL(20,2) COMMENT '营业收入(元)',
    net_profit DECIMAL(20,2) COMMENT '净利润(元)',
    eps DECIMAL(10,4) COMMENT '每股收益',
    roe DECIMAL(10,4) COMMENT 'ROE(%)',
    roa DECIMAL(10,4) COMMENT 'ROA(%)',
    gross_margin DECIMAL(10,4) COMMENT '毛利率(%)',
    net_margin DECIMAL(10,4) COMMENT '净利率(%)',
    debt_ratio DECIMAL(10,4) COMMENT '资产负债率(%)',
    current_ratio DECIMAL(10,4) COMMENT '流动比率',
    operating_cashflow DECIMAL(20,2) COMMENT '经营现金流(元)',
    total_assets DECIMAL(20,2) COMMENT '总资产(元)',
    total_equity DECIMAL(20,2) COMMENT '净资产(元)',
    data_source VARCHAR(20) DEFAULT 'akshare',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY idx_fina_code_date (stock_code, report_date),
    KEY idx_fina_code (stock_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='季度财务数据';

CREATE TABLE IF NOT EXISTS trade_macro_indicator (
    id INT AUTO_INCREMENT PRIMARY KEY,
    indicator_date DATE NOT NULL COMMENT '指标月份(月末日期)',
    cpi_yoy DECIMAL(10,2) COMMENT 'CPI同比(%)',
    ppi_yoy DECIMAL(10,2) COMMENT 'PPI同比(%)',
    pmi DECIMAL(10,2) COMMENT 'PMI',
    m2_yoy DECIMAL(10,2) COMMENT 'M2同比增速(%)',
    shrzgm DECIMAL(14,0) COMMENT '社融规模增量(亿元)',
    lpr_1y DECIMAL(6,2) COMMENT 'LPR 1年期(%)',
    lpr_5y DECIMAL(6,2) COMMENT 'LPR 5年期(%)',
    data_source VARCHAR(20) DEFAULT 'akshare',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY idx_macro_date (indicator_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='月度宏观指标';

CREATE TABLE IF NOT EXISTS trade_rate_daily (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rate_date DATE NOT NULL COMMENT '日期',
    cn_bond_10y DECIMAL(8,4) COMMENT '中国10年期国债收益率(%)',
    us_bond_10y DECIMAL(8,4) COMMENT '美国10年期国债收益率(%)',
    data_source VARCHAR(20) DEFAULT 'akshare',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY idx_rate_date (rate_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='日频利率指标';

CREATE TABLE IF NOT EXISTS trade_report_consensus (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    broker VARCHAR(50) COMMENT '券商',
    report_date DATE,
    rating VARCHAR(20) COMMENT '买入/增持/中性/减持',
    target_price DECIMAL(10,2),
    eps_forecast_current DECIMAL(10,4) COMMENT '当年EPS预测',
    eps_forecast_next DECIMAL(10,4) COMMENT '次年EPS预测',
    revenue_forecast DECIMAL(20,2) COMMENT '营收预测(亿)',
    source_file VARCHAR(500) COMMENT 'PDF文件路径',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY idx_consensus_unique (stock_code, broker, report_date),
    KEY idx_consensus_code (stock_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='研报一致性预期';

CREATE TABLE IF NOT EXISTS trade_calendar_event (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_date DATE NOT NULL COMMENT '事件日期',
    event_time VARCHAR(10) COMMENT '事件时间(HH:MM)',
    country VARCHAR(10) NOT NULL DEFAULT 'CN' COMMENT 'CN/US/EU/JP',
    category VARCHAR(30) NOT NULL COMMENT 'rate/inflation/employment/gdp/pmi/trade/policy/other',
    title VARCHAR(200) NOT NULL,
    importance TINYINT DEFAULT 2 COMMENT '1=低 2=中 3=高',
    previous_value VARCHAR(50) COMMENT '前值',
    forecast_value VARCHAR(50) COMMENT '预测值',
    actual_value VARCHAR(50) COMMENT '实际值',
    impact VARCHAR(200) COMMENT '市场影响说明',
    ai_prompt TEXT COMMENT 'AI提问prompt',
    source VARCHAR(50) COMMENT 'eastmoney/fred/manual',
    source_url VARCHAR(500),
    is_recurring TINYINT DEFAULT 0,
    recurrence_rule VARCHAR(100) COMMENT '周期规则',
    status VARCHAR(20) DEFAULT 'upcoming' COMMENT 'upcoming/released/cancelled',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY idx_calendar_event (event_date, country, title),
    KEY idx_calendar_date (event_date),
    KEY idx_calendar_country (country),
    KEY idx_calendar_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财经日历事件';

CREATE TABLE IF NOT EXISTS trade_stock_basic (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(50) COMMENT '股票名称',
    exchange VARCHAR(20) COMMENT '交易所(SSE/SZSE)',
    industry VARCHAR(50) COMMENT '行业',
    sector VARCHAR(50) COMMENT '板块',
    listed_date DATE COMMENT '上市日期',
    total_shares DECIMAL(20,0) COMMENT '总股本(股)',
    float_shares DECIMAL(20,0) COMMENT '流通股本(股)',
    is_st TINYINT DEFAULT 0 COMMENT '是否ST',
    is_hk TINYINT DEFAULT 0 COMMENT '是否港股',
    data_source VARCHAR(20) DEFAULT 'baostock',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY idx_stock_code (stock_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票基础信息';

CREATE TABLE IF NOT EXISTS trade_backtest_result (
    id INT AUTO_INCREMENT PRIMARY KEY,
    strategy_name VARCHAR(50) NOT NULL COMMENT '策略名称',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    start_date DATE NOT NULL COMMENT '回测开始日期',
    end_date DATE NOT NULL COMMENT '回测结束日期',
    initial_capital DECIMAL(15,2) COMMENT '初始资金',
    final_capital DECIMAL(15,2) COMMENT '最终资金',
    total_return DECIMAL(10,4) COMMENT '总收益率',
    annualized_return DECIMAL(10,4) COMMENT '年化收益率',
    max_drawdown DECIMAL(10,4) COMMENT '最大回撤',
    sharpe_ratio DECIMAL(10,4) COMMENT '夏普比率',
    win_rate DECIMAL(10,4) COMMENT '胜率',
    total_trades INT COMMENT '交易次数',
    profit_factor DECIMAL(10,4) COMMENT '盈利因子',
    strategy_params TEXT COMMENT '策略参数(JSON)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_backtest_strategy (strategy_name),
    KEY idx_backtest_code (stock_code),
    KEY idx_backtest_date (start_date, end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='策略回测结果';

CREATE TABLE IF NOT EXISTS trade_signal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    strategy_name VARCHAR(50) NOT NULL COMMENT '策略名称',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    signal_date DATE NOT NULL COMMENT '信号日期',
    signal_type VARCHAR(20) NOT NULL COMMENT 'buy/sell/hold',
    signal_strength DECIMAL(5,2) COMMENT '信号强度(0-1)',
    confidence DECIMAL(5,2) COMMENT '置信度(0-1)',
    price DECIMAL(10,2) COMMENT '信号触发价格',
    stop_loss DECIMAL(10,2) COMMENT '止损价',
    take_profit DECIMAL(10,2) COMMENT '止盈价',
    notes TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY idx_signal_unique (strategy_name, stock_code, signal_date),
    KEY idx_signal_code (stock_code),
    KEY idx_signal_date (signal_date),
    KEY idx_signal_type (signal_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='交易信号';

CREATE TABLE IF NOT EXISTS trade_operation_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation_type VARCHAR(30) NOT NULL COMMENT '操作类型',
    operator VARCHAR(50) COMMENT '操作人',
    target_type VARCHAR(30) COMMENT '操作对象类型',
    target_id VARCHAR(100) COMMENT '操作对象ID',
    description TEXT COMMENT '操作描述',
    before_data TEXT COMMENT '操作前数据(JSON)',
    after_data TEXT COMMENT '操作后数据(JSON)',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    user_agent VARCHAR(200) COMMENT '用户代理',
    success TINYINT DEFAULT 1 COMMENT '是否成功',
    error_message TEXT COMMENT '错误信息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_operation_type (operation_type),
    KEY idx_operation_time (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志';

SELECT 'Tables created successfully in database: trade' AS result;