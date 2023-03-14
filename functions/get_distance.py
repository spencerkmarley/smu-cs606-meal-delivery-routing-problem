def get_distance(source: tuple, destination : tuple) -> float:
    '''
    Get the distance between two points
    '''

    distance = ((source[1] - destination[1]) ** 2 + (source[0] - destination[0]) ** 2)**0.5 # calculate the distance between the source and the destination

    return distance
