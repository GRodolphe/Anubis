# BCC — Bytecode Compilation

**Flag:** `--bcc`

Bytecode Compilation compiles the source to a Python code object, serialises it with `marshal`, compresses the result with `zlib`, and encodes it as `base64`. The output is a three-line loader stub that reverses the process and `exec()`s the code object.

## Output format

```python
import marshal as _m,zlib as _z,base64 as _b
exec(_m.loads(_z.decompress(_b.b64decode(b'eJw...'))))
```

## Why it is hard to decompile

Standard decompilers (`uncompyle6`, `decompile3`, `pycdc`) work on `.pyc` files — they expect a file header with a magic number and timestamp. BCC's output has neither: it is a raw marshalled code object wrapped in `zlib+base64`. Most decompilers cannot handle this format without a custom unpacking step.

## Compatibility

The bytecode produced by `compile()` is specific to the **Python version that runs Anubis**. The obfuscated file must be executed on the same major.minor version (e.g. code compiled with Python 3.12 will not run on Python 3.11).

## Recommended combinations

```bash
# Maximum source-level obfuscation before BCC
anubis script.py --carbon --junk --mix-strings --bcc

# Double-encode: compress source as text first, then compile the loader to bytecode
anubis script.py --carbon --rft --bcc
```

## Notes

- No external dependencies at runtime (`marshal`, `zlib`, `base64` are stdlib).
- BCC discards unreferenced constants — `--big-script` blobs are removed if applied before BCC.
- Apply `--big-script` **after** BCC is not possible in the current pipeline; use `--rft` between `--big-script` and `--bcc` if you want blob inflation to survive.
