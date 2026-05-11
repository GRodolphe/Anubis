# AES Encrypt

**Flag:** `--encrypt`

The AES Encrypt pass encrypts the entire source using AES-256-CBC and produces a self-decrypting one-liner. The encryption key is embedded in the output file and decryption happens at runtime via the `ancrypt` native extension.

## Output format

```python
import ancrypt
ancrypt.load(__file__)
'''
<wall><key><wall><iv><wall><ciphertext><wall>
'''
```

`ancrypt.load()` reads the triple-quoted block, extracts the key and IV, decrypts the ciphertext, and `exec()`s the result.

## Building ancrypt

The `ancrypt` extension must be compiled once and shipped alongside the obfuscated file:

```bash
uv run --group dev python setup.py build_ext --inplace
# → ancrypt.cpython-3XX-linux-gnu.so  (Linux)
# → ancrypt.cpython-3XX-darwin.so     (macOS)
# → ancrypt.cpython-3XX-win_amd64.pyd (Windows)
```

Place the resulting `.so` / `.pyd` file in the same directory as the obfuscated script before distributing.

## Key details

- Key derivation: `SHA-256` hash of a 32-byte random key (generated fresh each obfuscation run)
- Cipher: `AES-256-CBC` via `pycryptodome`
- The key is stored inside the output file this protects against casual inspection but not against a determined attacker who reads the source

## Limitations

- `--encrypt` and `--compile` (Nuitka) are mutually exclusive.
- The runtime machine must have the correct `ancrypt` binary for its Python version and platform.
- Use `--bcc` or `--rft` as lighter alternatives if distributing `ancrypt` is inconvenient.
