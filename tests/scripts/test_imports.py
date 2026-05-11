import math
import hashlib

values = [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]
for v in values:
    print(math.sqrt(v))

text = "anubis obfuscator"
digest = hashlib.sha256(text.encode()).hexdigest()
print(digest)

print(math.gcd(48, 18))
print(math.lcm(4, 6))
print(round(math.pi, 5))
