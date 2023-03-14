class Courier(object):
    '''
    Courier class
    '''
    def __init__(self, courier_information:dict):
        '''
        Initialize a courier
        '''

        self.id = courier_information.get('courier') # courier id
        self.x = courier_information.get('x') # courier x location
        self.y = courier_information.get('y') # courier y location
        self.on_time = courier_information.get('on_time') # courier on time
        self.off_time = courier_information.get('off_time') # courier off time

        # Sequence of moves of the courier, updated and derived along the way:
        self.assignments = [] # list of order assignments
        self.next_available_time = self.on_time # the next time the courier is available
        self.position_after_last_assignment = (self.x, self.y) # the position of the courier after the last assignment
