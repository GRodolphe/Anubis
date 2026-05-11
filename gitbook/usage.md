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

The obfuscated output is written to `script-obf.py` in the same directory (override with `-o`).

## Flag reference

### Source transforms

| Flag | Description |
|---|---|
| `--antidebug` | Inject anti-debugger thread (cross-platform) |
| `--junk` | Wrap code in unreachable junk class definitions |
| `--flatten` | Rewrite function bodies as `while True` state machines |
| `--opaque` | Wrap functions in always-true guards with dead branches |
| `--mix-strings` | Replace string literals with `chr()` chains |
| `--xor-strings` | XOR-encrypt string literals with a random key |
| `--blind` | Replace integer literals `N` with `(N^R)^R` for random R |
| `--big-script` | Inflate output with ~256 KB of random dead-code blobs |
| `--carbon` | Rename identifiers to random `I`/`l` strings |
| `--semantic-noise` | Rename identifiers to misleading English names (LLM resistance) |
| `--import-alias` | Obfuscate imported module names with random aliases |
| `--dynamic-imports` | Replace `import X` with XOR-encoded `__import__()` calls |

### Encoding / compilation

| Flag | Description |
|---|---|
| `--encrypt` | AES-encrypt source into a self-decrypting one-liner (requires `ancrypt`) |
| `--rft` | RFT: encode source as `zlib+base64` blob and `exec()` at runtime |
| `--bcc` | BCC: compile to bytecode, `marshal+zlib+base64` encode into a loader stub |
| `--compile` | Compile final output to a standalone exe with Nuitka |

### Other

| Flag | Description |
|---|---|
| `-o PATH` / `--output PATH` | Write output to this path instead of `<input>-obf.py` |
| `--ci` | CI/CD mode: no interactive prompts, plain stdout, exit 1 on error |
| `--version` | Print version and exit |

## Pipeline order

When multiple flags are combined, passes always run in this fixed order:

```
junk → antidebug → junk → flatten → opaque
→ carbon → semantic-noise
→ mix-strings → xor-strings → blind
→ import-alias → dynamic-imports → big-script
→ encrypt → rft → bcc
```

## Examples

```bash
# Rename identifiers + add junk
anubis script.py --carbon --junk

# Full protection: junk + anti-debug + rename + encrypt
anubis script.py --junk --antidebug --carbon --mix-strings --encrypt

# AST hardening: flatten control flow + opaque predicates + XOR strings
anubis script.py --flatten --opaque --xor-strings --blind

# LLM-resistant: misleading names + encrypted strings + hidden imports
anubis script.py --semantic-noise --xor-strings --blind --dynamic-imports

# Maximum obfuscation: everything + bytecode compilation
anubis script.py --junk --antidebug --flatten --opaque --carbon --xor-strings --blind --dynamic-imports --bcc

# Bytecode compilation (hardest to decompile)
anubis script.py --carbon --mix-strings --bcc

# Write output to a custom path
anubis script.py --carbon --xor-strings -o /tmp/protected.py

# CI/CD pipeline usage
anubis script.py --flatten --carbon --bcc --ci
```

## anubis.toml

Pin your flag choices in a config file so every pipeline invocation stays short:

```toml
[obfuscate]
carbon = true
junk   = true
bcc    = true
output = "dist/script-obf.py"
```

Place `anubis.toml` in the directory you run `anubis` from, then:

```bash
anubis script.py --ci   # reads anubis.toml, no long flag lists
```

CLI flags always override `anubis.toml` values. Unknown keys and wrong-typed values are silently ignored.

## Notes

- `--encrypt` and `--compile` are mutually exclusive.
- `--bcc` produces Python-version-specific bytecode run the output on the same Python version used to obfuscate.
- `--carbon` and `--semantic-noise` both rename identifiers using both applies `--carbon` first then `--semantic-noise` renames whatever is left. For best results, pick one.
- Flags can be combined freely; the pipeline order above is always preserved regardless of the order you specify them.
