class Broker:
    def __init__(self, initial_capital=100000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.position = 0
        self.current_price = 0
        self.trades = []
        self.portfolio_history = {'date': [], 'value': []}
    
    def reset(self):
        self.cash = self.initial_capital
        self.position = 0
        self.trades = []
        self.portfolio_history = {'date': [], 'value': []}
    
    def set_price(self, price):
        self.current_price = price
    
    def place_order(self, order_type, quantity):
        if order_type == 'buy':
            cost = self.current_price * quantity
            if cost <= self.cash:
                self.cash -= cost
                self.position += quantity
                self._record_trade('buy', quantity, self.current_price)
        elif order_type == 'sell':
            if quantity <= self.position:
                proceeds = self.current_price * quantity
                self.cash += proceeds
                self.position -= quantity
                self._record_trade('sell', quantity, self.current_price)
    
    def _record_trade(self, trade_type, quantity, price):
        trade = {
            'type': trade_type,
            'quantity': quantity,
            'price': price,
            'date': None,
            'profit': 0
        }
        if trade_type == 'sell' and self.trades:
            buy_trades = [t for t in self.trades if t['type'] == 'buy' and t['profit'] == 0]
            if buy_trades:
                buy_trade = buy_trades[-1]
                buy_trade['profit'] = (price - buy_trade['price']) * quantity
                trade['profit'] = buy_trade['profit']
        self.trades.append(trade)
    
    def update_portfolio(self, date):
        portfolio_value = self.cash + self.position * self.current_price
        self.portfolio_history['date'].append(date)
        self.portfolio_history['value'].append(portfolio_value)
    
    def get_position(self):
        return self.position
    
    def get_cash(self):
        return self.cash
    
    def get_portfolio_value(self):
        return self.cash + self.position * self.current_price