class Node:
    def __init__(self, value):
        self.value = value
        self.next = None


class LinkedList:
    def __init__(self):
        self.head = None
        self._size = 0

    def append(self, value):
        node = Node(value)
        if self.head is None:
            self.head = node
        else:
            current = self.head
            while current.next is not None:
                current = current.next
            current.next = node
        self._size += 1

    def prepend(self, value):
        node = Node(value)
        node.next = self.head
        self.head = node
        self._size += 1

    def remove(self, value):
        if self.head is None:
            return
        if self.head.value == value:
            self.head = self.head.next
            self._size -= 1
            return
        current = self.head
        while current.next is not None:
            if current.next.value == value:
                current.next = current.next.next
                self._size -= 1
                return
            current = current.next

    def to_list(self):
        result = []
        current = self.head
        while current is not None:
            result.append(current.value)
            current = current.next
        return result

    def size(self):
        return self._size


ll = LinkedList()
for n in [1, 2, 3, 4, 5]:
    ll.append(n)

ll.prepend(0)
ll.remove(3)

print(ll.to_list())
print(ll.size())

ll2 = LinkedList()
for n in range(10, 0, -1):
    ll2.prepend(n)
print(ll2.to_list())
