import argparse
import json

from functions.read_instance_information import *
from functions.procedure1 import *
from functions.analysis import *

from config import *
f = F
delta_u = DELTA_U
beta = BETA
gamma = GAMMA

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--instance_dir', type=str, default='0o50t75s1p100')
    args = parser.parse_args()

    instance_dir = 'data/' + str(args.instance_dir)

    orders,restaurants,couriers,instanceparams,locations, meters_per_minute, pickup_service_minutes, dropoff_service_minutes, \
            target_click_to_door, pay_per_order,\
            guaranteed_pay_per_hour=read_instance_information(instance_dir)
    
    dr, final_result = procedure1(instance_dir)
    obj = json.loads(json.dumps(str(final_result), indent=4))
    with open(str(instance_dir) + '/final_result.json', 'w') as f:
        f.write(obj)

    orders_list(dr, final_result, orders, locations)
