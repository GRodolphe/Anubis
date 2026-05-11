# Constant Blinding

**Flag:** `--blind`

Replaces every integer literal in the source with an equivalent XOR expression. A magic number `N` becomes `(N^R)^R` where `R` is a random value chosen at obfuscation time. The expression evaluates to the original value at runtime but hides it from static inspection.

## How it works

For each `ast.Constant` node with an integer value:

1. A random 16-bit mask `R` is generated.
2. The constant `N` is replaced with the AST node `(N ^ R) ^ R`.
3. Because `(N ^ R) ^ R == N` for all integers, runtime behaviour is unchanged.

## Example

**Before:**

```python
PORT = 4444
TIMEOUT = 30
MAX_RETRIES = 3
```

**After:**

```python
PORT = (4444 ^ 19823) ^ 19823      # evaluates to 4444
TIMEOUT = (30 ^ 61204) ^ 61204     # evaluates to 30
MAX_RETRIES = (3 ^ 8971) ^ 8971    # evaluates to 3
```

## What it defeats

- **Grep/search for known constants** `grep "4444"` finds nothing.
- **YARA / signature rules** rules that match specific numeric values no longer fire.
- **Quick static inspection** ports, sizes, and magic numbers are not immediately visible.

## Notes

- Boolean values (`True`, `False`) are skipped they are integers in Python but must remain as-is.
- Values larger than `0xFFFF` (65535) are skipped to keep the mask values reasonable.
- Floating-point, complex, bytes, and string constants are not affected.
- Combine with `--xor-strings` to hide both string and numeric constants.
