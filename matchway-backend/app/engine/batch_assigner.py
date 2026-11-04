# The BatchAssigner optimally matches groups of riders (VirtualRooms) to available drivers.
# Using a bipartite matching algorithm (Kuhn's algorithm) is superior to a greedy
# "nearest-driver-first" approach because it maximizes the total number of matches.
# A greedy choice might assign the only available driver to a room that has other
# options, potentially leaving another room without any possible driver. Bipartite
# matching finds the global optimum via augmenting paths.

from app.engine.bipartite_graph import BipartiteGraph
from app.engine.hash_map import HashMap
from app.engine.driver_dispatch import DriverDispatcher
from app.engine.kd_tree import haversine_m

class BatchAssigner:
    def assign(self, dispatcher, rooms, radius_m=3000):
        """
        Assigns available drivers to rooms to maximize the total number of matches.
        rooms: list of (room_id, vehicle_type, lat, lon)
        """
        bg = BipartiteGraph()

        # 1. Add rooms as right nodes
        for room_id, vehicle_type, lat, lon in rooms:
            bg.add_right(room_id)

        # 2. Add free drivers as left nodes
        driver_ids = dispatcher.drivers.keys()
        for d_id in driver_ids:
            driver = dispatcher.drivers.get(d_id)
            if not driver.is_busy:
                bg.add_left(d_id)

        # 3. Add edges based on vehicle type and distance
        for room_id, r_vehicle, r_lat, r_lon in rooms:
            for d_id in driver_ids:
                driver = dispatcher.drivers.get(d_id)
                if not driver.is_busy and driver.vehicle_type == r_vehicle:
                    dist = haversine_m(driver.latitude, driver.longitude, r_lat, r_lon)
                    if dist <= radius_m:
                        bg.add_edge(d_id, room_id)

        # 4. Calculate maximum matching
        matching = bg.max_matching()

        # 5. Mark matched drivers as busy
        results = []
        for d_id, room_id in matching:
            driver = dispatcher.drivers.get(d_id)
            driver.is_busy = True
            dispatcher.drivers.put(d_id, driver)
            results.append((room_id, d_id))

        return results
