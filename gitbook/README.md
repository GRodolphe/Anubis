# Anubis

> Fork of [Anubis](https://github.com/0sir1ss/Anubis) originally created by [0sir1ss](https://github.com/0sir1ss).

Anubis is a Python source-code obfuscator with multiple protection layers. It transforms readable Python scripts into hardened outputs that are difficult to reverse-engineer, without changing what the code does at runtime.

## Protection layers

| Layer | What it does |
|---|---|
| [Flatten Control Flow](features/flatten.md) | Rewrites function bodies as `while True` state machines |
| [Opaque Predicates](features/opaque.md) | Wraps functions in always-true guards with dead branches |
| [XOR String Encryption](features/xor-strings.md) | Encrypts string literals with a random key |
| [Constant Blinding](features/blind.md) | Hides integer literals: `N` → `(N^R)^R` |
| [Dynamic Imports](features/dynamic-imports.md) | Replaces `import X` with XOR-encoded `__import__()` calls |
| [Semantic Noise](features/semantic-noise.md) | Renames identifiers to misleading English names (LLM resistance) |
| [Carbon](features/carbon.md) | Renames every identifier to random `I`/`l` strings |
| [Junk Code](features/junk-code.md) | Wraps code in unreachable class definitions |
| [Mix Strings](features/mix-strings.md) | Replaces string literals with `chr()` chains |
| [Big Script](features/big-script.md) | Inflates output with ~256 KB of random dead-code blobs |
| [Anti-Debug](features/anti-debug.md) | Kills known debugger processes at runtime |
| [Import Alias](features/import-alias.md) | Obfuscates imported module names |
| [AES Encrypt](features/encrypt.md) | Encrypts source into a self-decrypting one-liner |
| [RFT](features/rft.md) | Encodes entire source as `zlib+base64` and `exec()`s it |
| [BCC](features/bcc.md) | Compiles to bytecode, wraps in a marshal loader stub |

## Quick start

```bash
pip install git+https://github.com/GRodolphe/Anubis.git
anubis script.py --flatten --opaque --carbon --xor-strings --blind --bcc
```

See [Installation](installation.md) for full setup options.
