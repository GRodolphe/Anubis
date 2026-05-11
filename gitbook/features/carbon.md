# Carbon Identifier Renaming

**Flag:** `--carbon`

Carbon renames every user-defined identifier in the source to a random string composed only of the characters `I` (uppercase i) and `l` (lowercase L). These characters are visually identical in most monospace fonts, making the output extremely hard to read.

## What gets renamed

- Function and method names (except `__init__` and dunder methods)
- Class names
- Variable names (assignments and loop variables)
- Function parameters

## What is preserved

- Python keywords (`if`, `for`, `return`, …)
- Built-in names (`print`, `len`, `range`, …)
- Names bound by import statements (e.g. `import math` `math` is not renamed)
- Built-in type method names (`append`, `pop`, `split`, …) these are preserved to avoid breaking calls on standard library objects

## Example

**Before:**

```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(10))
```

**After:**

```python
def IlIlIlIIIl(IIlIllII):
    if IIlIllII <= 1:
        return 1
    return IIlIllII * IlIlIlIIIl(IIlIllII - 1)

print(IlIlIlIIIl(10))
```

## Notes

- Carbon strips all comments and docstrings before renaming.
- It is an offline pass no network requests are made.
- Names are unique within each run (no two identifiers get the same obfuscated name).
- Combine with `--mix-strings` and `--junk` for stronger obfuscation.
