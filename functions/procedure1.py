from classes.deliveryrouting import DeliveryRouting
from collections import defaultdict

def procedure1(instance_dir):

    dr = DeliveryRouting(instance_dir)
    dr.get_ready_orders()
    t_list = [*range(0, 24*60+1, dr.f)]
    final_result = defaultdict(list)
    for t in t_list:
        ready_orders = dr.get_ready_orders_at_t(t)
        idle_couriers = dr.get_idle_courier_at_t(t)
        bundle_size = int(dr.get_bundle_size(t))
        list_of_routes_by_restaurant = dr.initialization(t,ready_orders,idle_couriers,bundle_size)
        final_result[t] = list_of_routes_by_restaurant
    final_result = {k:v for k,v in final_result.items() if len(v)>0}

    return final_result 
