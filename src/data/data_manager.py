# -*- coding: utf-8 -*-
"""
数据管理器 - 管理所有数据采集任务的定时执行

功能特性:
  1. 统一管理所有数据采集模块
  2. 支持定时任务配置（基于 APScheduler）
  3. 支持手动触发执行
  4. 执行日志记录与查询
  5. 命令行接口支持

使用方式:
  # 命令行执行
  python -m src.data.data_manager run --task market_data
  python -m src.data.data_manager schedule --start
  
  # Python API
  from src.data.data_manager import DataManager
  dm = DataManager()
  dm.run_task('market_data')
  dm.start_scheduler()
"""
import os
import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ============================================================
# APScheduler 导入（延迟导入）
# ============================================================
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

# ============================================================
# 日志配置
# ============================================================
logger = logging.getLogger('DataManager')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# ============================================================
# 任务配置
# ============================================================
TASK_CONFIG = {
    'market_data': {
        'name': '行情数据采集',
        'module': 'market_data',
        'function': 'main',
        'cron': '0 18 * * *',      # 每天18:00执行（收盘后）
        'description': '采集全量A股日线数据',
        'requires_xtquant': True
    },
    'financial_data': {
        'name': '财务数据采集',
        'module': 'financial_data',
        'function': 'main',
        'cron': '0 19 * * 1',      # 每周一19:00执行
        'description': '采集股票季度财务数据',
        'requires_xtquant': True
    },
    'macro_data': {
        'name': '宏观数据采集',
        'module': 'macro_data',
        'function': 'main',
        'cron': '0 10 2-28 * *',   # 每月2-28日10:00执行
        'description': '采集宏观经济指标',
        'requires_xtquant': False
    },
    'news_events': {
        'name': '新闻事件采集',
        'module': 'news_events',
        'function': 'main',
        'cron': '0 */2 * * *',     # 每2小时执行一次
        'description': '采集个股新闻事件',
        'requires_xtquant': False
    },
    'research_reports': {
        'name': '研报数据采集',
        'module': 'research_reports',
        'function': 'main',
        'cron': '0 9 * * 1-5',     # 工作日9:00执行
        'description': '采集券商研报数据',
        'requires_xtquant': False
    },
    'calendar_data': {
        'name': '财经日历采集',
        'module': 'calendar_data',
        'function': 'main',
        'cron': '0 8 * * *',       # 每天8:00执行
        'description': '采集财经日历事件',
        'requires_xtquant': False
    },
    'catalysts': {
        'name': '催化剂数据采集',
        'module': 'catalysts',
        'function': 'main',
        'cron': '0 12 * * *',      # 每天12:00执行
        'description': '采集事件催化剂数据',
        'requires_xtquant': False
    },
    'ipo_data': {
        'name': 'IPO数据采集',
        'module': 'ipo_data',
        'function': 'main',
        'cron': '0 17 * * 5',      # 每周五17:00执行
        'description': '采集新股发行数据',
        'requires_xtquant': False
    }
}


class LogEntry:
    """日志条目 - 用于内存日志记录"""
    def __init__(self, task_name, task_code, status, start_time):
        self.task_name = task_name
        self.task_code = task_code
        self.status = status
        self.start_time = start_time
        self.end_time = None
        self.duration = 0
        self.records_processed = 0
        self.error_message = ''


class DataManager:
    """数据管理器 - 管理所有数据采集任务"""
    
    def __init__(self):
        self.scheduler = None
        self._db_available = False
        self._memory_logs = []  # 内存日志（当数据库不可用时使用）
        self._init_scheduler()
        self._check_db_connection()
    
    def _init_scheduler(self):
        """初始化定时任务调度器"""
        if APSCHEDULER_AVAILABLE:
            self.scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
            self._register_tasks()
        else:
            logger.warning("APScheduler 不可用，请安装: pip install apscheduler")
    
    def _check_db_connection(self):
        """检查数据库连接是否可用"""
        try:
            from src.conf.db_config import get_connection
            conn = get_connection()
            conn.close()
            self._db_available = True
            logger.info("数据库连接正常")
            self._ensure_log_table()
        except Exception as e:
            self._db_available = False
            logger.warning(f"数据库不可用，将使用内存日志: {e}")
    
    def _ensure_log_table(self):
        """确保执行日志表存在"""
        if not self._db_available:
            return
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS trade_task_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            task_name VARCHAR(50) NOT NULL,
            task_code VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL COMMENT 'running/success/failed',
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            duration INT COMMENT '耗时(秒)',
            records_processed INT DEFAULT 0,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            KEY idx_task_log_name (task_name),
            KEY idx_task_log_time (start_time),
            KEY idx_task_log_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务执行日志';
        """
        try:
            from src.conf.db_config import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"创建日志表失败: {e}")
    
    def _register_tasks(self):
        """注册所有定时任务"""
        if not self.scheduler:
            return
        
        for task_code, config in TASK_CONFIG.items():
            try:
                cron_expr = config.get('cron')
                if cron_expr:
                    trigger = CronTrigger.from_crontab(cron_expr, timezone='Asia/Shanghai')
                    self.scheduler.add_job(
                        self._run_task_wrapper,
                        trigger=trigger,
                        args=[task_code],
                        id=f'task_{task_code}',
                        name=config['name'],
                        replace_existing=True
                    )
                    logger.info(f"已注册定时任务: {config['name']} ({cron_expr})")
            except Exception as e:
                logger.error(f"注册任务 {task_code} 失败: {e}")
    
    def _run_task_wrapper(self, task_code: str):
        """任务执行包装器 - 记录日志"""
        start_time = datetime.now()
        task_name = TASK_CONFIG.get(task_code, {}).get('name', task_code)
        
        # 记录开始
        log_entry = self._log_task_start(task_code, task_name, start_time)
        
        try:
            logger.info(f"开始执行任务: {task_name}")
            result = self.run_task(task_code)
            
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            
            if result['success']:
                self._log_task_success(log_entry, end_time, duration, result.get('records_processed', 0))
                logger.info(f"任务 {task_name} 执行成功，耗时 {duration} 秒")
            else:
                self._log_task_failed(log_entry, end_time, duration, result.get('error', ''))
                logger.error(f"任务 {task_name} 执行失败: {result.get('error', '')}")
                
        except Exception as e:
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            self._log_task_failed(log_entry, end_time, duration, str(e))
            logger.error(f"任务 {task_name} 执行异常: {e}")
    
    def _log_task_start(self, task_code: str, task_name: str, start_time: datetime):
        """记录任务开始"""
        if self._db_available:
            try:
                from src.conf.db_config import get_connection
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO trade_task_log (task_name, task_code, status, start_time) VALUES (%s, %s, %s, %s)",
                    (task_name, task_code, 'running', start_time)
                )
                conn.commit()
                log_id = cursor.lastrowid
                cursor.close()
                conn.close()
                return log_id
            except Exception as e:
                logger.warning(f"数据库日志记录失败，使用内存日志: {e}")
        
        # 内存日志
        entry = LogEntry(task_name, task_code, 'running', start_time)
        self._memory_logs.append(entry)
        return entry
    
    def _log_task_success(self, log_ref, end_time: datetime, duration: int, records: int):
        """记录任务成功"""
        if self._db_available and isinstance(log_ref, int):
            try:
                from src.conf.db_config import get_connection
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE trade_task_log SET status=%s, end_time=%s, duration=%s, records_processed=%s WHERE id=%s",
                    ('success', end_time, duration, records, log_ref)
                )
                conn.commit()
                cursor.close()
                conn.close()
                return
            except Exception as e:
                logger.warning(f"数据库日志更新失败: {e}")
        
        # 内存日志更新
        if isinstance(log_ref, LogEntry):
            log_ref.status = 'success'
            log_ref.end_time = end_time
            log_ref.duration = duration
            log_ref.records_processed = records
    
    def _log_task_failed(self, log_ref, end_time: datetime, duration: int, error_msg: str):
        """记录任务失败"""
        if self._db_available and isinstance(log_ref, int):
            try:
                from src.conf.db_config import get_connection
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE trade_task_log SET status=%s, end_time=%s, duration=%s, error_message=%s WHERE id=%s",
                    ('failed', end_time, duration, error_msg[:2000] if len(error_msg) > 2000 else error_msg, log_ref)
                )
                conn.commit()
                cursor.close()
                conn.close()
                return
            except Exception as e:
                logger.warning(f"数据库日志更新失败: {e}")
        
        # 内存日志更新
        if isinstance(log_ref, LogEntry):
            log_ref.status = 'failed'
            log_ref.end_time = end_time
            log_ref.duration = duration
            log_ref.error_message = error_msg
    
    def run_task(self, task_code: str) -> Dict:
        """
        执行指定任务
        
        Args:
            task_code: 任务代码，如 'market_data', 'macro_data'
        
        Returns:
            {'success': bool, 'records_processed': int, 'error': str}
        """
        config = TASK_CONFIG.get(task_code)
        if not config:
            return {'success': False, 'records_processed': 0, 'error': f"未知任务: {task_code}"}
        
        module_name = config['module']
        function_name = config['function']
        
        try:
            # 动态导入模块
            module = __import__(f'src.data.{module_name}', fromlist=[function_name])
            func = getattr(module, function_name)
            
            # 执行任务
            start_time = time.time()
            result = func()
            
            # 解析结果
            records_processed = 0
            if isinstance(result, dict) and 'records_processed' in result:
                records_processed = result['records_processed']
            elif isinstance(result, int):
                records_processed = result
            
            duration = time.time() - start_time
            logger.info(f"任务 {config['name']} 完成，处理 {records_processed} 条记录，耗时 {duration:.2f} 秒")
            
            return {'success': True, 'records_processed': records_processed, 'error': ''}
            
        except ImportError as e:
            if config.get('requires_xtquant') and 'xtquant' in str(e):
                error = f"需要安装 MiniQMT (xtquant) 才能运行此任务"
            else:
                error = f"导入模块失败: {e}"
            logger.error(error)
            return {'success': False, 'records_processed': 0, 'error': error}
        except Exception as e:
            error = f"执行任务失败: {e}"
            logger.error(error)
            return {'success': False, 'records_processed': 0, 'error': error}
    
    def run_all_tasks(self) -> List[Dict]:
        """执行所有任务"""
        results = []
        for task_code in TASK_CONFIG.keys():
            logger.info(f"--- 执行任务: {TASK_CONFIG[task_code]['name']} ---")
            result = self.run_task(task_code)
            results.append({'task_code': task_code, **result})
        return results
    
    def start_scheduler(self):
        """启动定时任务调度器"""
        if not self.scheduler:
            logger.error("APScheduler 不可用，请安装: pip install apscheduler")
            return
        
        if self.scheduler.running:
            logger.info("调度器已在运行")
            return
        
        self.scheduler.start()
        logger.info("定时任务调度器已启动")
        
        # 打印当前任务列表
        print("\n当前定时任务列表:")
        print("=" * 60)
        for job in self.scheduler.get_jobs():
            print(f"  {job.name} ({job.id}): {str(job.trigger)}")
        print("=" * 60)
        print("按 Ctrl+C 停止调度器")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_scheduler()
    
    def stop_scheduler(self):
        """停止定时任务调度器"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("定时任务调度器已停止")
    
    def get_task_status(self, task_code: Optional[str] = None) -> List[Dict]:
        """
        查询任务执行状态
        
        Args:
            task_code: 任务代码，为空则查询所有
        
        Returns:
            任务状态列表
        """
        results = []
        
        if self._db_available:
            try:
                from src.conf.db_config import get_connection
                conn = get_connection()
                cursor = conn.cursor()
                
                if task_code:
                    cursor.execute("""
                        SELECT task_name, task_code, status, start_time, end_time, duration, records_processed, error_message
                        FROM trade_task_log
                        WHERE task_code = %s
                        ORDER BY start_time DESC
                        LIMIT 10
                    """, (task_code,))
                else:
                    cursor.execute("""
                        SELECT task_name, task_code, status, start_time, end_time, duration, records_processed, error_message
                        FROM trade_task_log
                        ORDER BY start_time DESC
                        LIMIT 50
                    """)
                
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
                
                for row in rows:
                    results.append({
                        'task_name': row[0],
                        'task_code': row[1],
                        'status': row[2],
                        'start_time': row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else None,
                        'end_time': row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else None,
                        'duration': row[5],
                        'records_processed': row[6],
                        'error_message': row[7]
                    })
                return results
            except Exception as e:
                logger.warning(f"从数据库读取日志失败，使用内存日志: {e}")
        
        # 从内存日志读取
        logs = self._memory_logs
        if task_code:
            logs = [l for l in logs if l.task_code == task_code]
        
        for entry in logs[-10:]:  # 只返回最近10条
            results.append({
                'task_name': entry.task_name,
                'task_code': entry.task_code,
                'status': entry.status,
                'start_time': entry.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': entry.end_time.strftime('%Y-%m-%d %H:%M:%S') if entry.end_time else None,
                'duration': entry.duration,
                'records_processed': entry.records_processed,
                'error_message': entry.error_message
            })
        
        return results
    
    def get_task_list(self) -> List[Dict]:
        """获取所有任务配置列表"""
        return [
            {
                'task_code': code,
                'task_name': config['name'],
                'cron': config.get('cron', '未配置'),
                'description': config['description'],
                'requires_xtquant': config.get('requires_xtquant', False)
            }
            for code, config in TASK_CONFIG.items()
        ]


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据管理器 - 管理所有数据采集任务')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # run 命令 - 执行指定任务
    run_parser = subparsers.add_parser('run', help='执行指定任务')
    run_parser.add_argument('task', nargs='?', default=None, help='任务代码，如 market_data')
    run_parser.add_argument('--all', action='store_true', help='执行所有任务')
    
    # schedule 命令 - 定时任务管理
    schedule_parser = subparsers.add_parser('schedule', help='定时任务管理')
    schedule_parser.add_argument('--start', action='store_true', help='启动定时任务调度器')
    schedule_parser.add_argument('--stop', action='store_true', help='停止定时任务调度器')
    
    # status 命令 - 查询任务状态
    status_parser = subparsers.add_parser('status', help='查询任务状态')
    status_parser.add_argument('task', nargs='?', default=None, help='任务代码')
    
    # list 命令 - 列出所有任务
    subparsers.add_parser('list', help='列出所有任务配置')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    dm = DataManager()
    
    if args.command == 'run':
        if args.all:
            print("执行所有任务...")
            results = dm.run_all_tasks()
            print("\n执行结果汇总:")
            print("=" * 60)
            for r in results:
                status = '成功' if r['success'] else '失败'
                print(f"  {r['task_code']}: {status}")
                if not r['success']:
                    print(f"    错误: {r['error']}")
        elif args.task:
            result = dm.run_task(args.task)
            if result['success']:
                print(f"任务 {args.task} 执行成功，处理 {result['records_processed']} 条记录")
            else:
                print(f"任务 {args.task} 执行失败: {result['error']}")
        else:
            print("请指定任务代码或使用 --all 参数")
    
    elif args.command == 'schedule':
        if args.start:
            dm.start_scheduler()
        elif args.stop:
            dm.stop_scheduler()
    
    elif args.command == 'status':
        results = dm.get_task_status(args.task)
        print("任务执行日志:")
        print("=" * 80)
        for r in results:
            print(f"\n任务: {r['task_name']} ({r['task_code']})")
            print(f"  状态: {r['status']}")
            print(f"  开始时间: {r['start_time']}")
            print(f"  结束时间: {r['end_time']}")
            print(f"  耗时: {r['duration']} 秒")
            print(f"  处理记录数: {r['records_processed']}")
            if r['error_message']:
                print(f"  错误信息: {r['error_message']}")
    
    elif args.command == 'list':
        tasks = dm.get_task_list()
        print("任务配置列表:")
        print("=" * 80)
        for task in tasks:
            print(f"\n任务代码: {task['task_code']}")
            print(f"  任务名称: {task['task_name']}")
            print(f"  定时规则: {task['cron']}")
            print(f"  描述: {task['description']}")
            print(f"  需要 xtquant: {'是' if task['requires_xtquant'] else '否'}")


if __name__ == '__main__':
    main()
