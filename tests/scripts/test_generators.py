def fibonacci(limit):
    a, b = 0, 1
    while a <= limit:
        yield a
        a, b = b, a + b


def squares(iterable):
    for item in iterable:
        yield item * item


def take(n, iterable):
    count = 0
    for item in iterable:
        if count >= n:
            break
        yield item
        count += 1


for val in fibonacci(200):
    print(val)

nums = list(range(1, 11))
for sq in squares(nums):
    print(sq)

for val in take(5, fibonacci(1000)):
    print(val)
