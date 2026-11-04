# A Bipartite Graph is a graph whose vertices can be divided into two disjoint
# sets (left and right) such that every edge connects a vertex in the left set
# to one in the right set. In our system, left nodes are drivers and right nodes
# are riders.
#
# Augmenting paths are paths that start and end at unmatched vertices,
# alternating between unmatched and matched edges. By repeatedly finding
# augmenting paths and "flipping" them (matching the unmatched edges and
# unmatching the matched ones), we increase the size of the matching.
#
# This is used to optimally match drivers to riders after filtering by
# constraints (like gender or capacity), ensuring the maximum number
# of people get a ride.

from app.engine.hash_map import HashMap

class BipartiteGraph:
    def __init__(self):
        # Maps left_id -> list of right_id neighbors
        self.adj = HashMap()
        # Set of all left nodes
        self.left_nodes = []
        # Set of all right nodes
        self.right_nodes = []
        # HashMap to check if a node exists (simulating a set)
        self.left_exists = HashMap()
        self.right_exists = HashMap()

    def add_left(self, node_id):
        if not self.left_exists.contains(node_id):
            self.left_nodes.append(node_id)
            self.left_exists.put(node_id, True)
            self.adj.put(node_id, [])

    def add_right(self, node_id):
        if not self.right_exists.contains(node_id):
            self.right_nodes.append(node_id)
            self.right_exists.put(node_id, True)

    def add_edge(self, left_id, right_id):
        if not self.left_exists.contains(left_id):
            raise KeyError(f"Left node {left_id} not added")
        if not self.right_exists.contains(right_id):
            raise KeyError(f"Right node {right_id} not added")

        neighbors = self.adj.get(left_id)
        # Ignore duplicates
        if right_id not in neighbors:
            neighbors.append(right_id)
            self.adj.put(left_id, neighbors)

    def neighbors(self, left_id):
        if not self.left_exists.contains(left_id):
            raise KeyError(f"Left node {left_id} not found")
        return self.adj.get(left_id)

    def max_matching(self):
        """Computes maximum bipartite matching using Kuhn's algorithm."""
        # match_r: right_id -> left_id
        match_r = HashMap()
        for r_node in self.right_nodes:
            match_r.put(r_node, None)

        def dfs(u, visited):
            for v in self.neighbors(u):
                if not visited.contains(v):
                    visited.put(v, True)
                    # If v is unmatched or we can find an augmenting path for its current match
                    matched_u = match_r.get(v)
                    if matched_u is None or dfs(matched_u, visited):
                        match_r.put(v, u)
                        return True
            return False

        matching_count = 0
        for u in self.left_nodes:
            visited = HashMap()
            if dfs(u, visited):
                matching_count += 1

        # Convert match_r to list of (left, right) pairs
        pairs = []
        for r_node in self.right_nodes:
            u = match_r.get(r_node)
            if u is not None:
                pairs.append((u, r_node))
        return pairs

    def size(self):
        return len(self.left_nodes) + len(self.right_nodes)
