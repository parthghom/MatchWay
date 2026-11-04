# A KD-Tree (k-dimensional tree) is a space-partitioning data structure for organizing
# points in a k-dimensional space. In this 2D implementation, it alternates splitting
# the space by latitude and longitude at each level of the tree.
# This helps find nearby riders and drivers by pruning large sections of the search
# space that are mathematically guaranteed to be further than the target radius,
# reducing the search complexity from O(N) to average O(log N).

import math

def haversine_m(lat1, lon1, lat2, lon2):
    """Returns the distance between two points in metres."""
    R = 6371000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class KDNode:
    def __init__(self, lat, lon, item):
        self.lat = lat
        self.lon = lon
        self.item = item
        self.left = None
        self.right = None

class KDTree:
    def __init__(self):
        self.root = None
        self._size = 0

    def insert(self, lat, lon, item):
        """Inserts a point into the KD-Tree."""
        def _insert_rec(node, lat, lon, item, depth):
            if node is None:
                return KDNode(lat, lon, item)

            # Alternate splitting axis: 0 = lat, 1 = lon
            axis = depth % 2
            if axis == 0:
                if lat < node.lat:
                    node.left = _insert_rec(node.left, lat, lon, item, depth + 1)
                else:
                    node.right = _insert_rec(node.right, lat, lon, item, depth + 1)
            else:
                if lon < node.lon:
                    node.left = _insert_rec(node.left, lat, lon, item, depth + 1)
                else:
                    node.right = _insert_rec(node.right, lat, lon, item, depth + 1)
            return node

        self.root = _insert_rec(self.root, lat, lon, item, 0)
        self._size += 1

    def radius_search(self, lat, lon, radius_m):
        """Returns items within radius_m, sorted by distance."""
        results = []

        def _search_rec(node, depth):
            if node is None:
                return

            dist = haversine_m(lat, lon, node.lat, node.lon)
            if dist <= radius_m:
                results.append((dist, node.item))

            axis = depth % 2
            # Determine which side to visit first
            if axis == 0:
                diff = lat - node.lat
                near, far = (node.left, node.right) if diff < 0 else (node.right, node.left)
                plane_dist = abs(diff) * 111320
            else:
                diff = lon - node.lon
                near, far = (node.left, node.right) if diff < 0 else (node.right, node.left)
                plane_dist = abs(diff) * 111320 * math.cos(math.radians(lat))

            _search_rec(near, depth + 1)
            if plane_dist <= radius_m:
                _search_rec(far, depth + 1)

        _search_rec(self.root, 0)

        # Hand-written insertion sort for results
        for i in range(1, len(results)):
            key = results[i]
            j = i - 1
            while j >= 0 and results[j][0] > key[0]:
                results[j + 1] = results[j]
                j -= 1
            results[j + 1] = key

        return results

    def nearest(self, lat, lon):
        """Returns the closest point (distance, item)."""
        if self.root is None:
            raise ValueError("Tree is empty")

        self._best_dist = float('inf')
        self._best_item = None

        def _nearest_rec(node, depth):
            if node is None:
                return

            dist = haversine_m(lat, lon, node.lat, node.lon)
            if dist < self._best_dist:
                self._best_dist = dist
                self._best_item = node.item

            axis = depth % 2
            if axis == 0:
                diff = lat - node.lat
                near, far = (node.left, node.right) if diff < 0 else (node.right, node.left)
                plane_dist = abs(diff) * 111320
            else:
                diff = lon - node.lon
                near, far = (node.left, node.right) if diff < 0 else (node.right, node.left)
                plane_dist = abs(diff) * 111320 * math.cos(math.radians(lat))

            _nearest_rec(near, depth + 1)
            if plane_dist < self._best_dist:
                _nearest_rec(far, depth + 1)

        _nearest_rec(self.root, 0)
        return (self._best_dist, self._best_item)

    def size(self):
        return self._size
