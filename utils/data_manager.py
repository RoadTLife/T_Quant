import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta
from .datasources import DataSourceFactory

class DataManager:
    def __init__(self, db_path='data/stock_data.db'):
        self.db_path = db_path
        self._init_database()
        self.data_source = None
        self.stock_list_file = 'data/basic/stock_list.csv'
    
    def fetch_a_stock_list(self, source='baostock'):
        """从数据源获取A股股票列表"""
        if self.data_source is None:
            self.data_source = DataSourceFactory.create_source(source)
            self.data_source.initialize()
        
        df = self.data_source.get_stock_list(market='A')
        return df
    
    def save_stock_list_to_file(self, df, filename=None):
        """保存股票列表到本地文件"""
        if filename is None:
            filename = self.stock_list_file
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        df.to_csv(filename, index=False)
        return filename
    
    def load_stock_list_from_file(self, filename=None):
        """从本地文件加载股票列表"""
        if filename is None:
            filename = self.stock_list_file
        
        if not os.path.exists(filename):
            return None
        
        df = pd.read_csv(filename)
        return df
    
    def get_a_stock_list(self, source='baostock', use_local=True):
        """
        获取A股股票列表，优先使用本地文件
        
        Args:
            source: 数据源
            use_local: 是否优先使用本地文件
        
        Returns:
            DataFrame: 股票列表
        """
        if use_local:
            df = self.load_stock_list_from_file()
            if df is not None and not df.empty:
                return df
        
        df = self.fetch_a_stock_list(source)
        
        if not df.empty:
            self.save_stock_list_to_file(df)
        
        return df
    
    def _init_database(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                symbol TEXT PRIMARY KEY,
                name TEXT,
                market TEXT,
                industry TEXT,
                listed_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_data (
                symbol TEXT,
                date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                amount REAL,
                data_source TEXT,
                PRIMARY KEY (symbol, date)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_status (
                symbol TEXT PRIMARY KEY,
                earliest_date TEXT,
                latest_date TEXT,
                total_records INTEGER,
                last_sync TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def list_downloaded_stocks(self):
        conn = self._connect()
        query = '''
            SELECT s.symbol, s.name, s.market, 
                   ds.earliest_date, ds.latest_date, ds.total_records
            FROM stocks s
            LEFT JOIN data_status ds ON s.symbol = ds.symbol
        '''
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    
    def get_database_summary(self):
        conn = self._connect()
        
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM stocks')
        total_stocks = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM daily_data')
        total_records = cursor.fetchone()[0]
        
        cursor.execute('SELECT MIN(date), MAX(date) FROM daily_data')
        date_range = cursor.fetchone()
        
        cursor.execute('''
            SELECT COUNT(*) FROM data_status 
            WHERE status = 'incomplete'
        ''')
        incomplete_count = cursor.fetchone()[0] if cursor.rowcount > 0 else 0
        
        conn.close()
        
        return {
            'total_stocks': total_stocks,
            'total_records': total_records,
            'date_range': {'start': date_range[0], 'end': date_range[1]},
            'incomplete_stocks': incomplete_count,
            'database_path': self.db_path
        }
    
    def get_stock_detail(self, symbol):
        conn = self._connect()
        
        query = '''
            SELECT s.*, ds.*
            FROM stocks s
            LEFT JOIN data_status ds ON s.symbol = ds.symbol
            WHERE s.symbol = ?
        '''
        cursor = conn.cursor()
        cursor.execute(query, (symbol,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        detail = {
            'symbol': row[0],
            'name': row[1],
            'market': row[2],
            'industry': row[3],
            'listed_date': row[4],
            'created_at': row[5],
            'earliest_date': row[6],
            'latest_date': row[7],
            'total_records': row[8],
            'last_sync': row[9],
            'status': row[10]
        }
        
        query_data = 'SELECT * FROM daily_data WHERE symbol = ? ORDER BY date DESC LIMIT 10'
        recent_data = pd.read_sql(query_data, conn, params=(symbol,))
        
        conn.close()
        
        detail['recent_data'] = recent_data
        return detail
    
    def check_local_data(self, symbol, start_date, end_date):
        """检查本地是否存在指定时间段的数据"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM daily_data 
            WHERE symbol = ? AND date >= ? AND date <= ?
        ''', (symbol, start_date, end_date))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        expected_days = len(pd.date_range(start_date, end_date, freq='B'))
        coverage = count / expected_days if expected_days > 0 else 0
        
        return {
            'exists': count > 0,
            'count': count,
            'expected': expected_days,
            'coverage': coverage
        }
    
    def get_local_data(self, symbol, start_date, end_date):
        """从本地读取指定时间段的数据"""
        conn = self._connect()
        query = '''
            SELECT * FROM daily_data 
            WHERE symbol = ? AND date >= ? AND date <= ?
            ORDER BY date
        '''
        df = pd.read_sql(query, conn, params=(symbol, start_date, end_date))
        conn.close()
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        
        return df
    
    def download_data(self, symbol, start_date, end_date, source='baostock', use_local=True):
        """
        下载股票数据，优先检查本地数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            source: 数据源
            use_local: 是否优先使用本地数据
        
        Returns:
            (success, message)
        """
        if use_local:
            local_info = self.check_local_data(symbol, start_date, end_date)
            if local_info['coverage'] >= 0.95:
                return True, f"本地已存在完整数据 ({local_info['count']}/{local_info['expected']} 条)"
        
        if self.data_source is None:
            self.data_source = DataSourceFactory.create_source(source)
            self.data_source.initialize()
        
        try:
            df = self.data_source.get_daily_data(symbol, start_date, end_date)
            
            if df.empty:
                return False, "未获取到数据"
            
            conn = self._connect()
            
            df['date'] = df.index.strftime('%Y-%m-%d')
            df['symbol'] = symbol
            df['data_source'] = source
            
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM daily_data 
                WHERE symbol = ? AND date >= ? AND date <= ?
            ''', (symbol, start_date, end_date))
            
            df.to_sql('daily_data', conn, if_exists='append', index=False)
            
            self._update_stock_info(symbol, df)
            self._update_data_status(symbol)
            
            conn.commit()
            conn.close()
            
            csv_path = self._save_to_csv(df, source, start_date, end_date, symbol)
            
            return True, f"成功下载 {len(df)} 条数据，已保存至 {csv_path}"
        
        except Exception as e:
            return False, str(e)
    
    def download_all_stocks(self, start_date, end_date, source='baostock'):
        """下载所有A股股票的数据，只保存合并的 CSV 文件"""
        print(f"正在获取A股股票列表...")
        
        stock_list = self.get_a_stock_list(source=source, use_local=True)
        
        if stock_list is None or stock_list.empty:
            return {'success': [], 'failed': [], 'skipped': [], 'error': '无法获取股票列表'}
        
        symbols = stock_list['symbol'].tolist()
        print(f"共找到 {len(symbols)} 只股票")
        
        results = {'success': [], 'failed': [], 'skipped': [], 'total': len(symbols)}
        all_data = []
        
        if self.data_source is None:
            self.data_source = DataSourceFactory.create_source(source)
            self.data_source.initialize()
        
        for i, symbol in enumerate(symbols):
            print(f"\r正在下载 ({i+1}/{len(symbols)}): {symbol}", end='', flush=True)
            
            local_info = self.check_local_data(symbol, start_date, end_date)
            
            if local_info['coverage'] >= 0.95:
                results['skipped'].append({'symbol': symbol, 'reason': '本地已有完整数据'})
                df = self.get_local_data(symbol, start_date, end_date)
                if not df.empty:
                    df = df.reset_index()
                    df['symbol'] = symbol
                    all_data.append(df)
            else:
                try:
                    df = self.data_source.get_daily_data(symbol, start_date, end_date)
                    
                    if df.empty:
                        results['failed'].append({'symbol': symbol, 'error': '未获取到数据'})
                        continue
                    
                    df['date'] = df.index.strftime('%Y-%m-%d')
                    df['symbol'] = symbol
                    df['data_source'] = source
                    
                    conn = self._connect()
                    cursor = conn.cursor()
                    cursor.execute('''
                        DELETE FROM daily_data 
                        WHERE symbol = ? AND date >= ? AND date <= ?
                    ''', (symbol, start_date, end_date))
                    
                    df.to_sql('daily_data', conn, if_exists='append', index=False)
                    self._update_stock_info(symbol, df)
                    self._update_data_status(symbol)
                    conn.commit()
                    conn.close()
                    
                    results['success'].append({'symbol': symbol, 'message': f"成功下载 {len(df)} 条数据"})
                    
                    df = self.get_local_data(symbol, start_date, end_date)
                    if not df.empty:
                        df = df.reset_index()
                        df['symbol'] = symbol
                        all_data.append(df)
                
                except Exception as e:
                    results['failed'].append({'symbol': symbol, 'error': str(e)})
        
        # 合并所有股票数据为一个 CSV 文件
        if all_data:
            all_df = pd.concat(all_data, ignore_index=True)
            all_df = all_df[['date', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'amount', 'data_source']]
            csv_filename = self._save_to_csv(all_df, source, start_date, end_date, 'all')
            results['csv_file'] = csv_filename
        
        return results
    
    def _save_to_csv(self, df, source, start_date, end_date, symbol='all'):
        """保存数据到 CSV 文件"""
        os.makedirs('data/csv', exist_ok=True)
        
        csv_filename = f"{source}_{start_date}_{end_date}_{symbol}.csv"
        csv_path = os.path.join('data', 'csv', csv_filename)
        
        df.to_csv(csv_path, index=False)
        
        return csv_path
    
    def _update_stock_info(self, symbol, df):
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM stocks WHERE symbol = ?', (symbol,))
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO stocks (symbol, name, market, listed_date)
                VALUES (?, ?, ?, ?)
            ''', (symbol, '', 'A', df['date'].min()))
        
        conn.commit()
        conn.close()
    
    def _update_data_status(self, symbol):
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT MIN(date), MAX(date), COUNT(*) FROM daily_data WHERE symbol = ?
        ''', (symbol,))
        result = cursor.fetchone()
        
        if result[0]:
            cursor.execute('''
                REPLACE INTO data_status 
                (symbol, earliest_date, latest_date, total_records, last_sync, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (symbol, result[0], result[1], result[2], 
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'active'))
        
        conn.commit()
        conn.close()
    
    def scan_data_gaps(self, symbol=None):
        gaps = {}
        
        if symbol:
            symbols = [symbol]
        else:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute('SELECT symbol FROM data_status')
            symbols = [row[0] for row in cursor.fetchall()]
            conn.close()
        
        for sym in symbols:
            gaps[sym] = self._scan_single_stock_gaps(sym)
        
        return gaps
    
    def _scan_single_stock_gaps(self, symbol):
        conn = self._connect()
        
        query = '''
            SELECT earliest_date, latest_date, total_records 
            FROM data_status 
            WHERE symbol = ?
        '''
        cursor = conn.cursor()
        cursor.execute(query, (symbol,))
        status = cursor.fetchone()
        
        if not status:
            conn.close()
            return {'status': 'not_found', 'gaps': []}
        
        earliest = datetime.strptime(status[0], '%Y-%m-%d')
        latest = datetime.strptime(status[1], '%Y-%m-%d')
        expected_days = len(pd.date_range(earliest, latest, freq='B'))
        
        actual_records = status[2]
        gap_count = expected_days - actual_records
        
        missing_dates = []
        if gap_count > 0:
            query_dates = 'SELECT date FROM daily_data WHERE symbol = ? ORDER BY date'
            existing_dates = pd.read_sql(query_dates, conn, params=(symbol,))['date'].tolist()
            all_dates = pd.date_range(earliest, latest, freq='B').strftime('%Y-%m-%d').tolist()
            missing_dates = list(set(all_dates) - set(existing_dates))
            missing_dates.sort()
        
        conn.close()
        
        return {
            'status': 'incomplete' if gap_count > 0 else 'complete',
            'expected_records': expected_days,
            'actual_records': actual_records,
            'gap_count': gap_count,
            'missing_dates': missing_dates[:20]
        }
    
    def fix_data_gaps(self, symbol=None):
        results = {}
        
        if symbol:
            symbols = [symbol]
        else:
            gaps = self.scan_data_gaps()
            symbols = [sym for sym, info in gaps.items() if info['status'] == 'incomplete']
        
        for sym in symbols:
            gaps_info = self._scan_single_stock_gaps(sym)
            if gaps_info['missing_dates']:
                results[sym] = self._fix_single_stock_gaps(sym, gaps_info['missing_dates'])
            else:
                results[sym] = {'status': 'no_gaps', 'fixed_count': 0}
        
        return results
    
    def _fix_single_stock_gaps(self, symbol, missing_dates):
        if self.data_source is None:
            self.data_source = DataSourceFactory.create_source('baostock')
            self.data_source.initialize()
        
        fixed_count = 0
        failed_dates = []
        
        for date in missing_dates:
            try:
                df = self.data_source.get_daily_data(symbol, date, date)
                if not df.empty:
                    conn = self._connect()
                    df['date'] = df.index.strftime('%Y-%m-%d')
                    df['symbol'] = symbol
                    df['data_source'] = 'baostock'
                    df.to_sql('daily_data', conn, if_exists='append', index=False)
                    conn.commit()
                    conn.close()
                    fixed_count += 1
            except Exception:
                failed_dates.append(date)
        
        self._update_data_status(symbol)
        
        return {
            'status': 'fixed' if not failed_dates else 'partial',
            'fixed_count': fixed_count,
            'failed_dates': failed_dates
        }
    
    def sync_today_data(self):
        today = datetime.now().strftime('%Y-%m-%d')
        results = {'success': [], 'failed': []}
        
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute('SELECT symbol FROM stocks')
        symbols = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        for symbol in symbols:
            success, msg = self.download_data(symbol, today, today)
            if success:
                results['success'].append(symbol)
            else:
                results['failed'].append({'symbol': symbol, 'error': msg})
        
        return results
    
    def schedule_sync(self, time='18:00'):
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            scheduler = BackgroundScheduler()
            scheduler.add_job(self.sync_today_data, 'cron', hour=int(time.split(':')[0]), 
                             minute=int(time.split(':')[1]))
            scheduler.start()
            return True, f"定时任务已设置，每天 {time} 执行"
        except ImportError:
            return False, "请安装 apscheduler: pip install apscheduler"
    
    def add_stock(self, symbol, name='', market='A', industry='', listed_date=''):
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM stocks WHERE symbol = ?', (symbol,))
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO stocks (symbol, name, market, industry, listed_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (symbol, name, market, industry, listed_date))
            conn.commit()
            conn.close()
            return True
        conn.close()
        return False
    
    def remove_stock(self, symbol):
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM stocks WHERE symbol = ?', (symbol,))
        cursor.execute('DELETE FROM daily_data WHERE symbol = ?', (symbol,))
        cursor.execute('DELETE FROM data_status WHERE symbol = ?', (symbol,))
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0