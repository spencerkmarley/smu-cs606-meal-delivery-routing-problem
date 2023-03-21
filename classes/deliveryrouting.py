from collections import defaultdict
import copy
import numpy as np
from typing import Tuple
from classes.assignment import Assignment
from classes.courier import Courier
from classes.order import Order
from classes.route import Route
from functions.read_instance_information import read_instance_information

class DeliveryRouting:
    def __init__(self, instance_dir : str):

        orders, restaurants, couriers, instanceparams, locations ,\
        self.meters_per_minute, self.pickup_service_minutes, self.dropoff_service_minutes, \
            self.target_click_to_door, self.pay_per_order,\
            self.guaranteed_pay_per_hour = read_instance_information(instance_dir)


        self.orders = [Order(order) for order in orders.to_dict(orient = 'records')]
        self.orders = sorted(self.orders, key = lambda x: x.id)

        self.restaurants = restaurants
        self.couriers = [Courier(courier) for courier in couriers.to_dict(orient = 'records')]
        self.unassigned_orders = self.copy(self.orders)
        
        self.orders_by_horizon_interval = defaultdict(list)
        self.locations = locations

        # Hyperparameters
        self.f = 5
        self.delta_u = 10


    def travel_time(self, origin_id,destination_id):
        dist=np.sqrt((self.locations.at[destination_id,'x']-self.locations.at[origin_id,'x'])**2\
                    +(self.locations.at[destination_id,'y']-self.locations.at[origin_id,'y'])**2)
        tt=np.ceil(dist/self.meters_per_minute)
        return tt

    def copy(self,x):
        return copy.deepcopy(x)

    def get_ready_orders(self) -> dict:
        '''
        This function return orders which have ready time fall into the corresponding horizon.
        This function should be run only once.
        '''
        # starting time of each interval
        t_list = [*range(0,24*60+1,self.f)]
        # get ready orders correspoding to each horizon interval
        for i in range(1,len(t_list)):
            for o in self.orders:
                if o.placement_time < t_list[i] and o.placement_time >= t_list[i-1] and o.ready_time < t_list[i]+self.delta_u:
                    self.orders_by_horizon_interval[t_list[i]].append(o)
                if o.placement_time < t_list[i] and o.placement_time >= t_list[i-1] and o.ready_time >= t_list[i]+self.delta_u:
                    self.orders_by_horizon_interval[t_list[i]+self.f*np.ceil((o.ready_time - (t_list[i]+self.delta_u))/self.f)].append(o)

    def get_ready_orders_at_t(self,t):
        return self.orders_by_horizon_interval[t]

    def get_idle_courier_at_t(self,t):
        idle_courier = []
        for c in self.couriers:
            if c.next_available_time < t+self.delta_u and c.next_available_time < c.off_time :
                idle_courier.append(c)
        return idle_courier

    def get_bundle_size(self, t) -> int :
        
        number_of_orders = len(self.get_ready_orders_at_t(t))
        number_of_couriers = len(self.get_idle_courier_at_t(t))
        if number_of_couriers == 0:
            bundle_size = 2 # default value of bundle size
        else:
            bundle_size = np.ceil(number_of_orders/number_of_couriers)
        return bundle_size

    # check if the courier can take a bundle. 
    def can_assign(self, t, courier, route : Route) -> bool:
        route_ready_time = route.get_ready_time()
        if route_ready_time < courier.on_time:
            return False
        if route_ready_time> courier.off_time:
            return False
        if len(courier.assignments) > 0:
            if courier.assignments[-1].isfinal_flag == 0:
                if courier.assignments[-1].restaurant_id != route.restaurant_id:
                    return False
        return True

    # assign a bundle to a courier
    def assign_bundle(self, t: int, courier: Courier, route: Route):
        # calculate courier's arrival time to the bundle's restaurant:
        arrival_time = courier.next_available_time +\
                        self.dropoff_service_minutes/2 +\
                         self.travel_time(courier.position_after_last_assignment,route.restaurant_id) +\
                          self.pickup_service_minutes/2
        route_ready_time = route.get_ready_time()
        pickup_time = max(arrival_time,route_ready_time)
        assignment = Assignment(t, route.restaurant_id, courier, route)
        # update order attributes:
        for i, order in enumerate(route.bundle):
            order.pickup_time = pickup_time
            order.courier_id = courier.id
            if i == 0:
                order.dropoff_time = pickup_time + self.pickup_service_minutes/2 +\
                                        self.travel_time(route.restaurant_id,order.id) +\
                                        self.dropoff_service_minutes/2 
            else:
                order.dropoff_time = route.bundle[i-1].dropoff_time +\
                                        self.dropoff_service_minutes/2 +\
                                        self.travel_time(route.bundle[i-1].id,order.id) +\
                                        self.dropoff_service_minutes/2

        ### Commitment strategy
        # If d can reach restaurant r before t + f and all orders in s are estimated to be ready by t + f,
        # make a final commitment of d to s: instruct d to travel to rs, pick up and deliver orders in s.
        if arrival_time <= t+self.f and route_ready_time <= t+self.f:
            assignment.isfinal_flag = 1
            assignment.pickup_time = pickup_time
            
            if len(courier.assignments) > 0:
                # if the last assignment can be updated
                # the last assignment can be updated if its isfinal_flag = 0
                if courier.assignments[-1].isfinal_flag == 0:
                    # Combine bundle
                    courier.assignments[-1].update(assignment,self.meters_per_minute,self.locations) # the old courier.assignments[-1] is combined with the new assignment to become new courier.assignments[-1]
                    courier.assignments[-1].pickup_time = max(arrival_time,courier.assignments[-1].route.get_ready_time())
                    courier.next_available_time = courier.assignments[-1].pickup_time +  self.pickup_service_minutes/2 +\
                                                    courier.assignments[-1].route.get_total_travel_time(self.meters_per_minute,self.locations) +  self.dropoff_service_minutes/2     
                    courier.position_after_last_assignment = courier.assignments[-1].route.get_end_position(self.meters_per_minute,self.locations)
                else: # if the last assignment can not be updated
                    courier.assignments.append(assignment)
                    courier.next_available_time = courier.assignments[-1].pickup_time +  self.pickup_service_minutes/2 +\
                                                        courier.assignments[-1].route.get_total_travel_time(self.meters_per_minute,self.locations) +  self.dropoff_service_minutes/2
                    courier.position_after_last_assignment = courier.assignments[-1].route.get_end_position(self.meters_per_minute,self.locations)
            else: 
                courier.assignments.append(assignment)
                courier.next_available_time = courier.assignments[-1].pickup_time +  self.pickup_service_minutes/2 +\
                                                        courier.assignments[-1].route.get_total_travel_time(self.meters_per_minute,self.locations)+  self.dropoff_service_minutes/2
                courier.position_after_last_assignment = courier.assignments[-1].route.get_end_position(self.meters_per_minute,self.locations)
        
        else:
            assignment.isfinal_flag = 0
            assignment.pickup_time = pickup_time
            if len(courier.assignments) > 0:
                # if the last assignment can be updated
                # the last assignment can be updated if its isfinal_flag = 0
                if courier.assignments[-1].isfinal_flag == 0:
                    # Combine bundle
                    courier.assignments[-1].update(assignment,self.meters_per_minute,self.locations) # the old courier.assignments[-1] is combined with the new assignment to become new courier.assignments[-1]
                    courier.assignments[-1].pickup_time = max(arrival_time,courier.assignments[-1].route.get_ready_time())
                    if courier.assignments[-1].isfinal_flag == 1:
                        courier.next_available_time = courier.assignments[-1].pickup_time +  self.pickup_service_minutes/2 +\
                                                        courier.assignments[-1].route.get_total_travel_time(self.meters_per_minute,self.locations) +  self.dropoff_service_minutes/2
                        courier.position_after_last_assignment = courier.assignments[-1].route.get_end_position(self.meters_per_minute,self.locations)
                    else:
                        pass
                else: # if the last assignment can not be updated
                    courier.assignments.append(assignment)
            else: 
                courier.assignments.append(assignment)

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