# An Interval Tree is a specialized binary search tree used to store intervals.
# It is ordered by the start time of the intervals. To optimize overlap queries,
# each node stores the maximum 'end' value found in its subtree (max_end).
# This allows us to prune entire subtrees during a search if the subtree's
# maximum end time is smaller than the query's start time, making it efficient
# to find riders or drivers with compatible travel-time windows.

class Node:
    def __init__(self, start, end, item):
        self.start = start
        self.end = end
        self.item = item
        self.max_end = end
        self.left = None
        self.right = None

class IntervalTree:
    def __init__(self):
        self.root = None
        self._size = 0

    def insert(self, start, end, item):
        """Inserts an interval into the tree."""
        if start > end:
            raise ValueError("Start time cannot be greater than end time")

        def _insert_rec(node, start, end, item):
            if node is None:
                self._size += 1
                return Node(start, end, item)

            # Update max_end on the way down
            if end > node.max_end:
                node.max_end = end

            if start < node.start:
                node.left = _insert_rec(node.left, start, end, item)
            else:
                node.right = _insert_rec(node.right, start, end, item)

            return node

        self.root = _insert_rec(self.root, start, end, item)

    def overlap_search(self, start, end):
        """Returns a list of items whose intervals overlap with [start, end]."""
        results = []

        def _search_rec(node):
            if node is None:
                return

            # Pruning: search left child only if it exists and its max_end >= query start
            if node.left and node.left.max_end >= start:
                _search_rec(node.left)

            # Check current node: a_start <= b_end AND b_start <= a_end
            if node.start <= end and start <= node.end:
                results.append(node.item)

            # Pruning: search right child only if it exists and query end >= node start
            if node.right and end >= node.start:
                _search_rec(node.right)

        _search_rec(self.root)
        return results

    def size(self):
        """Returns total number of intervals in the tree."""
        return self._size
