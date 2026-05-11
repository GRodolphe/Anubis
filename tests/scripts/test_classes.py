class Stack:
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        return self._items.pop()

    def peek(self):
        return self._items[-1]

    def is_empty(self):
        return len(self._items) == 0

    def size(self):
        return len(self._items)


s = Stack()
for v in [10, 20, 30, 40, 50]:
    s.push(v)

print(s.size())
print(s.peek())

while not s.is_empty():
    print(s.pop())
