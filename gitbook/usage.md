# Usage

## Interactive mode

Run `anubis` with no arguments to be prompted through every option step-by-step:

```bash
anubis
```

## CLI mode

Pass the target file and any combination of flags:

```bash
anubis script.py [flags...]
```

The obfuscated output is written to `script-obf.py` in the same directory.

## Flag reference

| Flag | Description |
|---|---|
| `--antidebug` | Inject anti-debugger thread (cross-platform) |
| `--junk` | Wrap code in unreachable junk class definitions |
| `--mix-strings` | Replace string literals with `chr()` chains |
| `--big-script` | Inflate output with ~256 KB of random dead-code blobs |
| `--carbon` | Rename identifiers offline |
| `--import-alias` | Obfuscate imported module names with random aliases |
| `--encrypt` | AES-encrypt source into a self-decrypting one-liner (requires `ancrypt`) |
| `--rft` | RFT: encode source as `zlib+base64` blob and `exec()` at runtime |
| `--bcc` | BCC: compile to bytecode, `marshal+zlib+base64` encode into a loader stub |
| `--compile` | Compile final output to a standalone exe with Nuitka |
| `--version` | Print version and exit |

## Pipeline order

When multiple flags are combined, passes always run in this fixed order:

```
junk → antidebug → junk → carbon → mix-strings → import-alias
→ big-script → encrypt → rft → bcc
```

## Examples

```bash
# Rename identifiers + add junk
anubis script.py --carbon --junk

# Full protection: junk + anti-debug + rename + encrypt
anubis script.py --junk --antidebug --carbon --mix-strings --encrypt

# Bytecode compilation (hardest to decompile)
anubis script.py --carbon --mix-strings --bcc

# Double-encode: RFT then BCC
anubis script.py --carbon --rft --bcc

# Inflate + rename + alias imports + compile to exe
anubis script.py --big-script --carbon --import-alias --compile
```

## Notes

- `--encrypt` and `--compile` are mutually exclusive.
- `--bcc` produces Python-version-specific bytecode — run the output on the same Python version used to obfuscate.
- Flags can be combined freely; the pipeline order above is always preserved regardless of the order you specify them.
