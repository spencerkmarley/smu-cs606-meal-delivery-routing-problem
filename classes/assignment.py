from classes.route import Route

class Assignment():
    def __init__(self, assign_time : int , restaurant_id : str, courier: object, route : Route):
        self.assign_time = assign_time
        self.restaurant_id = restaurant_id  # each assignment of a bundle has only one corresponding restaurant
        self.pickup_time = 0
        self.courier = courier
        self.route = route
        self.isfinal_flag = 0 # indicate if the assignment is final (can not be updated)
        self.update_time = 0

    def update(self, new_assignment, meters_per_minute,locations):
        # update the new assignment into the old assignment
        # combine orders in the new assigment with orders in the old assignment
        for o in new_assignment.route.bundle:
            n = len(self.route.bundle)
            min_route_cost = float('inf')
            best_pos = 0
            for pos in range(n+1):
                self.route.bundle.insert(pos,o)
                route_cost = self.route.get_route_cost(meters_per_minute,locations)
                if route_cost < min_route_cost:
                    min_route_cost = route_cost
                    best_pos = pos
                self.route.bundle.pop(pos)
            self.route.bundle.insert(best_pos, o)
        # if the new assigment is final (isfinal_flage = 1), set isfinal_flag of the combination as 1
        if new_assignment.isfinal_flag == 1:
            self.isfinal_flag = 1
        else: # if the new assigment is not final (isfinal_flage = 0)
            # if there is an order that has been ready for x minutes, set assignment as final
            if not self.is_no_order_long_ready_time():
                self.isfinal_flag = 1
            else: # if there is no order that has been ready for x minutes, set assignment as tentative
                self.isfinal_flag = 0
        self.update_time +=1
        self.assign_time = new_assignment.assign_time

    def is_no_order_long_ready_time(self, x = 40) -> bool:
        for o in self.route.bundle:
            route_ready_time = self.route.bundle.get_ready_time()
            if route_ready_time - o.ready_time >= x:
                return False
        return True