# CI/CD Mode

Anubis is safe to run in automated pipelines. Use the `--ci` flag (or rely on the `CI=true` environment variable that most CI platforms set automatically) to get pipeline-friendly behaviour.

## What CI mode does

| Behaviour | Normal CLI | CI mode |
|-----------|-----------|---------|
| Banner | printed | suppressed |
| Terminal clear | yes | no |
| Keypress wait at exit | yes | no |
| Success message | coloured ANSI | plain `Obfuscated: <path>` to stdout |
| Error message | coloured ANSI + pause | `error: <msg>` to stderr |
| Exit code on error | 0 | 1 |

## Activating CI mode

**Option 1 explicit flag** (works everywhere, including local testing):

```bash
anubis script.py --ci --carbon --bcc
```

**Option 2 environment variable** (zero-config on cloud CI):

GitHub Actions, GitLab CI, CircleCI, Bitbucket Pipelines, and most other platforms set `CI=true` automatically. Anubis detects this and enables CI mode without any extra flags.

## Output path

Use `-o` / `--output` to write the obfuscated file to a predictable path your pipeline can collect as an artifact:

```bash
anubis script.py --ci --carbon --output dist/script-obf.py
```

## anubis.toml pin flags in version control

Commit an `anubis.toml` at your project root so pipelines stay short and flags are version-controlled:

```toml
[obfuscate]
carbon = true
junk   = true
bcc    = true
output = "dist/script-obf.py"
```

Then every pipeline step is just:

```bash
anubis src/script.py --ci
```

CLI flags always take precedence over `anubis.toml` values.

## GitHub Actions

```yaml
name: Obfuscate

on:
  push:
    branches: [main]

jobs:
  obfuscate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Anubis
        run: pip install git+https://github.com/GRodolphe/Anubis.git

      - name: Obfuscate
        # CI=true is set automatically --ci is optional but explicit
        run: anubis src/script.py --ci --output dist/script-obf.py

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: obfuscated
          path: dist/
```

## GitLab CI

```yaml
stages:
  - obfuscate

obfuscate:
  stage: obfuscate
  image: python:3.12-slim
  before_script:
    - pip install git+https://github.com/GRodolphe/Anubis.git
  script:
    # CI=true is set automatically by GitLab
    - anubis src/script.py --ci --output dist/script-obf.py
  artifacts:
    paths:
      - dist/
    expire_in: 7 days
```

## Generic shell script

```bash
#!/usr/bin/env bash
set -euo pipefail

anubis script.py --ci --carbon --junk --bcc --output dist/script-obf.py
# exits 1 on any error, so set -e stops the pipeline
```

## Notes

- `--encrypt` and `--compile` are mutually exclusive even in CI mode.
- `--bcc` output is Python-version-specific run it on the same interpreter version used to obfuscate.
- The `ANUBIS_CI=1` environment variable is equivalent to `--ci` and can be set in your pipeline's environment config to apply CI mode project-wide without modifying every `anubis` call.
