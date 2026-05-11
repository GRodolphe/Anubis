# XOR String Encryption

**Flag:** `--xor-strings`

Encrypts every plain string constant in the source with a random one-byte XOR key. A tiny decoder lambda is injected at the top of the file; each original string is replaced with a `decoder(b'...', key)` call that decrypts the value at runtime.

## How it works

1. A random key byte (1–255) is generated for the entire file.
2. Every `str` constant in the AST is XOR-encrypted: `encrypted[i] = ord(char[i]) ^ key`.
3. The constant is replaced with `_dec(b'\xNN\xNN...', key)` in the AST.
4. A one-liner decoder is prepended: `_dec = lambda b,k: ''.join(chr(c^k) for c in b)`.

The decoder name is a random `I`/`l` string it disappears into the noise when combined with `--carbon`.

## Example

**Before:**

```python
print("Hello, world!")
```

**After (conceptually):**

```python
_IlIlIlIl = lambda b, k: ''.join(chr(c ^ k) for c in b)
print(_IlIlIlIl(b'\x61\x64\x6c\x6c\x6f\x2c\x20\x77\x6f\x72\x6c\x63\x21', 0x29))
```

## Difference from `--mix-strings`

| | `--mix-strings` | `--xor-strings` |
|---|---|---|
| Encoding | `chr(N)` chains | XOR cipher with random key |
| Key required to decode | No trivially reversible | Yes key is embedded but non-obvious |
| Plaintext in .pyc | Yes (as integer constants) | No |
| Output size | Large (one `chr()` per character) | Compact (bytes literal) |

## Notes

- F-strings (`f"..."`) are skipped their internal structure is preserved.
- Strings longer than 200 characters are skipped to avoid oversized bytes literals.
- Non-ASCII strings (characters with `ord() > 127`) are skipped safely.
- Apply before `--bcc` so the encrypted strings are compiled into bytecode.
