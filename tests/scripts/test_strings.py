words = ["apple", "banana", "cherry", "date", "elderberry"]
result = ", ".join(words)
print(result)
print(result.upper())
print(len(words))

greeting = "hello"
name = "world"
message = greeting + " " + name
print(message)

parts = []
for w in words:
    parts.append(w[0].upper() + w[1:])
print(" ".join(parts))
