class BaseStrategy:
    def __init__(self):
        self.broker = None
        self.data = None
        self.signals = []
    
    def set_broker(self, broker):
        self.broker = broker
    
    def set_data(self, data):
        self.data = data
    
    def on_bar(self, data):
        raise NotImplementedError("Subclasses must implement on_bar method")
    
    def buy(self, quantity=1):
        if self.broker:
            self.broker.place_order('buy', quantity)
            self.signals.append(('buy', self.data.index[-1]))
    
    def sell(self, quantity=1):
        if self.broker:
            self.broker.place_order('sell', quantity)
            self.signals.append(('sell', self.data.index[-1]))
    
    def get_signals(self):
        return self.signals