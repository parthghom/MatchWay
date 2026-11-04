# This MinHeap implementation uses a plain Python list as a binary heap.
# It maintains the min-heap property where the parent node is always smaller than or equal to its children.
# push() uses sift-up to maintain the property, and pop() uses sift-down.

class MinHeap:
    def __init__(self):
        # Store elements as tuples of (priority, item)
        self.heap = []

    def push(self, priority, item):
        """Adds a new item with a given priority to the heap."""
        self.heap.append((priority, item))
        self._sift_up(len(self.heap) - 1)

    def pop(self):
        """Removes and returns the item with the smallest priority."""
        if self.is_empty():
            raise IndexError("pop from empty heap")

        # If only one element, just pop it
        if len(self.heap) == 1:
            return self.heap.pop()

        # Swap root with the last element
        root = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._sift_down(0)
        return root

    def peek(self):
        """Returns the item with the smallest priority without removing it."""
        if self.is_empty():
            raise IndexError("peek from empty heap")
        return self.heap[0]

    def is_empty(self):
        """Returns True if the heap contains no items."""
        return len(self.heap) == 0

    def size(self):
        """Returns the number of items in the heap."""
        return len(self.heap)

    def _sift_up(self, index):
        parent = (index - 1) // 2
        if index > 0 and self.heap[index][0] < self.heap[parent][0]:
            self.heap[index], self.heap[parent] = self.heap[parent], self.heap[index]
            self._sift_up(parent)

    def _sift_down(self, index):
        smallest = index
        left = 2 * index + 1
        right = 2 * index + 2

        if left < len(self.heap) and self.heap[left][0] < self.heap[smallest][0]:
            smallest = left

        if right < len(self.heap) and self.heap[right][0] < self.heap[smallest][0]:
            smallest = right

        if smallest != index:
            self.heap[index], self.heap[smallest] = self.heap[smallest], self.heap[index]
            self._sift_down(smallest)
