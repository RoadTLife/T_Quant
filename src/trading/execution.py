class ExecutionEngine:
    def __init__(self, broker):
        self.broker = broker
        self.order_queue = []
    
    def submit_order(self, order):
        self.order_queue.append(order)
    
    def process_orders(self, current_price):
        executed_orders = []
        remaining_orders = []
        
        for order in self.order_queue:
            self.broker.set_price(current_price)
            if order['type'] == 'buy':
                if self.broker.get_cash() >= current_price * order['quantity']:
                    self.broker.place_order('buy', order['quantity'])
                    executed_orders.append(order)
                else:
                    remaining_orders.append(order)
            elif order['type'] == 'sell':
                if self.broker.get_position() >= order['quantity']:
                    self.broker.place_order('sell', order['quantity'])
                    executed_orders.append(order)
                else:
                    remaining_orders.append(order)
        
        self.order_queue = remaining_orders
        return executed_orders
    
    def get_pending_orders(self):
        return self.order_queue