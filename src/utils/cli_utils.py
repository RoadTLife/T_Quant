"""
命令行工具公共模块

提供CLI工具和GUI工具共用的功能
"""

import sys

def print_table(data, headers=None):
    """
    打印表格数据
    
    Args:
        data: 数据（dict, DataFrame, list等）
        headers: 自定义表头
    """
    if isinstance(data, dict):
        max_key_len = max(len(str(k)) for k in data.keys())
        for key, value in data.items():
            print(f"{str(key).ljust(max_key_len)}: {value}")
    elif hasattr(data, 'to_string'):
        print(data.to_string(index=False))
    elif isinstance(data, list):
        for idx, item in enumerate(data, 1):
            print(f"{idx}. {item}")
    else:
        print(data)

def print_divider(char='-', length=60):
    """打印分隔线"""
    print(char * length)

def print_title(title):
    """打印标题"""
    print_divider('=')
    print(f"{title:^60}")
    print_divider('=')

def print_success(message):
    """打印成功消息"""
    print(f"\n✅ {message}")

def print_error(message):
    """打印错误消息"""
    print(f"\n❌ {message}")

def print_warning(message):
    """打印警告消息"""
    print(f"\n⚠️  {message}")

def print_info(message):
    """打印信息消息"""
    print(f"\nℹ️  {message}")

def get_input(prompt, required=True, default=None):
    """
    获取用户输入
    
    Args:
        prompt: 提示信息
        required: 是否必填
        default: 默认值
    
    Returns:
        用户输入的值
    """
    while True:
        value = input(prompt).strip()
        if value:
            return value
        elif not required:
            return default
        else:
            print_error("此项为必填，请重新输入")

def validate_date(date_str):
    """
    验证日期格式
    
    Args:
        date_str: 日期字符串
    
    Returns:
        (bool, message): 验证结果和消息
    """
    import re
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_str):
        return False, "日期格式应为 YYYY-MM-DD"
    
    try:
        from datetime import datetime
        datetime.strptime(date_str, '%Y-%m-%d')
        return True, "日期格式正确"
    except ValueError:
        return False, "无效的日期"

def validate_time(time_str):
    """
    验证时间格式
    
    Args:
        time_str: 时间字符串
    
    Returns:
        (bool, message): 验证结果和消息
    """
    import re
    pattern = r'^\d{2}:\d{2}$'
    if not re.match(pattern, time_str):
        return False, "时间格式应为 HH:MM"
    
    try:
        hours, minutes = map(int, time_str.split(':'))
        if 0 <= hours < 24 and 0 <= minutes < 60:
            return True, "时间格式正确"
        return False, "时间超出范围"
    except ValueError:
        return False, "无效的时间"

def validate_stock_symbol(symbol):
    """
    验证股票代码格式
    
    Args:
        symbol: 股票代码
    
    Returns:
        (bool, message): 验证结果和消息
    """
    import re
    pattern = r'^[0-9]{6}(?:\.[A-Za-z]{2})?$'
    if re.match(pattern, symbol):
        return True, "股票代码格式正确"
    return False, "股票代码格式应为 6位数字 或 6位数字.交易所代码"

def exit_with_error(message, exit_code=1):
    """打印错误并退出"""
    print_error(message)
    sys.exit(exit_code)

def confirm_action(message):
    """
    确认操作
    
    Args:
        message: 确认消息
    
    Returns:
        bool: 用户是否确认
    """
    response = input(f"{message} (y/N): ").strip().lower()
    return response == 'y' or response == 'yes'