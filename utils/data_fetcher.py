import pandas as pd
import os

class DataFetcher:
    def __init__(self, data_dir='data/raw'):
        self.data_dir = data_dir
    
    def fetch_from_csv(self, filename):
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        df = pd.read_csv(filepath)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        return df
    
    def save_to_csv(self, df, filename):
        filepath = os.path.join(self.data_dir, filename)
        df.to_csv(filepath)
    
    def generate_sample_data(self, days=365, start_date='2023-01-01'):
        dates = pd.date_range(start=start_date, periods=days, freq='D')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(days) * 0.5)
        
        df = pd.DataFrame({
            'open': prices,
            'high': prices + np.random.rand(days) * 2,
            'low': prices - np.random.rand(days) * 2,
            'close': prices,
            'volume': np.random.randint(1000, 10000, days)
        }, index=dates)
        
        return df