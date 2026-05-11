# Big Script

**Flag:** `--big-script`

Big Script inflates the obfuscated output to approximately **256 KB** by prepending a large number of random byte-blob variable assignments. These variables are never referenced and have no effect at runtime.

## Purpose

Static analysis tools often prioritize smaller files. A bloated file is slower to load in decompilers and harder to navigate manually. The random blobs also prevent simple compression-based analysis.

## How it works

Random variable names (prefixed with `_`) are assigned random `bytes` literals until the prepended block reaches the target size (~256 KB). Example:

```python
_xkzqabcdef1234 = b'\xde\xad\xbe\xef...'
_mqwrtyuiop5678 = b'\x00\xff\x12\x34...'
# ... hundreds more ...

# your actual obfuscated code below
```

## Notes

- The blobs are optimised away entirely if the output is subsequently compiled with `--bcc` (bytecode compilation discards unreferenced constants).
- Use `--big-script` before `--rft` or `--bcc` if you want the inflation to survive in the final output.
- The exact size varies slightly depending on random blob lengths (each blob is 120–400 bytes).
