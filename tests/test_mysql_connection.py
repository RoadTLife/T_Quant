# -*- coding: utf-8 -*-
"""
MySQL 数据库连接测试
测试数据库配置是否正确，连接是否正常
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from src.utils.config_loader import get_database_config, ConfigError


def test_mysql_connection():
    """测试 MySQL 数据库连接"""
    print("=" * 60)
    print("MySQL 数据库连接测试")
    print("=" * 60)
    
    try:
        # 获取数据库配置
        db_config = get_database_config()
        print(f"\n📋 加载的数据库配置:")
        print(f"  Host: {db_config.get('host')}")
        print(f"  Port: {db_config.get('port')}")
        print(f"  Username: {db_config.get('user')}")
        print(f"  Database: {db_config.get('database')}")
        print(f"  Charset: {db_config.get('charset')}")
        
        # 验证配置完整性
        required_fields = ['host', 'user', 'database', 'port']
        missing_fields = [f for f in required_fields if f not in db_config or not db_config[f]]
        
        if missing_fields:
            print(f"\n❌ 配置不完整，缺少以下字段: {', '.join(missing_fields)}")
            print("请检查 config.yaml 中的 database 配置")
            return False
        
        # 尝试连接数据库
        print("\n🔌 正在尝试连接数据库...")
        connection = None
        
        try:
            connection = pymysql.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config.get('password', ''),
                database=db_config['database'],
                charset=db_config.get('charset', 'utf8mb4'),
                connect_timeout=10
            )
            
            print("✅ 数据库连接成功!")
            
            # 测试查询
            print("\n📊 测试数据库查询...")
            with connection.cursor() as cursor:
                # 获取 MySQL 版本
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                print(f"  MySQL 版本: {version}")
                
                # 获取当前数据库名
                cursor.execute("SELECT DATABASE()")
                db_name = cursor.fetchone()[0]
                print(f"  当前数据库: {db_name}")
                
                # 获取表数量
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                table_count = len(tables)
                print(f"  数据库表数量: {table_count}")
                
                if table_count > 0:
                    print(f"  表列表: {', '.join([t[0] for t in tables[:5]])}" + ("..." if table_count > 5 else ""))
            
            print("\n✅ 所有测试通过!")
            return True
            
        except pymysql.Error as e:
            print(f"\n❌ 数据库连接失败: {e}")
            print(f"  错误代码: {e.args[0]}")
            print(f"  错误信息: {e.args[1]}")
            
            # 常见错误提示
            error_codes = {
                1045: "用户名或密码错误",
                1049: "数据库不存在",
                2003: "无法连接到MySQL服务器，请检查主机和端口",
                2006: "MySQL服务器断开连接",
                1044: "用户没有访问数据库的权限"
            }
            
            if e.args[0] in error_codes:
                print(f"  可能原因: {error_codes[e.args[0]]}")
            
            return False
        
        finally:
            if connection:
                connection.close()
                print("\n🔒 连接已关闭")
    
    except ConfigError as e:
        print(f"\n❌ 配置加载失败: {e}")
        return False
    
    except Exception as e:
        print(f"\n❌ 测试过程中发生未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schema_exists():
    """测试数据库表结构是否存在"""
    print("\n" + "=" * 60)
    print("数据库表结构测试")
    print("=" * 60)
    
    try:
        db_config = get_database_config()
        connection = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config.get('password', ''),
            database=db_config['database'],
            charset=db_config.get('charset', 'utf8mb4'),
            connect_timeout=10
        )
        
        required_tables = [
            'trade_stock_daily',
            'trade_stock_news',
            'trade_stock_financial',
            'trade_macro_indicator',
            'trade_rate_daily',
            'trade_report_consensus',
            'trade_calendar_event',
            'trade_stock_basic',
            'trade_backtest_result',
            'trade_signal',
            'trade_operation_log'
        ]
        
        print("\n📋 检查表结构是否存在:")
        
        missing_tables = []
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            existing_tables = [t[0] for t in cursor.fetchall()]
            
            for table in required_tables:
                if table in existing_tables:
                    print(f"  ✅ {table}")
                else:
                    print(f"  ❌ {table} - 缺失")
                    missing_tables.append(table)
        
        if missing_tables:
            print(f"\n⚠️  存在缺失的表: {', '.join(missing_tables)}")
            print("请运行 sql/schema.sql 创建表结构")
            return False
        else:
            print("\n✅ 所有表结构都已存在")
            return True
    
    except Exception as e:
        print(f"\n❌ 表结构测试失败: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("MySQL 数据库连接测试工具")
    print("版本: 1.0")
    print("=" * 60)
    
    # 运行连接测试
    conn_success = test_mysql_connection()
    
    # 如果连接成功，继续测试表结构
    if conn_success:
        test_schema_exists()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    sys.exit(0 if conn_success else 1)