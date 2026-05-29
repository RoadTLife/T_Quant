# -*- coding: utf-8 -*-
"""
数据库连接配置
从 utils/config_loader 获取配置
"""
import sys
import os

# 添加项目根目录到路径
def _add_project_root():
    current_file = os.path.abspath(__file__)
    # src/conf/db_config.py -> 向上三级到项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

_add_project_root()

import pymysql
from src.utils.config_loader import get_database_config, get_main_config, ConfigError

DB_CONFIG = get_database_config()

# 可选配置，如果配置
def _safe_get_config(key, default=None):
    try:
        return get_main_config(key)
    except:
        return default

KIMI_API_KEY = _safe_get_config('kimi.api_key')
KIMI_BASE_URL = _safe_get_config('kimi.base_url')
KIMI_MODEL = _safe_get_config('kimi.model')

DASHSCOPE_API_KEY = _safe_get_config('dashscope.api_key')
QWEN_MODEL = _safe_get_config('qwen.model')


def get_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)


def execute_query(sql, params=None):
    """执行查询，返回字典列表"""
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(sql, params or ())
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def execute_update(sql, params=None):
    """执行单条更新/插入"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params or ())
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    return affected


def execute_many(sql, data_list):
    """批量执行插入/更新"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(sql, data_list)
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    return affected