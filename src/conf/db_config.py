# -*- coding: utf-8 -*-
"""
数据库连接配置
从 utils/config_loader 获取配置
"""
import pymysql
from src.utils.config_loader import get_database_config, get_main_config, ConfigError

DB_CONFIG = get_database_config()

KIMI_API_KEY = get_main_config('kimi.api_key')
KIMI_BASE_URL = get_main_config('kimi.base_url')
KIMI_MODEL = get_main_config('kimi.model')

DASHSCOPE_API_KEY = get_main_config('dashscope.api_key')
QWEN_MODEL = get_main_config('dashscope.model')


def _safe_get_config(key: str, default=None):
    """安全获取配置，不存在时返回默认值"""
    try:
        return get_main_config(key)
    except ConfigError:
        return default


# OpenAI配置（兼容DashScope等服务）
OPENAI_API_KEY = _safe_get_config('openai.api_key')
OPENAI_BASE_URL = _safe_get_config('openai.base_url')
OPENAI_MODEL = _safe_get_config('openai.model')


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