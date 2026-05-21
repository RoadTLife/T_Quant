# 量化交易框架

一个基于 Python 的量化交易框架，用于策略开发、回测和实盘交易。

## 功能特性

- 支持多种数据源（股票、期货、加密货币）
- 灵活的策略开发框架
- 强大的回测引擎
- 实时交易支持
- 详细的性能分析报告

## 技术栈

- **语言**: Python 3.9+
- **数据库**: SQLite / MySQL
- **数据处理**: Pandas, NumPy
- **可视化**: Matplotlib, Plotly
- **回测引擎**: 自建事件驱动引擎
- **API接口**: RESTful API

## 项目结构

```
quant/
├── data/                 # 数据目录
│   ├── raw/             # 原始数据
│   └── processed/       # 处理后数据
├── strategies/          # 策略模块
│   ├── __init__.py
│   ├── base.py          # 策略基类
│   ├── moving_average.py # 均线策略
│   └── momentum.py      # 动量策略
├── backtest/            # 回测模块
│   ├── __init__.py
│   ├── engine.py        # 回测引擎
│   └── analyzer.py      # 分析器
├── trading/             # 交易模块
│   ├── __init__.py
│   ├── broker.py        # 券商接口
│   └── execution.py     # 执行引擎
├── utils/               # 工具模块
│   ├── __init__.py
│   ├── data_fetcher.py  # 数据获取
│   ├── logger.py        # 日志工具
│   └── config.py        # 配置管理
├── tests/               # 测试模块
│   ├── __init__.py
│   ├── test_strategies.py
│   └── test_backtest.py
├── docs/                # 文档
├── config.yaml          # 配置文件
├── requirements.txt     # 依赖列表
└── main.py              # 主入口
```

## 安装步骤

```bash
# 克隆项目
git clone <repository-url>
cd quant

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 快速开始

### 1. 配置数据源

编辑 `config.yaml` 文件，配置数据源和交易参数。

### 2. 运行回测

```python
from backtest.engine import BackTestEngine
from strategies.moving_average import MovingAverageStrategy

# 创建策略
strategy = MovingAverageStrategy()

# 创建回测引擎
engine = BackTestEngine()

# 运行回测
results = engine.run(strategy, '2023-01-01', '2024-01-01')

# 打印结果
print(results)
```

### 3. 查看分析报告

回测完成后，系统会自动生成详细的性能分析报告，包括：
- 收益率曲线
- 最大回撤
- Sharpe比率
- 胜率统计

## 策略开发

### 创建自定义策略

继承 `BaseStrategy` 类并实现以下方法：

```python
from strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
    
    def on_bar(self, data):
        # 实现策略逻辑
        if self.should_buy(data):
            self.buy()
        elif self.should_sell(data):
            self.sell()
```

## 模块说明

### strategies/
包含所有交易策略的实现，支持自定义策略开发。

### backtest/
回测引擎核心模块，支持事件驱动回测。

### trading/
实盘交易模块，对接券商API。

### utils/
工具函数集合，包括数据获取、日志和配置管理。

## 测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行指定测试
python -m pytest tests/test_strategies.py
```

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License