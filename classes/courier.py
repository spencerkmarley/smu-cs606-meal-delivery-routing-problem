class Courier(object):
    def __init__(self, courier_information : dict, ):
        self.id = courier_information.get('courier')
        self.x = courier_information.get('x')
        self.y = courier_information.get('y')
        self.on_time = courier_information.get('on_time')
        self.off_time = courier_information.get('off_time')

        # Sequence of moves of the courier
        # Update and derived along the way
        self.assignments = []                           # containing assigned assigments 
        self.next_available_time = self.on_time                 # when the courier is available for the next assignment (or the drop off time of the last order of the last assignment)
        self.position_after_last_assignment = self.id  # the position of the courier after completing the last assignment           
