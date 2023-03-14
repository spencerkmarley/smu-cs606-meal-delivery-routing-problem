class Order:
    def __init__(self, order_information : dict):

        self.id = order_information.get('order')
        self.destination = (order_information.get('x'), order_information.get('y'))
        self.placement_time = order_information.get('placement_time')
        self.restaurant_id = order_information.get('restaurant')
        self.ready_time = order_information.get('ready_time')
        
        # To be updated after assignment
        self.pickup_time = 0
        self.dropoff_time = 0
        self.courier_id = ""
