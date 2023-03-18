from functions.travel_time import travel_time

# Import the config file
from config import *
beta = BETA
gamma = GAMMA

class Route(object):
    '''
    Route class
    '''
    def __init__(self,bundle:list, restaurant_id:str):
        '''
        Initialize a route
        '''
        
        self.bundle = bundle # list of orders
        self.restaurant_id = restaurant_id # restaurant id
        self.beta = beta # controls the freshness in the construction of bundles, should be tuned
        self.gamma = gamma # controls the click-to-door time in the construction of bundles, should be tuned
        
    def get_ready_time(self):
        '''
        Get the ready time of the route
        '''
        
        ready_time = max([o.ready_time for o in self.bundle]) # ready time of the route is the latest ready time of the orders in the route's bundle
        
        return ready_time

    def get_total_travel_time(self, meters_per_minute, locations):
        '''
        Calculate the total travel time of the route from the 1st destination to the last destination
        - do not include pickup service time and drop off service time
        '''

        travel_points = [self.restaurant_id] + [o.id for o in self.bundle] # list of travel points

        if len(travel_points) == 1: # if there is only one travel point
            return 0 # return 0
        
        else: # if there are more than one travel points
            total_travel_time = 0 # initiate total travel time
            
            for i in range(len(travel_points)-1): # loop through all travel points except the first one
                total_travel_time += travel_time(travel_points[i], travel_points[i+1], meters_per_minute, locations) # add the travel time between the current travel point and the next travel point to the total travel time
            
            return total_travel_time # return the total travel time

    def get_end_position(self):
        '''
        Get the end position of the route
        '''

        end_position = self.bundle[-1].id # end position of the route is the last order in the route's bundle

        return end_position

    def get_total_service_delay(self, meters_per_minute, locations):
        '''
        Calculate the total service delay of the route
        '''
        
        travel_points = [self.restaurant_id]+ [o.id for o in self.bundle] # list of travel points
        
        if len(travel_points) == 1: # if there is only one travel point
            return 0 # return 0
        else:
            total_service_delay = 0 # initiate total service delay
            arrival_time_at_cp = self.get_ready_time() # initiate arrival time at customer place

            for i in range(len(travel_points)-1): # loop through all travel points except the first one
                arrival_time_at_cp += (travel_time(travel_points[i], travel_points[i+1], meters_per_minute, locations)) # add the travel time between the current travel point and the next travel point to the arrival time at customer place
                total_service_delay += (arrival_time_at_cp - self.bundle[i].ready_time) # add the service delay of the current order to the total service delay
                
            return total_service_delay

    def get_total_service_waiting(self,meters_per_minute,locations):
        '''
        Calculate the total service waiting of the route
        '''
        
        travel_points = [self.restaurant_id]+[o.id for o in self.bundle] # list of travel points

        if len(travel_points) == 1: # if there is only one travel point
            return 0 # return 0
        else: # if there are more than one travel points
            total_service_waiting = 0 # initiate total service waiting
            arrival_time_at_cp = self.get_ready_time() # initiate arrival time at customer place

            for i in range(len(travel_points)-1): # loop through all travel points except the first one
                arrival_time_at_cp += (travel_time(travel_points[i], travel_points[i+1], meters_per_minute, locations)) # add the travel time between the current travel point and the next travel point to the arrival time at customer place
                total_service_waiting += (arrival_time_at_cp - self.bundle[i].placement_time) # add the service waiting of the current order to the total service waiting
                
            return total_service_waiting

    def route_efficiency(self, meters_per_minute, locations):
        '''
        Calculate the route efficiency, orders per travel time
        '''
        
        # route efficiency = number of orders / total travel time
        route_efficiency = len(self.bundle) / self.get_total_travel_time(meters_per_minute, locations)
        
        return route_efficiency

    def get_route_cost(self, meters_per_minute, locations):
        '''
        Calculate the route cost
        '''
        
        # route cost = total travel time + beta * total service delay + gamma * total service waiting
        route_cost = self.get_total_travel_time(meters_per_minute, locations) + self.beta * self.get_total_service_delay(meters_per_minute, locations) + self.gamma * self.get_total_service_waiting(meters_per_minute, locations)
        
        return route_cost
