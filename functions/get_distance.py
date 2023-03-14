def get_distance(source: tuple, destination : tuple) -> float:
    return ((source[1] - destination[1]) ** 2 + (source[0] - destination[0]) ** 2)**0.5
