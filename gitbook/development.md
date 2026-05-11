# Development

## Setup

```bash
git clone https://github.com/GRodolphe/Anubis && cd Anubis
uv sync
```

This installs the package in editable mode plus the dev tools: `ruff`, `ty`, and `Cython`.

## Project layout

```
src/anubis/
  __init__.py       # package marker, __version__
  __main__.py       # enables python -m anubis
  cli.py            # argparse entry point + interactive mode
  obfuscators.py    # all obfuscation passes
  crypto.py         # AES encryption (Encryption class)
  terminal.py       # ANSI colour helpers, clear/pause/leave/error
ancrypt.py          # Cython source for the AES runtime loader
setup.py            # build ancrypt extension only
pyproject.toml      # project metadata, ruff, ty config
tests/
  check_obf.sh      # test helper: run original, obfuscate, compare output
  scripts/          # deterministic test scripts
.github/workflows/
  ci.yml            # lint + obfuscation matrix (Python 3.10–3.13)
gitbook/            # documentation source (this site)
```

## Lint

```bash
uv run ruff check src/
uv run ruff format src/
```

## Type check

```bash
uv run ty check src/
```

## Running tests locally

```bash
# Single test
bash tests/check_obf.sh tests/scripts/test_math.py --carbon --junk

# All combinations (mirrors CI)
for f in tests/scripts/*.py; do
  bash tests/check_obf.sh "$f" --carbon --junk --mix-strings
done
```

## Building ancrypt

```bash
uv run --group dev python setup.py build_ext --inplace
```

## Adding a new obfuscation pass

1. Implement the pass as a function in `src/anubis/obfuscators.py` with signature `def my_pass(code: str) -> str`.
2. Import it in `src/anubis/cli.py`.
3. Add a `--my-pass` flag to `_build_parser()`.
4. Insert the call at the right point in `_run_pipeline()`.
5. Add the flag to the interactive prompts in `_interactive()`.
6. Write a test script in `tests/scripts/` and add steps to `tests/check_obf.sh` / `.github/workflows/ci.yml`.

## Releasing

1. Bump `version` in `pyproject.toml` and `src/anubis/__init__.py`.
2. Push to `main` — CI must pass.
3. Tag the commit: `git tag vX.Y.Z && git push --tags`.
