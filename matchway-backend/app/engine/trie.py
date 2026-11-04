# This Trie implementation stores sequences of stops (routes) to efficiently
# find riders sharing overlapping paths. By organizing routes hierarchically,
# we can find all riders sharing a prefix of stops in O(L) time where L is
# the route length, regardless of the total number of riders in the system.

from app.engine.hash_map import HashMap

class TrieNode:
    def __init__(self):
        # Store children as a HashMap: {stop_name: TrieNode}
        self.children = HashMap()
        # List of riders whose routes pass through this stop
        self.rider_ids = []

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, route, rider_id):
        """Adds a rider to every node along the specified route."""
        node = self.root
        # Add to root as well (optional, but represents the start of all routes)
        node.rider_ids.append(rider_id)

        for stop in route:
            if not node.children.contains(stop):
                node.children.put(stop, TrieNode())
            node = node.children.get(stop)
            node.rider_ids.append(rider_id)

    def riders_with_prefix(self, route):
        """Returns rider_ids whose routes start with the given prefix of stops."""
        node = self.root
        for stop in route:
            if not node.children.contains(stop):
                return []
            node = node.children.get(stop)

        # Return a copy of the list at the final node of the prefix
        return list(node.rider_ids)

    def longest_common_prefix(self, route):
        """Returns the number of stops from the start of the route that exist in the trie."""
        node = self.root
        count = 0
        for stop in route:
            if not node.children.contains(stop):
                break
            node = node.children.get(stop)
            count += 1
        return count

    def remove(self, route, rider_id):
        """Removes a rider from every node along the specified route."""
        node = self.root
        if rider_id in node.rider_ids:
            node.rider_ids.remove(rider_id)

        for stop in route:
            if not node.children.contains(stop):
                break
            node = node.children.get(stop)
            if rider_id in node.rider_ids:
                node.rider_ids.remove(rider_id)
