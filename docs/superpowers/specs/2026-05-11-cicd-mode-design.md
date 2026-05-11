# CI/CD Mode — Design Spec

**Date:** 2026-05-11
**Approach:** Option A — minimal patch

## Problem

The current CLI is not safe to run in automated pipelines:

- `clear()` wipes the terminal log
- `pause()` blocks indefinitely waiting for a keypress
- `error()` calls `pause()` before exiting — any error hangs CI forever
- ANSI color codes add noise to structured CI logs
- Exit code is always 0 even on failure
- No `--output` flag to control the output path
- All obfuscation flags must be repeated on every pipeline invocation

## Solution

Surgical additions to `cli.py` and `terminal.py` only. No restructuring of the existing pipeline.

---

## Architecture

### `src/anubis/terminal.py`

Add one public helper:

```python
def is_ci() -> bool:
    return os.environ.get("CI") == "true" or os.environ.get("ANUBIS_CI") == "1"
```

Modify existing functions:
- `clear()` — no-op when `is_ci()` is true
- `pause()` — no-op when `is_ci()` is true
- `error(msg)` — when `is_ci()`: print `f"error: {msg}"` to `stderr`, `sys.exit(1)`; no pause/clear

### `src/anubis/config.py` (new, ~40 lines)

Reads `anubis.toml` from the current directory using `tomllib` (Python 3.11+) with a `tomli` fallback for 3.10. Returns a `dict[str, bool | str]` of flag values from `[obfuscate]` table. Returns empty dict if the file doesn't exist.

```toml
[obfuscate]
carbon = true
junk = true
mix_strings = true
big_script = false
antidebug = false
import_alias = true
encrypt = false
rft = false
bcc = true
output = "dist/script-obf.py"
```

### `src/anubis/cli.py`

Four targeted changes:

1. **`--ci` flag** — `action="store_true"`; when present sets `os.environ["ANUBIS_CI"] = "1"` before anything else runs so `is_ci()` returns true for the rest of the process lifetime.

2. **`--output` / `-o` flag** — specifies output file path; defaults to existing `<stem>-obf.py` behaviour when absent.

3. **Config loader call** — `load_config()` called once before `parse_args()`; results applied as `parser.set_defaults(**config)` so CLI flags always win.

4. **Guard decorative output** — banner print, `clear()` calls, and `pause()` calls in `main()` are wrapped in `if not is_ci():`.

---

## Data Flow

```
anubis script.py --ci [--carbon --bcc --output dist/out.py]
        │
        ├─ set ANUBIS_CI=1
        ├─ load anubis.toml → set_defaults()
        ├─ parse_args()  (CLI flags win over toml)
        ├─ is_ci() → True  → skip banner, skip clear
        ├─ _run_pipeline(src, ...)
        ├─ write output file
        ├─ print "Obfuscated: <path>"  (stdout)
        └─ sys.exit(0)

On any error:
        └─ print "error: <msg>"  (stderr)  → sys.exit(1)
```

---

## Config File Precedence

Highest → lowest:

1. CLI flags (`--carbon`, `--output dist/`)
2. `anubis.toml` `[obfuscate]` table
3. Built-in defaults (all false, output = `<stem>-obf.py`)

---

## CI Environment Detection

| Trigger | When |
|---------|------|
| `CI=true` env var | Set automatically by GitHub Actions, GitLab CI, CircleCI, Bitbucket Pipelines, etc. |
| `ANUBIS_CI=1` env var | Set by `--ci` flag, or manually in any environment |

Both paths produce identical behaviour.

---

## Output Behaviour

| Mode | Success | Error |
|------|---------|-------|
| Interactive | banner + ANSI colors + pause | ANSI error + pause + exit 0 |
| CI | `Obfuscated: <path>` to stdout | `error: <msg>` to stderr + exit 1 |

---

## Example Workflows

### GitHub Actions (`.github/workflows/obfuscate.yml`)

```yaml
name: Obfuscate
on: [push]

jobs:
  obfuscate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install git+https://github.com/GRodolphe/Anubis.git
      - run: anubis src/script.py --ci
      - uses: actions/upload-artifact@v4
        with:
          name: obfuscated
          path: src/script-obf.py
```

### GitLab CI (`.gitlab-ci.yml`)

```yaml
obfuscate:
  image: python:3.12
  before_script:
    - pip install git+https://github.com/GRodolphe/Anubis.git
  script:
    - anubis src/script.py --ci
  artifacts:
    paths:
      - dist/
```

### Generic shell

```bash
#!/usr/bin/env bash
set -euo pipefail
anubis script.py --ci --carbon --junk --bcc --output dist/script-obf.py
```

---

## Files Changed

| File | Change |
|------|--------|
| `src/anubis/terminal.py` | Add `is_ci()`; guard `clear`, `pause`, `error` |
| `src/anubis/cli.py` | Add `--ci`, `--output`; config loader; guard decorative output |
| `src/anubis/config.py` | New — `anubis.toml` loader (~40 lines) |
| `pyproject.toml` | Add `tomli >= 2.0 ; python_version < "3.11"` as a conditional required dep |
| `.github/workflows/obfuscate.yml` | New — example GitHub Actions workflow |
| `.gitlab-ci.yml` | New — example GitLab CI config |

## Out of Scope

- JSON output mode
- Config file in locations other than cwd
- CI-specific flag presets / profiles
- Watching files and re-obfuscating on change
