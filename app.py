#!/usr/bin/env python3
"""
股票信息查询前端服务
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

STOCK_LIST_FILE = 'data/basic/stock_list.csv'

def load_stock_list():
    """加载股票列表"""
    if not os.path.exists(STOCK_LIST_FILE):
        return None
    
    df = pd.read_csv(STOCK_LIST_FILE)
    return df

@app.route('/')
def index():
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
