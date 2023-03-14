import numpy as np

def traveltime(origin_id, destination_id, meters_per_minute, locations):
    '''
    Calculate travel time between two points, the origin and the destination
    '''

    dist = np.sqrt((locations.at[destination_id, 'x'] - locations.at[origin_id, 'x'])**2\
                + (locations.at[destination_id, 'y'] - locations.at[origin_id, 'y'])**2) # calculate the distance between the origin and the destination
    
    tt = np.ceil(dist/meters_per_minute) # calculate the travel time between the origin and the destination
    
    return tt
