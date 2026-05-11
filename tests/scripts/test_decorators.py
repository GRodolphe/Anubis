def repeat(times):
    def decorator(func):
        def wrapper(*args, **kwargs):
            results = []
            for _ in range(times):
                results.append(func(*args, **kwargs))
            return results

        return wrapper

    return decorator


def memoize(func):
    cache = {}

    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]

    return wrapper


@repeat(3)
def greet(name):
    return "Hello, " + name + "!"


@memoize
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)


results = greet("Alice")
for r in results:
    print(r)

for i in range(10):
    print(fib(i))
