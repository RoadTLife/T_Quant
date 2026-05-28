from utils.stock_code_finder import get_stock_code, search_stock, get_stock_info_by_code

# 测试1: 根据名称获取代码
code = get_stock_code('贵州茅台')
print(f'贵州茅台的代码: {code}')

# 测试2: 搜索股票
result = search_stock('茅台')
print('\n搜索茅台结果:')
for item in result:
    print(f'  {item["symbol"]} - {item["name"]}')

# 测试3: 获取股票信息
info = get_stock_info_by_code('sh.600519')
print(f'\n股票信息: {info}')