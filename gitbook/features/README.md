# Features

Anubis applies protection passes in a fixed pipeline. Each pass is independent — combine as many as you need.

## Pipeline order

```
junk → antidebug → junk → flatten → opaque
→ carbon → semantic-noise
→ mix-strings → xor-strings → blind
→ import-alias → dynamic-imports → big-script
→ encrypt → rft → bcc
```

## Pass reference

| Pass | Flag | Effect |
|---|---|---|
| [Flatten Control Flow](flatten.md) | `--flatten` | Rewrites function bodies as `while True` state machines |
| [Opaque Predicates](opaque.md) | `--opaque` | Wraps functions in always-true guards with dead branches |
| [XOR String Encryption](xor-strings.md) | `--xor-strings` | Encrypts string literals with a random key |
| [Constant Blinding](blind.md) | `--blind` | Replaces integer literals `N` with `(N^R)^R` |
| [Dynamic Imports](dynamic-imports.md) | `--dynamic-imports` | Replaces `import X` with XOR-encoded `__import__()` calls |
| [Semantic Noise](semantic-noise.md) | `--semantic-noise` | Renames identifiers to misleading English names (LLM resistance) |
| [Carbon](carbon.md) | `--carbon` | Renames all identifiers to random `I`/`l` strings |
| [Junk Code](junk-code.md) | `--junk` | Wraps code in unreachable class definitions |
| [Mix Strings](mix-strings.md) | `--mix-strings` | Replaces string literals with `chr()` chains |
| [Big Script](big-script.md) | `--big-script` | Inflates output with ~256 KB of dead-code blobs |
| [Anti-Debug](anti-debug.md) | `--antidebug` | Kills debugger processes at runtime |
| [Import Alias](import-alias.md) | `--import-alias` | Rewrites import names to random aliases |
| [AES Encrypt](encrypt.md) | `--encrypt` | Encrypts source into a self-decrypting one-liner |
| [RFT](rft.md) | `--rft` | Encodes source as `zlib+base64` and `exec()`s it |
| [BCC](bcc.md) | `--bcc` | Compiles to bytecode, wraps in a marshal loader |

## Recommended combinations

**Maximum protection (all layers):**
```bash
anubis script.py --junk --antidebug --flatten --opaque --carbon --xor-strings --blind --dynamic-imports --bcc
```

**LLM-resistant:**
```bash
anubis script.py --flatten --opaque --semantic-noise --xor-strings --blind --dynamic-imports
```

**Lightweight + portable:**
```bash
anubis script.py --carbon --mix-strings --blind --import-alias
```

**Bytecode hardening:**
```bash
anubis script.py --flatten --carbon --xor-strings --bcc
```
