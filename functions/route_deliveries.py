from classes.deliveryrouting import DeliveryRouting
from collections import defaultdict

def route_deliveries(instance_dir):

    dr = DeliveryRouting(instance_dir) # initialize a delivery routing problem
    dr.get_ready_orders() # get the ready orders
    t_list = [*range(0, 24*60+1, dr.f)] # get the time horizon
    final_result = defaultdict(list) # initialize the final result
    
    for t in t_list: # loop through the time horizon
        ready_orders = dr.get_ready_orders_at_t(t) # get the ready orders at time t
        idle_couriers = dr.get_idle_courier_at_t(t) # get the idle couriers at time t
        bundle_size = int(dr.get_bundle_size(t)) # get the bundle size at time t
        list_of_routes_by_restaurant = dr.initialization(t, ready_orders, idle_couriers, bundle_size) # get the list of routes by restaurant
        final_result[t] = list_of_routes_by_restaurant # add the list of routes by restaurant to the final result

    final_result = {k:v for k,v in final_result.items() if len(v)>0} # remove the empty time slots

    return dr, final_result 
