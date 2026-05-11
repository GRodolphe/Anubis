# Features

Anubis applies protection passes in a fixed pipeline. Each pass is independent — combine as many as you need.

| Pass | Flag | Effect |
|---|---|---|
| [Carbon](carbon.md) | `--carbon` | Renames all identifiers to random `I`/`l` strings |
| [Junk Code](junk-code.md) | `--junk` | Wraps code in unreachable class definitions |
| [Mix Strings](mix-strings.md) | `--mix-strings` | Replaces string literals with `chr()` chains |
| [Big Script](big-script.md) | `--big-script` | Inflates output with ~256 KB of dead-code blobs |
| [Anti-Debug](anti-debug.md) | `--antidebug` | Kills debugger processes at runtime |
| [Import Alias](import-alias.md) | `--import-alias` | Rewrites import names to random aliases |
| [AES Encrypt](encrypt.md) | `--encrypt` | Encrypts source into a self-decrypting one-liner |
| [RFT](rft.md) | `--rft` | Encodes source as `zlib+base64` and `exec()`s it |
| [BCC](bcc.md) | `--bcc` | Compiles to bytecode, wraps in a marshal loader |
