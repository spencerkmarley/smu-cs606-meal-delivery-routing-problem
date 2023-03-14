import os
import pandas as pd

# Read instance information
def read_instance_information(instance_dir):
    orders=pd.read_table(os.path.join(instance_dir,'orders.txt'))
    restaurants=pd.read_table(os.path.join(instance_dir,'restaurants.txt'))
    couriers=pd.read_table(os.path.join(instance_dir,'couriers.txt'))
    instanceparams=pd.read_table(os.path.join(instance_dir,'instance_parameters.txt'))

    order_locations=pd.DataFrame(data=[orders.order,orders.x,orders.y]).transpose()
    order_locations.columns=['id','x','y']
    restaurant_locations=pd.DataFrame(data=[restaurants.restaurant,restaurants.x,restaurants.y]).transpose()
    restaurant_locations.columns=['id','x','y']
    courier_locations=pd.DataFrame(data=[couriers.courier,couriers.x,couriers.y]).transpose()
    courier_locations.columns=['id','x','y']
    locations=pd.concat([order_locations,restaurant_locations,courier_locations])
    locations.set_index('id',inplace=True)

    meters_per_minute=instanceparams.at[0,'meters_per_minute']
    pickup_service_minutes=instanceparams.at[0,'pickup service minutes']
    dropoff_service_minutes=instanceparams.at[0,'dropoff service minutes']
    target_click_to_door=instanceparams.at[0,'target click-to-door']
    pay_per_order=instanceparams.at[0,'pay per order']
    guaranteed_pay_per_hour=instanceparams.at[0,'guaranteed pay per hour']

    return orders,restaurants,couriers,instanceparams,locations, meters_per_minute, pickup_service_minutes, dropoff_service_minutes, \
            target_click_to_door, pay_per_order,\
            guaranteed_pay_per_hour