# RFT — Run From Text

**Flag:** `--rft`

Run From Text compresses the entire source with `zlib`, encodes it as `base64`, and produces a two-line loader that decompresses and `exec()`s the blob at runtime. No plain Python source is visible in the output.

## Output format

```python
import zlib as _z,base64 as _b
exec(_z.decompress(_b.b64decode(b'eJy...')).decode())
```

## Example

**Before:**

```python
def greet(name):
    print("Hello, " + name)

greet("world")
```

**After:**

```python
import zlib as _z,base64 as _b
exec(_z.decompress(_b.b64decode(b'eJxLy8kvLk4tLk4tKs1VSMsvyklRslIqS...')).decode())
```

## Notes

- RFT is a thin encoding layer — the original source can be recovered by decoding the blob. Use `--carbon` or `--mix-strings` before `--rft` to obfuscate the source before encoding.
- Stacking `--rft` then `--bcc` (the double-encode pattern) hides the `exec` call inside bytecode, making static recovery harder.
- No external dependencies are required at runtime (`zlib` and `base64` are stdlib).
- Compression level is set to maximum (`zlib` level 9), so the encoded blob is typically smaller than the original source.
