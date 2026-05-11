def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)


def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


for i in range(1, 11):
    print(factorial(i))

primes = [n for n in range(2, 50) if is_prime(n)]
print(primes)
