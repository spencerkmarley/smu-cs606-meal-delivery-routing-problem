import argparse
import os, math, numpy as np
import pandas as pd
import copy
from collections import defaultdict

import classes as cls
from functions.read_instance_information import read_instance_information

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
    
    