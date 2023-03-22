from collections import defaultdict
import copy
import numpy as np
from typing import Tuple
from classes.assignment import Assignment
from classes.courier import Courier
from classes.order import Order
from classes.route import Route
from functions.read_instance_information import read_instance_information

# Import the config file
from config import *
f_minute = F_MINUTE
commitment_strategy = COMMITMENT_STRATEGY

class DeliveryRouting:
    def __init__(self, instance_dir:str):
        '''
        Initialize a delivery routing problem
        '''

        orders, restaurants, couriers, instanceparams, locations ,\
        self.meters_per_minute, self.pickup_service_minutes, self.dropoff_service_minutes, \
            self.target_click_to_door, self.pay_per_order,\
            self.guaranteed_pay_per_hour = read_instance_information(instance_dir) # read instance information from the instance directory

        # Orders
        self.orders = [Order(order) for order in orders.to_dict(orient = 'records')] # convert orders to Order class
        self.orders = sorted(self.orders, key = lambda x: x.id) # sort orders by id
        self.unassigned_orders = self.copy(self.orders) # unassigned orders
        self.orders_by_horizon_interval = defaultdict(list)

        # Restaurants
        self.restaurants = restaurants # set restaurants in the problem
        
        # Couriers
        self.couriers = [Courier(courier) for courier in couriers.to_dict(orient = 'records')] # convert couriers to Courier class
        
        # Locations
        self.locations = locations
    

    def travel_time(self, origin_id:str, destination_id:str):
        """
        Calculate the travel time between two locations.
        Args:
            origin_id (int): The id of the origin location.
            destination_id (int): The id of the destination location.
        Returns:
            float: The travel time between the origin and destination in minutes.
        """

        dist = np.sqrt((self.locations.at[destination_id, 'x'] - self.locations.at[origin_id, 'x'])**2\
                    + (self.locations.at[destination_id, 'y'] - self.locations.at[origin_id, 'y'])**2) # calculate the distance between the origin and the destination
        
        tt = np.ceil(dist/self.meters_per_minute) # calculate the travel time between the origin and the destination
        
        return tt

    def copy(self, x):
        '''
        This function is used to copy a list of objects
        '''
        
        return copy.deepcopy(x)

    def get_ready_orders(self) -> dict:
        '''
        This function return orders which have ready time fall into the corresponding horizon.
        This function should be run only once.
        '''
        t_list = [*range(0, 24*60+1, self.f)] # initiate the starting time of each interval
        
        for i in range(1, len(t_list)): # loop through each interval
            for o in self.orders: # loop through each order
                if o.placement_time < t_list[i] and o.placement_time >= t_list[i-1] and o.ready_time < t_list[i] + self.delta_u: # if the order placement time is within the interval and the order is ready within the assignemnt horizon
                    self.orders_by_horizon_interval[t_list[i]].append(o) # append the order to the corresponding horizon
                if o.placement_time < t_list[i] and o.placement_time >= t_list[i-1] and o.ready_time >= t_list[i] + self.delta_u: # if the order placement time is within the interval but the order is ready after the assignemnt horizon
                    self.orders_by_horizon_interval[t_list[i] + self.f * np.ceil((o.ready_time - (t_list[i] + self.delta_u))/self.f)].append(o) # append the order to a future horizon in which the order is ready.

    def get_ready_orders_at_t(self, t):
        '''
        This function return orders which have ready time fall into the corresponding horizon.
        '''

        return self.orders_by_horizon_interval[t]

    def get_idle_courier_at_t(self, t):
        '''
        Get idle couriers at time t
        '''
        idle_courier = [] # initiate a list of idle couriers

        for c in self.couriers: # loop through each courier
            if c.next_available_time < t + self.delta_u and c.next_available_time < c.off_time : # if the courier is next available within the assignment horizon and the courier is not off duty
                idle_courier.append(c) # append the courier to the list of idle couriers
        return idle_courier # return the list of idle couriers

    def get_bundle_size(self, t) -> int :
        '''
        Get the bundle size at time t
        '''
        number_of_orders = len(self.get_ready_orders_at_t(t)) # get the number of orders ready at time t
        number_of_couriers = len(self.get_idle_courier_at_t(t)) # get the number of idle couriers at time t
        
        if number_of_couriers == 0: # if there are no idle couriers
            bundle_size = 2 # default value of bundle size
        else:
            bundle_size = np.ceil(number_of_orders/number_of_couriers) # otherwise the bundle size is the number of orders divided by the number of idle couriers
        return bundle_size # return the bundle size

    def can_assign(self, t, courier, route : Route) -> bool:
        '''
        Check if a courier can take a bundle
        '''

        route_ready_time = route.get_ready_time() # get the ready time of the bundle
        
        if route_ready_time < courier.on_time: # if the ready time of the bundle is before the courier's on duty time
            return False # the courier cannot take the bundle
        if route_ready_time> courier.off_time: # if the ready time of the bundle is after the courier's off duty time
            return False # the courier cannot take the bundle
        
        arrival_time = max(t, courier.next_available_time) +\
                        self.dropoff_service_minutes/2 +\
                         self.travel_time(courier.position_after_last_assignment, route.restaurant_id) +\
                          self.pickup_service_minutes/2 # calculate the arrival time of the courier to the bundle's restaurant as the maximum of the current time and the courier's next available time plus the dropoff service time divided by 2, the travel time to the restaurant, and the pickup service time divided by 2
        
        if arrival_time > courier.off_time: # if the arrival time is after the courier's off duty time
            return False # the courier cannot take the bundle
        
        if len(courier.assignments) > 0: # if the courier has taken at least one bundle
            if courier.assignments[-1].isfinal_flag == 0: # if the last bundle the courier took is not final
                if courier.assignments[-1].restaurant_id != route.restaurant_id: # if the last bundle the courier took is not from the same restaurant as the current bundle
                    return False # the courier cannot take the bundle
        
        return True # otherwise the courier can take the bundle

    def assign_bundle(self, t:int, courier:Courier, route:Route):
        '''
        Assign a bundle to a courier
        '''

        arrival_time = max(t, courier.next_available_time) +\
                        self.dropoff_service_minutes/2 +\
                         self.travel_time(courier.position_after_last_assignment, route.restaurant_id) +\
                          self.pickup_service_minutes/2 # calculate the arrival time of the courier to the bundle's restaurant as the maximum of the current time and the courier's next available time plus the dropoff service time divided by 2, the travel time to the restaurant, and the pickup service time divided by 2

        route_ready_time = route.get_ready_time() # get the ready time of the bundle
        pickup_time = max(arrival_time, route_ready_time) # calculate the pickup time as the maximum of the arrival time and the ready time of the bundle
        assignment = Assignment(t, route.restaurant_id, courier, route) # create an assignment object
        
        assignment.pickup_time = pickup_time # set the pickup time of the assignment to the pickup time calculated above
        assignment.departure_time = max(t, courier.next_available_time) + self.dropoff_service_minutes/2 # set the departure time of the assignment to the maximum of the current time and the courier's next available time plus the dropoff service time divided by 2
        assignment.departure_location = courier.position_after_last_assignment # set the departure location of the assignment to the courier's position after the last assignment
        
        for i, order in enumerate(route.bundle): # loop through each order in the bundle
            order.pickup_time = pickup_time # set the pickup time of the order to the pickup time calculated above
            order.assign_time = t # set the assign time of the order to the current time
            order.courier_id = courier.id # set the courier id of the order to the courier's id
            
            if i == 0: # if the order is the first order in the bundle
                order.dropoff_time = pickup_time + self.pickup_service_minutes/2 +\
                                        self.travel_time(route.restaurant_id, order.id) +\
                                        self.dropoff_service_minutes/2 # set the dropoff time of the order to the pickup time plus the pickup service time divided by 2 plus the travel time from the restaurant to the order, and the dropoff service time divided by 2 
            else: # if the order is not the first order in the bundle
                order.dropoff_time = route.bundle[i-1].dropoff_time +\
                                        self.dropoff_service_minutes/2 +\
                                        self.travel_time(route.bundle[i-1].id, order.id) +\
                                        self.dropoff_service_minutes/2 # set the dropoff time of the order to the dropoff time of the previous order plus the dropoff service time divided by 2 plus the travel time from the previous order to the current order, and the dropoff service time divided by 2

        ## Commitment strategy
        # If the courier, c, can reach the restaurant, r, before time t + f, and all orders in the bundle, b, are estimated to be ready by t + f,
        # Then make a final commitment of the courier to the bundle - instruct the courer to travel to the restaurant, pick up and deliver the orders in the bundle.

        if (arrival_time <= t + f_minute and route_ready_time <= t + f_minute) or\
           (route_ready_time <= t + f_minute and route_ready_time <= arrival_time): # if the arrival time is before the current time plus f minutes and the ready time of the bundle is before the current time plus f minutes or the ready time of the bundle is before the arrival time
            
            
            assignment.isfinal_flag = 1
            
            if len(courier.assignments) > 0:
                # if the last assignment can be updated
                # the last assignment can be updated if its isfinal_flag = 0
                if courier.assignments[-1].isfinal_flag == 0:
                    # Combine bundle
                    courier.assignments[-1].update(assignment,self.meters_per_minute,self.locations) # the old courier.assignments[-1] is combined with the new assignment to become new courier.assignments[-1]
                    courier.assignments[-1].pickup_time = max(arrival_time,courier.assignments[-1].route.get_ready_time())
                    courier.next_available_time = courier.assignments[-1].pickup_time +  self.pickup_service_minutes/2 +\
                                                    courier.assignments[-1].route.get_total_travel_time(self.meters_per_minute,self.locations) +\
                                                     self.dropoff_service_minutes*(len(courier.assignments[-1].route.bundle)-1) +\
                                                      self.dropoff_service_minutes/2     
                    courier.position_after_last_assignment = courier.assignments[-1].route.get_end_position(self.meters_per_minute,self.locations)
                    # update order attributes:
                    for i, order in enumerate(courier.assignments[-1].route.bundle):
                        order.pickup_time = pickup_time
                        order.courier_id = courier.id
                        if i == 0:
                            order.dropoff_time = pickup_time + self.pickup_service_minutes/2 +\
                                                    self.travel_time(courier.assignments[-1].restaurant_id,order.id) +\
                                                    self.dropoff_service_minutes/2 
                        else:
                            order.dropoff_time = courier.assignments[-1].route.bundle[i-1].dropoff_time +\
                                                    self.dropoff_service_minutes/2 +\
                                                    self.travel_time(courier.assignments[-1].route.bundle[i-1].id,order.id) +\
                                                    self.dropoff_service_minutes/2
                else: # if the last assignment can not be updated
                    courier.assignments.append(assignment)
                    courier.next_available_time = courier.assignments[-1].pickup_time +  self.pickup_service_minutes/2 +\
                                                        courier.assignments[-1].route.get_total_travel_time(self.meters_per_minute,self.locations) +\
                                                     self.dropoff_service_minutes*(len(courier.assignments[-1].route.bundle)-1) +\
                                                      self.dropoff_service_minutes/2
                    courier.position_after_last_assignment = courier.assignments[-1].route.get_end_position(self.meters_per_minute,self.locations)
            else: 
                courier.assignments.append(assignment)
                courier.next_available_time = courier.assignments[-1].pickup_time +  self.pickup_service_minutes/2 +\
                                                        courier.assignments[-1].route.get_total_travel_time(self.meters_per_minute,self.locations) +\
                                                     self.dropoff_service_minutes*(len(courier.assignments[-1].route.bundle)-1) +\
                                                      self.dropoff_service_minutes/2
                courier.position_after_last_assignment = courier.assignments[-1].route.get_end_position(self.meters_per_minute,self.locations)
        
        else:
            if commitment_strategy == 0:
                assignment.isfinal_flag = 1
            else:
                assignment.isfinal_flag = 0
            
            if len(courier.assignments) > 0:
                # if the last assignment can be updated
                # the last assignment can be updated if its isfinal_flag = 0
                if courier.assignments[-1].isfinal_flag == 0:
                    # Combine bundle
                    courier.assignments[-1].update(assignment,self.meters_per_minute,self.locations) # the old courier.assignments[-1] is combined with the new assignment to become new courier.assignments[-1]
                    courier.assignments[-1].pickup_time = max(arrival_time,courier.assignments[-1].route.get_ready_time())
                    if courier.assignments[-1].isfinal_flag == 1:
                        courier.next_available_time = courier.assignments[-1].pickup_time +  self.pickup_service_minutes/2 +\
                                                        courier.assignments[-1].route.get_total_travel_time(self.meters_per_minute,self.locations) +\
                                                     self.dropoff_service_minutes*(len(courier.assignments[-1].route.bundle)-1) +\
                                                      self.dropoff_service_minutes/2
                        courier.position_after_last_assignment = courier.assignments[-1].route.get_end_position(self.meters_per_minute,self.locations)
                    else:
                        pass
                    # update order attributes:
                    for i, order in enumerate(courier.assignments[-1].route.bundle):
                        order.pickup_time = pickup_time
                        order.courier_id = courier.id
                        if i == 0:
                            order.dropoff_time = pickup_time + self.pickup_service_minutes/2 +\
                                                    self.travel_time(courier.assignments[-1].restaurant_id,order.id) +\
                                                    self.dropoff_service_minutes/2 
                        else:
                            order.dropoff_time = courier.assignments[-1].route.bundle[i-1].dropoff_time +\
                                                    self.dropoff_service_minutes/2 +\
                                                    self.travel_time(courier.assignments[-1].route.bundle[i-1].id,order.id) +\
                                                    self.dropoff_service_minutes/2
                else: # if the last assignment can not be updated
                    courier.assignments.append(assignment)
                    if courier.assignments[-1].isfinal_flag == 1:
                        courier.next_available_time = courier.assignments[-1].pickup_time +  self.pickup_service_minutes/2 +\
                                                        courier.assignments[-1].route.get_total_travel_time(self.meters_per_minute,self.locations) +\
                                                     self.dropoff_service_minutes*(len(courier.assignments[-1].route.bundle)-1) +\
                                                      self.dropoff_service_minutes/2
                        courier.position_after_last_assignment = courier.assignments[-1].route.get_end_position(self.meters_per_minute,self.locations)
            else: 
                courier.assignments.append(assignment)
                if courier.assignments[-1].isfinal_flag == 1:
                    courier.next_available_time = courier.assignments[-1].pickup_time +  self.pickup_service_minutes/2 +\
                                                        courier.assignments[-1].route.get_total_travel_time(self.meters_per_minute,self.locations) +\
                                                     self.dropoff_service_minutes*(len(courier.assignments[-1].route.bundle)-1) +\
                                                      self.dropoff_service_minutes/2
                    courier.position_after_last_assignment = courier.assignments[-1].route.get_end_position(self.meters_per_minute,self.locations)

    def initialization(self, t:int, ready_orders: list, idle_couriers: list, bundle_size: int):
        list_of_routes_by_restaurant = []
        if not ready_orders:
            # print('b1')
            return  list_of_routes_by_restaurant
        else:
            # print('b2')
            for r_id in self.restaurants['restaurant']:
                # print(r_id)
                
                # build set of ready orders from restaurant r
                r_order= []
                for o in ready_orders:
                    if o.restaurant_id == r_id:
                        r_order.append(o)
                # print(r_order)
                # get number of bundel for restaurant r
                number_of_bundle = int(np.ceil(len(r_order)/bundle_size))
                # Initiate emptly lists
                set_of_bundles = [[] for _ in range(number_of_bundle)]
                
                # Assign orders into bundels:
                for o in r_order:
                    min_cost_increase = float('inf')
                    for i in range(number_of_bundle):
                        n = len(set_of_bundles[i])
                        if n + 1<= bundle_size:
                            #print('x')
                            min_route_cost = float('inf')
                            for pos in range(n+1):
                                set_of_bundles[i].insert(pos,o)
                                if Route(set_of_bundles[i], r_id).get_route_cost(self.meters_per_minute,self.locations) < min_route_cost:
                                    min_route_cost = Route(set_of_bundles[i], r_id).get_route_cost(self.meters_per_minute,self.locations)
                                    best_pos = pos
                                set_of_bundles[i].pop(pos)
                        else: # if existing size + 1 > bundle size and insertion decreases route efficiency then
                              # Disregard s for order o and finnd the next best route and insertion position
                            #print('o')
                            min_route_cost = float('inf')
                            for pos in range(n+1):
                                set_of_bundles[i].insert(pos,o)
                                if Route(set_of_bundles[i], r_id).get_route_cost(self.meters_per_minute,self.locations) < min_route_cost:
                                    min_route_cost = Route(set_of_bundles[i], r_id).get_route_cost(self.meters_per_minute,self.locations)
                                    best_pos = pos
                                set_of_bundles[i].pop(pos)
                            # get current efficiency
                            current_efficiency = n / Route(set_of_bundles[i],r_id).get_total_travel_time(self.meters_per_minute,self.locations)
                            # get new efficiency
                            set_of_bundles[i].insert(best_pos,o)
                            new_efficiency = (n+1) / Route(set_of_bundles[i],r_id).get_total_travel_time(self.meters_per_minute,self.locations)
                            if current_efficiency < new_efficiency:
                                set_of_bundles[i].pop(best_pos)
                            else: 
                                set_of_bundles[i].pop(best_pos)
                                continue 

                        current_cost = Route(set_of_bundles[i],r_id).get_route_cost(self.meters_per_minute,self.locations)
                        set_of_bundles[i].insert(best_pos, o)
                        new_cost = Route(set_of_bundles[i],r_id).get_route_cost(self.meters_per_minute,self.locations)
                        cost_increase = new_cost - current_cost
                        if cost_increase < min_cost_increase:
                            min_cost_increase = cost_increase
                            best_i = i
                            best_i_pos = best_pos
                        set_of_bundles[i].pop(best_pos)

                    # Assign o the best bundle and the best position within that bundle
                    set_of_bundles[best_i].insert(best_i_pos,o)
                
                set_of_bundles = [Route(bundle,r_id) for bundle in set_of_bundles]
                if set_of_bundles:
                    list_of_routes_by_restaurant.append(set_of_bundles)

            return list_of_routes_by_restaurant 
    

    #### Local Search ####
    def get_restaurant_cost(self, res:list): 
        res_cost = 0
        for route in res:
            res_cost += route.get_route_cost(self.meters_per_minute,self.locations)
        return res_cost
    
    def get_total_restaurant_cost(self, list_of_routes_by_restaurant:list): 
        total_res_cost = 0
        for res in list_of_routes_by_restaurant:
            for route in res:
                total_res_cost += route.get_route_cost(self.meters_per_minute,self.locations)
        return total_res_cost

    def driver_code(self):
        final_result = defaultdict(list) # initialize the final result
        self.get_ready_orders() # get the ready orders
        t_list = [*range(0, 24*60+1, self.f)] # get the time horizon

        for t in t_list: # loop through the time horizon
            ready_orders = self.get_ready_orders_at_t(t) # get the ready orders at time t
            idle_couriers = self.get_idle_courier_at_t(t) # get the idle couriers at time t
            bundle_size = int(self.get_bundle_size(t)) # get the bundle size at time t
            list_of_routes_by_restaurant = self.initialization(t, ready_orders, idle_couriers, bundle_size) # get the list of routes by restaurant
            final_result[t] = list_of_routes_by_restaurant # add the list of routes by restaurant to the final result

        final_result = {k:v for k,v in final_result.items() if len(v)>0} # remove the empty time slots
        self.final_result = final_result
        # return final_result

    def objective(self):
        self.total_cost = 0
        for time, routes in self.final_result.items():
            for route in routes:
                for bundle in route:
                    self.total_cost += bundle.get_route_cost(self.meters_per_minute,self.locations)
        return self.total_cost

    def local_search(self, list_of_routes_by_restaurant):
        # get current total cost: 
        current_total_res_cost = self.get_total_restaurant_cost(list_of_routes_by_restaurant)

        # perform local search
        for res in list_of_routes_by_restaurant:
            # cur = [o.id for route in res for o in route.bundle]
            # if len(cur)>1:
            #     print('Cur:', cur)
            # get current route cost
            current_cost = self.get_restaurant_cost(res)
            for route1 in res:
                for i in range(len(route1.bundle)):
                    best_route = route1
                    best_pos = i
                    # remove order at position i
                    o = route1.bundle.pop(i)
                    # find the best route and position to reinsert order o
                    for route2 in res:
                        for j in range(len(route2.bundle)+1):
                            # insert order at position j
                            route2.bundle.insert(j,o)
                            # try_c = [o.id for route in res for o in route.bundle]
                            # if len(try_c)>1:
                            #     print('Try:', try_c)
                            # get new cost
                            new_cost = self.get_restaurant_cost(res)
                            # if new cost is less than current cost then record the new position
                            if new_cost < current_cost:
                                current_cost = new_cost
                                best_route = route2
                                best_pos = j

                            route2.bundle.pop(j)
                    # insert order at best position
                    best_route.bundle.insert(best_pos,o)
        # delete route has no orders
        for res_index in range(len(list_of_routes_by_restaurant)):
            list_of_routes_by_restaurant[res_index] = [route for route in list_of_routes_by_restaurant[res_index] if  len(route.bundle)!= 0]
             
        # get new total cost
        new_total_res_cost = self.get_total_restaurant_cost(list_of_routes_by_restaurant)
        # if new_total_res_cost != current_total_res_cost:
        #     print('Old cost: ', current_total_res_cost)
        #     print('New cost: ', new_total_res_cost)
        return list_of_routes_by_restaurant