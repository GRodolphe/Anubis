# Dynamic Imports

**Flag:** `--dynamic-imports`

Replaces every `import X` statement with an assignment that calls `__import__()` with the module name XOR-encoded. The `import` keyword disappears from the source; the module name is never a plain string.

## How it works

1. A random one-byte XOR key is generated.
2. Each `import X` (or `import X as Y`) line is matched and the module name `X` is XOR-encoded.
3. The statement is replaced with `X = __import__(decoder(b'...', key))`.
4. A one-liner decoder is prepended to the file.

`from X import Y` forms are left intact — they are harder to rewrite safely without full dependency analysis.

## Example

**Before:**

```python
import os
import sys
import socket as sock
```

**After (conceptually):**

```python
_dec = lambda b, k: ''.join(chr(c ^ k) for c in b)
os = __import__(_dec(b'\x6c\x70', 0x03))        # 'os' XOR'd with 0x03
sys = __import__(_dec(b'\x70\x7a\x70', 0x03))   # 'sys' XOR'd with 0x03
sock = __import__(_dec(b'\x70\x6c\x62...', 0x03))
```

## What it defeats

- **`grep "import os"`** — no `import` keyword appears for these modules.
- **Static dependency scanners** — tools that enumerate imports by parsing `import` statements find nothing.
- **String search for module names** — `os`, `sys`, `socket` etc. don't appear as plain text.

## Notes

- Each run uses a fresh random key, so output differs between runs.
- `from X import Y` is unchanged — combine with `--import-alias` for partial coverage.
- The decoder name is a random `I`/`l` string that blends in when combined with `--carbon`.
- Module dotted names (`import os.path`) are encoded in full.
