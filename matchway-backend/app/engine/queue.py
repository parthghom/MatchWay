# This Queue implementation uses a singly linked list of nodes.
# It maintains references to the head (for dequeue/peek) and tail (for enqueue)
# to ensure all operations run in O(1) time.

class Node:
    def __init__(self, item):
        self.item = item
        self.next = None

class Queue:
    def __init__(self):
        self.head = None
        self.tail = None
        self._size = 0

    def enqueue(self, item):
        """Adds an item to the end of the queue."""
        new_node = Node(item)
        if self.is_empty():
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node
        self._size += 1

    def dequeue(self):
        """Removes and returns the item from the front of the queue."""
        if self.is_empty():
            raise IndexError("dequeue from empty queue")

        item = self.head.item
        self.head = self.head.next
        if self.head is None:
            self.tail = None
        self._size -= 1
        return item

    def peek(self):
        """Returns the item at the front of the queue without removing it."""
        if self.is_empty():
            raise IndexError("peek from empty queue")
        return self.head.item

    def is_empty(self):
        """Returns True if the queue contains no items."""
        return self.head is None

    def size(self):
        """Returns the number of items in the queue."""
        return self._size
