from classes.route import Route

# Import the config file
from config import *
x = X

class Assignment():
    '''
    Assignment class
    '''
    def __init__(self, assign_time:int , restaurant_id:str, courier:object, route:Route):
        '''
        Initialize an assignment
        '''
        self.assign_time = assign_time # assignment time
        self.restaurant_id = restaurant_id # restaurant id
        self.pickup_time = 0 # order pickup time
        self.courier = courier # assigned courier
        self.route = route # assigned route
        self.isfinal_flag = 0 # indicate if the assignment is final i.e. it cannot be updated
        self.update_time = 0 # the time that the assignment is updated

    def update(self, new_assignment, meters_per_minute, locations):
        '''
        Update the assignment with orders from a new bundle
        '''

        for o in new_assignment.route.bundle:
            n = len(self.route.bundle) # number of orders in the current bundle
            min_route_cost = float('inf') # initiate minimum route cost
            best_pos = 0 # initiate best position

            for pos in range(n+1): # loop through all possible positions to insert the order
                self.route.bundle.insert(pos, o) # insert the order to the current bundle
                route_cost = self.route.get_route_cost(meters_per_minute, locations) # calculate the route cost

                if route_cost < min_route_cost: # if the route cost is smaller than the minimum route cost:
                    min_route_cost = route_cost # update the minimum route cost
                    best_pos = pos # update the minimum route cost and the best position
                
                self.route.bundle.pop(pos) # otherwise remove the order from the current bundle

            self.route.bundle.insert(best_pos, o) # insert the order to the current bundle at the best position

        if new_assignment.isfinal_flag == 1: # if the new assigment is final (isfinal_flag = 1)
            self.isfinal_flag = 1 # set isfinal_flag of the combination as 1
        else: # if the new assigment is not final (isfinal_flag = 0)
            if not self.is_no_order_long_ready_time(): # if there is an order that has been ready for x minutes:
                self.isfinal_flag = 1 # mark the assignment as final
            else: # if there is no order that has been ready for x minutes:
                self.isfinal_flag = 0 # mark the assignment as not final
        
        self.update_time +=1 # increment the counter of the number of updates
        self.assign_time = new_assignment.assign_time # update the time of the last assignment

        return self

    def is_no_order_long_ready_time(self, x=x) -> bool:
        '''
        Check if there no orders will take x or more minutes to be ready
        '''

        for o in self.route.bundle:
            route_ready_time = self.route.bundle.get_ready_time()
            if route_ready_time - o.ready_time >= x:
                return False
        
        return True
