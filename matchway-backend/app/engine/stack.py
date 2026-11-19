# This Stack uses a singly linked list of nodes.
# The top is the head of the list, so push, pop and peek all run in O(1) time.
# Walking from the top gives the newest item first, which is exactly what a
# "history" screen wants.

class Node:
    def __init__(self, item):
        self.item = item
        self.next = None

class Stack:
    def __init__(self):
        self.top = None
        self._size = 0

    def push(self, item):
        """Puts an item on top of the stack."""
        node = Node(item)
        node.next = self.top
        self.top = node
        self._size += 1

    def pop(self):
        """Removes and returns the item on top."""
        if self.is_empty():
            raise IndexError("pop from empty stack")
        item = self.top.item
        self.top = self.top.next
        self._size -= 1
        return item

    def peek(self):
        """Returns the item on top without removing it."""
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self.top.item

    def is_empty(self):
        return self._size == 0

    def size(self):
        return self._size

    def to_list(self, limit=None):
        """Items from the top (newest) down. `limit` stops after that many."""
        out = []
        node = self.top
        while node is not None and (limit is None or len(out) < limit):
            out.append(node.item)
            node = node.next
        return out

    def trim(self, max_size):
        """Cuts the bottom of the stack so only the newest `max_size` items stay."""
        if self._size <= max_size:
            return
        if max_size <= 0:
            self.top = None
            self._size = 0
            return
        node = self.top
        for _ in range(max_size - 1):
            node = node.next
        node.next = None
        self._size = max_size
