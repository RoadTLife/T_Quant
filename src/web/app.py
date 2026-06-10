#!/usr/bin/env python3
"""
股票信息查询前端服务
"""

import sys
import os

# 将项目根目录添加到Python路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Flask, render_template, request, jsonify
import pandas as pd
import yaml
import importlib
import inspect

app = Flask(__name__)

STOCK_LIST_FILE = os.path.join(BASE_DIR, 'data/basic/stock_list.csv')

def load_config():
    """加载配置文件"""
    config_path = os.path.join(BASE_DIR, 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

config = load_config()
server_config = config.get('server', {})

def load_stock_list():
    """加载股票列表"""
    if not os.path.exists(STOCK_LIST_FILE):
        return None
    
    df = pd.read_csv(STOCK_LIST_FILE)
    return df

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data-browser')
def data_browser():
    return render_template('data_browser.html')

@app.route('/api/search', methods=['GET'])
def search_stock():
    """搜索股票"""
    query = request.args.get('q', '').strip().upper()
    
    df = load_stock_list()
    if df is None:
        return jsonify({'error': '股票列表文件不存在'}, 404)
    
    if not query:
        return jsonify([])
    
    # 支持按股票代码或名称搜索
    mask = (df['symbol'].str.contains(query, case=False) | 
            df['name'].str.contains(query, case=False))
    results = df[mask].head(20)
    
    return jsonify(results.to_dict('records'))

@app.route('/api/stock/<symbol>')
def get_stock_detail(symbol):
    """获取股票详情"""
    df = load_stock_list()
    if df is None:
        return jsonify({'error': '股票列表文件不存在'}, 404)
    
    result = df[df['symbol'] == symbol]
    if result.empty:
        # 尝试不带后缀的搜索
        result = df[df['symbol'].str.contains(symbol)]
    
    if result.empty:
        return jsonify({'error': '未找到股票'}, 404)
    
    return jsonify(result.iloc[0].to_dict())

@app.route('/api/data-modules')
def get_data_modules():
    """获取所有数据采集模块信息"""
    data_dir = os.path.join(BASE_DIR, 'src/data')
    modules_info = []
    
    # 数据模块配置
    modules_config = {
        'macro_data': {
            'name': '宏观经济数据',
            'description': '采集宏观经济指标（CPI、PPI、PMI、M2、LPR、社融等）',
            'dependencies': ['akshare'],
            'functions': [
                {'name': 'fetch_cpi', 'desc': '采集CPI数据'},
                {'name': 'fetch_ppi', 'desc': '采集PPI数据'},
                {'name': 'fetch_pmi', 'desc': '采集PMI数据'},
                {'name': 'fetch_m2', 'desc': '采集M2数据'},
                {'name': 'fetch_lpr', 'desc': '采集LPR数据'},
                {'name': 'fetch_shrzgm', 'desc': '采集社融数据'}
            ]
        },
        'news_events': {
            'name': '新闻事件采集',
            'description': '采集股票相关新闻，进行情绪分析和重要性识别',
            'dependencies': ['akshare'],
            'functions': [
                {'name': 'fetch_news_akshare', 'desc': '采集股票新闻'},
                {'name': 'analyze_sentiment', 'desc': '情绪分析'},
                {'name': 'check_important', 'desc': '重要事件识别'}
            ]
        },
        'calendar_data': {
            'name': '财经日历',
            'description': '采集财经日历事件，进行事件分类',
            'dependencies': ['akshare'],
            'functions': [
                {'name': 'fetch_and_save', 'desc': '采集财经日历'},
                {'name': 'classify_event', 'desc': '事件分类'}
            ]
        },
        'ipo_data': {
            'name': 'IPO数据',
            'description': '采集新股发行数据',
            'dependencies': ['akshare'],
            'functions': [
                {'name': 'fetch_new_stocks', 'desc': '采集新股列表'},
                {'name': 'parse_and_statistics', 'desc': '数据解析和统计'}
            ]
        },
        'research_reports': {
            'name': '研报数据',
            'description': '采集机构研究报告，包括评级和盈利预测',
            'dependencies': ['akshare'],
            'functions': [
                {'name': 'fetch_institute_recommend', 'desc': '机构评级采集'},
                {'name': 'fetch_profit_forecast', 'desc': '盈利预测采集'},
                {'name': 'deduplicate_recommend', 'desc': '去重处理'}
            ]
        },
        'market_data': {
            'name': '行情数据',
            'description': '采集股票行情数据（需要MiniQMT）',
            'dependencies': ['akshare', 'xtquant'],
            'functions': [
                {'name': 'main', 'desc': '主采集流程'},
                {'name': 'get_existing_latest_dates', 'desc': '获取已有最新日期'}
            ]
        },
        'financial_data': {
            'name': '财务数据',
            'description': '采集股票财务数据（需要MiniQMT）',
            'dependencies': ['akshare', 'xtquant'],
            'functions': [
                {'name': 'main', 'desc': '主采集流程'},
                {'name': 'get_existing_stocks', 'desc': '获取已有股票列表'}
            ]
        },
        'catalysts': {
            'name': '催化剂事件',
            'description': '采集催化剂事件数据（需要OpenAI）',
            'dependencies': ['akshare', 'openai'],
            'functions': [
                {'name': 'fetch_catalysts', 'desc': '采集催化剂事件'},
                {'name': 'analyze_catalyst', 'desc': '催化剂分析'}
            ]
        },
        'market_sentiment': {
            'name': '市场情绪',
            'description': '采集市场情绪核心指标，生成情绪报告',
            'dependencies': ['akshare'],
            'functions': [
                {'name': 'collect_all', 'desc': '采集所有情绪指标'},
                {'name': 'calculate_sentiment_score', 'desc': '计算情绪评分'},
                {'name': 'generate_text_report', 'desc': '生成文本报告'},
                {'name': 'save_to_db', 'desc': '保存到数据库'}
            ]
        }
    }
    
    for module_name, config in modules_config.items():
        # 检查模块是否存在
        module_path = os.path.join(data_dir, f'{module_name}.py')
        exists = os.path.exists(module_path)
        
        # 检查依赖是否满足
        deps_ok = []
        deps_missing = []
        for dep in config['dependencies']:
            try:
                importlib.import_module(dep)
                deps_ok.append(dep)
            except ImportError:
                deps_missing.append(dep)
        
        modules_info.append({
            'name': config['name'],
            'module': module_name,
            'description': config['description'],
            'exists': exists,
            'dependencies': {
                'required': config['dependencies'],
                'ok': deps_ok,
                'missing': deps_missing,
                'all_satisfied': len(deps_missing) == 0
            },
            'functions': config['functions']
        })
    
    return jsonify(modules_info)

@app.route('/api/execute-module/<module_name>', methods=['POST'])
def execute_module(module_name):
    """执行数据采集模块"""
    try:
        # 安全检查：只允许执行白名单中的模块
        allowed_modules = [
            'macro_data', 'news_events', 'calendar_data', 'ipo_data',
            'research_reports', 'market_sentiment'
        ]
        
        if module_name not in allowed_modules:
            return jsonify({'error': f'不允许执行模块: {module_name}'}, 403)
        
        # 动态导入模块
        module = importlib.import_module(f'src.data.{module_name}')
        
        # 查找主入口函数
        if hasattr(module, 'collect_all'):
            result = module.collect_all()
            return jsonify({
                'success': True,
                'module': module_name,
                'result_type': 'dict',
                'message': '采集成功',
                'data': result
            })
        elif hasattr(module, 'fetch_and_save'):
            result = module.fetch_and_save()
            return jsonify({
                'success': True,
                'module': module_name,
                'result_type': 'count',
                'message': f'采集成功，共 {result} 条记录',
                'data': {'count': result}
            })
        elif hasattr(module, 'main'):
            module.main()
            return jsonify({
                'success': True,
                'module': module_name,
                'result_type': 'none',
                'message': '执行成功'
            })
        else:
            return jsonify({'error': '模块没有可执行的入口函数'}, 400)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'module': module_name,
            'error': str(e)
        }), 500

@app.route('/api/test-module/<module_name>/<func_name>', methods=['POST'])
def test_module_function(module_name, func_name):
    """测试模块中的函数"""
    try:
        module = importlib.import_module(f'src.data.{module_name}')
        
        if not hasattr(module, func_name):
            return jsonify({'error': f'函数 {func_name} 不存在'}, 400)
        
        func = getattr(module, func_name)
        
        # 获取函数参数
        sig = inspect.signature(func)
        params = sig.parameters
        
        # 如果需要参数，尝试使用默认值或简单测试值
        args = []
        kwargs = {}
        
        for param_name, param in params.items():
            if param_name == 'self':
                # 如果是类方法，需要先实例化类
                class_name = func_name.replace('fetch_', '').replace('_', '').capitalize() + 'Collector'
                if hasattr(module, class_name):
                    instance = getattr(module, class_name)()
                    func = getattr(instance, func_name)
                continue
            if param.default is not inspect.Parameter.empty:
                kwargs[param_name] = param.default
            else:
                # 尝试提供简单的测试值
                if param.annotation == str:
                    kwargs[param_name] = '600519.SH'
                elif param.annotation == int:
                    kwargs[param_name] = 10
                else:
                    kwargs[param_name] = None
        
        result = func(*args, **kwargs)
        
        # 限制返回数据大小
        if isinstance(result, pd.DataFrame):
            data = result.head(10).to_dict('records')
            return jsonify({
                'success': True,
                'module': module_name,
                'function': func_name,
                'result_type': 'DataFrame',
                'rows': len(result),
                'sample': data
            })
        elif isinstance(result, dict):
            # 限制字典大小
            limited_result = {k: v for i, (k, v) in enumerate(result.items()) if i < 20}
            return jsonify({
                'success': True,
                'module': module_name,
                'function': func_name,
                'result_type': 'dict',
                'data': limited_result
            })
        else:
            return jsonify({
                'success': True,
                'module': module_name,
                'function': func_name,
                'result_type': type(result).__name__,
                'data': str(result)[:500]
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'module': module_name,
            'function': func_name,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = server_config.get('port', 5001)
    host = server_config.get('host', '0.0.0.0')
    debug = server_config.get('debug', True)
    
    print(f"启动服务器: http://{host}:{port}")
    app.run(debug=debug, host=host, port=port)
