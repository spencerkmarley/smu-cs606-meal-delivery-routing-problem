from functions.travel_time import travel_time

# Import the config file
from config import *
beta = BETA
gamma = GAMMA

class Route(object):
    def __init__(self,bundle : list, restaurant_id : str): 
        self.bundle = bundle 
        self.restaurant_id = restaurant_id
        
        # Hyperparameters
        self.beta = 5 
        self.gamma = 10
        
    def get_ready_time(self):
        ready_time = max([o.ready_time for o in self.bundle])
        return ready_time

    # calculate total travel time from 1st destination to the last destination of the route
    # do not include pickup service time and drop off service time
    def get_total_travel_time(self,meters_per_minute,locations):
        travel_points = [self.restaurant_id]+ [o.id for o in self.bundle]
        if len(travel_points) == 1:
            return 0
        else:
            total_travel_time = 0
            for i in range(len(travel_points)-1):
                total_travel_time += travel_time(travel_points[i], travel_points[i+1],meters_per_minute,locations)
            return total_travel_time

    def get_end_position(self,meters_per_minute,locations):
        return self.bundle[-1].id

    # calculate total service delay 
    # service delay = arrival_time at customer place - ready time (ignoring pickup service time and dropoff service time)
    def get_total_service_delay(self,meters_per_minute,locations):
        travel_points = [self.restaurant_id]+ [o.id for o in self.bundle]
        if len(travel_points) == 1:
            return 0
        else:
            total_service_delay = 0
            arrival_time_at_cp = self.get_ready_time()
            for i in range(len(travel_points)-1):
                arrival_time_at_cp += (travel_time(travel_points[i], travel_points[i+1],meters_per_minute,locations))
                total_service_delay += (arrival_time_at_cp - self.bundle[i].ready_time)
            return total_service_delay

    # calculate total_click_to_door 
    # click_to_door = arrival_time at customer place - placement time (ignoring pickup service time and dropoff service time)
    # the below function implement 
    def get_total_service_waiting(self,meters_per_minute,locations):
        travel_points = [self.restaurant_id]+[o.id for o in self.bundle]
        if len(travel_points) == 1:
            return 0
        else:
            total_service_waiting = 0
            arrival_time_at_cp = self.get_ready_time()
            for i in range(len(travel_points)-1):
                arrival_time_at_cp += (travel_time(travel_points[i], travel_points[i+1],meters_per_minute,locations))
                total_service_waiting += (arrival_time_at_cp - self.bundle[i].placement_time)
            return total_service_waiting

    # calculate route efficiency: travel time per order:
    def route_efficiency(self,meters_per_minute,locations):
        return len(self.bundle) / self.get_total_travel_time(meters_per_minute,locations)

    # calculate route cost
    def get_route_cost(self,meters_per_minute,locations):
        route_cost = self.get_total_travel_time(meters_per_minute,locations) + self.beta * self.get_total_service_delay(meters_per_minute,locations) + self.gamma * self.get_total_service_waiting(meters_per_minute,locations)
        return route_cost
