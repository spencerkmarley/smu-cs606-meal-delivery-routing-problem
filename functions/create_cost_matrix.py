from scipy.optimize import linear_sum_assignment
import numpy as np

def create_cost_matrix(self, t: int, idle_couriers: list, list_of_routes_by_restaurant: list) -> np.ndarray:
        n_couriers = len(idle_couriers)
        flat_list_of_bundles = [bundle for routes in list_of_routes_by_restaurant for bundle in routes]
        n_bundles = len(flat_list_of_bundles)

        cost_matrix = np.zeros((n_couriers, n_bundles))

        for i, courier in enumerate(idle_couriers):
            for j, bundle in enumerate(flat_list_of_bundles):
                cost_matrix[i, j] = bundle.get_route_cost(self.meters_per_minute, self.locations)  # Calculate the cost of assigning courier i to bundle

        return cost_matrix

# Add the following lines to driver_code()
#if idle_couriers and list_of_routes_by_restaurant:
#                cost_matrix = self.create_cost_matrix(t, idle_couriers, list_of_routes_by_restaurant)
#                row_ind, col_ind = linear_sum_assignment(cost_matrix)
#
#                # Assign bundles to couriers
#                assigned_bundles = []
#                flat_list_of_bundles = [bundle for routes in list_of_routes_by_restaurant for bundle in routes]
#                for i, j in zip(row_ind, col_ind):
#                    assigned_bundles.append((idle_couriers[i], flat_list_of_bundles[j]))
#                final_result[t] = assigned_bundles