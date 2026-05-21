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
            SELECT symbol, COUNT(*) as gaps 
            FROM data_status 
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
    
    def download_data(self, symbol, start_date, end_date, source='akshare'):
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
            
            df.to_sql('daily_data', conn, if_exists='append', index=False)
            
            self._update_stock_info(symbol, df)
            self._update_data_status(symbol)
            
            conn.commit()
            conn.close()
            
            return True, f"成功下载 {len(df)} 条数据"
        
        except Exception as e:
            return False, str(e)
    
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
            self.data_source = DataSourceFactory.create_source('akshare')
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
                    df['data_source'] = 'akshare'
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