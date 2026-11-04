# This HashMap implementation uses a list of buckets with chaining for collision resolution.
# It uses a custom polynomial rolling hash for strings and identity for integers.
# The map dynamically resizes (doubles in capacity) when the load factor exceeds 0.75.

class Entry:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None

class HashMap:
    def __init__(self):
        self.capacity = 8
        self.buckets = [None] * self.capacity
        self._size = 0

    def _custom_hash(self, key):
        """Custom hash function avoiding built-in hash()."""
        if isinstance(key, int):
            val = key
        elif isinstance(key, str):
            val = 0
            for char in key:
                val = (val * 31) + ord(char)
        else:
            raise TypeError("HashMap only supports int and str keys")
        return val % self.capacity

    def put(self, key, value):
        """Inserts or updates a key-value pair."""
        if self._size / self.capacity > 0.75:
            self._resize()

        idx = self._custom_hash(key)
        entry = self.buckets[idx]

        while entry:
            if entry.key == key:
                entry.value = value
                return
            entry = entry.next

        # Key not found, add new entry to head of chain
        new_entry = Entry(key, value)
        new_entry.next = self.buckets[idx]
        self.buckets[idx] = new_entry
        self._size += 1

    def get(self, key):
        """Retrieves the value associated with the key."""
        idx = self._custom_hash(key)
        entry = self.buckets[idx]
        while entry:
            if entry.key == key:
                return entry.value
            entry = entry.next
        raise KeyError(f"Key {key} not found")

    def remove(self, key):
        """Removes the key-value pair from the map."""
        idx = self._custom_hash(key)
        entry = self.buckets[idx]
        prev = None

        while entry:
            if entry.key == key:
                if prev:
                    prev.next = entry.next
                else:
                    self.buckets[idx] = entry.next
                self._size -= 1
                return
            prev = entry
            entry = entry.next
        raise KeyError(f"Key {key} not found")

    def contains(self, key):
        """Returns True if the key exists in the map."""
        try:
            self.get(key)
            return True
        except KeyError:
            return False

    def size(self):
        """Returns the number of items in the map."""
        return self._size

    def keys(self):
        """Returns a list of all keys in the map."""
        all_keys = []
        for bucket in self.buckets:
            entry = bucket
            while entry:
                all_keys.append(entry.key)
                entry = entry.next
        return all_keys

    def _resize(self):
        """Doubles the capacity and re-hashes all entries."""
        old_buckets = self.buckets
        self.capacity *= 2
        self.buckets = [None] * self.capacity
        self._size = 0

        for bucket in old_buckets:
            entry = bucket
            while entry:
                self.put(entry.key, entry.value)
                entry = entry.next
