**Fork of [Anubis](https://github.com/0sir1ss/Anubis) originally created by [0sir1ss](https://github.com/0sir1ss).**

<div align="center" id="top">
  <img src="./img.png" alt="Anubis" />

  &#xa0;

</div>

<h1 align="center">Anubis</h1>

<p align="center">
  <img alt="Github top language" src="https://img.shields.io/github/languages/top/GRodolphe/Anubis">
  <img alt="Github stars" src="https://img.shields.io/github/stars/GRodolphe/Anubis" />
  <img alt="License" src="https://img.shields.io/github/license/GRodolphe/Anubis">
  <img alt="Github issues" src="https://img.shields.io/github/issues/GRodolphe/Anubis" />
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue" />
</p>

<p align="center">
  <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/GRodolphe/Anubis/ci.yml?branch=main&label=CI" />
  <img alt="ruff" src="https://img.shields.io/badge/linter-ruff-261230?style=flat&logo=ruff&logoColor=white" />
  <img alt="ty" src="https://img.shields.io/badge/types-ty-6A0DAD?style=flat" />
  <img alt="uv" src="https://img.shields.io/badge/package%20manager-uv-DE5FE9?style=flat&logo=uv&logoColor=white" />
</p>

<p align="center">
  <a href="#dart-about">About</a> &#xa0; | &#xa0;
  <a href="#sparkles-features">Features</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-installation">Installation</a> &#xa0; | &#xa0;
  <a href="#rocket-quick-start">Quick Start</a> &#xa0; | &#xa0;
  <a href="#usage">Usage</a> &#xa0; | &#xa0;
  <a href="#wrench-cicd">CI/CD</a> &#xa0; | &#xa0;
  <a href="#memo-license">License</a>
</p>

<br>

## :dart: About ##

**Anubis** is a Python source-code obfuscator that stacks multiple independent protection layers. Each pass is opt-in, composable, and runs in a fixed pipeline so the result is deterministic regardless of the order you specify flags.

Protection ranges from lightweight identifier renaming to full bytecode compilation, with AST-level transforms (control flow flattening, opaque predicates, XOR string encryption) and encoding layers (AES, zlib+base64, marshal bytecode). A dedicated CI/CD mode makes it safe to embed in automated pipelines with a single flag.

This fork modernizes the original codebase, fixes reported bugs, and adds new features including AST-level obfuscation passes and LLM deobfuscation resistance (based on research from [arxiv:2512.16538](https://arxiv.org/abs/2512.16538) and [arxiv:2410.05797](https://arxiv.org/abs/2410.05797)).

## :sparkles: Features ##

**AST transforms** rewrite the syntax tree before the source ever hits the interpreter

| Pass | What it does |
|------|-------------|
| `--flatten` | Rewrites every function body as a `while True` state-machine |
| `--opaque` | Wraps functions in always-true guards with unreachable dead branches |
| `--xor-strings` | XOR-encrypts string literals with a random key; plaintext never appears in source or `.pyc` |
| `--blind` | Replaces integer literals `N` with `(N^R)^R` for random R |
| `--dynamic-imports` | Replaces `import X` with XOR-encoded `__import__()` calls |
| `--mix-strings` | Replaces string literals with `chr()` chains: `"hi"` → `(chr(104)+chr(105))` |

**Identifier & structure obfuscation**

| Pass | What it does |
|------|-------------|
| `--carbon` | Renames all identifiers to visually identical `I`/`l` strings; strips comments and docstrings |
| `--semantic-noise` | Renames identifiers to misleading English words to resist LLM-based deobfuscation |
| `--import-alias` | Obfuscates imported module names with random aliases |
| `--junk` | Injects unreachable class and function definitions |
| `--antidebug` | Spawns a thread that kills known debugger processes at runtime (cross-platform) |
| `--big-script` | Inflates output with ~256 KB of random dead-code blobs |

**Encoding & compilation**

| Pass | What it does |
|------|-------------|
| `--encrypt` | AES-encrypts the source into a self-decrypting one-liner (requires `ancrypt`) |
| `--rft` | Run From Text: encodes entire source as `zlib+base64` and `exec()`s it at runtime |
| `--bcc` | Bytecode Compilation: `compile()` → `marshal` → `zlib` → `base64` loader stub |
| `--compile` | Compiles the obfuscated output to a standalone executable via Nuitka |

## :checkered_flag: Installation ##

### Recommended pipx (isolated, globally available `anubis` command)

```bash
# Install directly from GitHub
pipx install git+https://github.com/GRodolphe/Anubis.git

# Or from a local clone
git clone https://github.com/GRodolphe/Anubis && cd Anubis
pipx install .
```

### uv (project venv)

```bash
git clone https://github.com/GRodolphe/Anubis && cd Anubis
uv sync
uv run anubis --help
```

### pip

```bash
pip install git+https://github.com/GRodolphe/Anubis.git
```

> **Requirements:** Python 3.10+, `uv` or `pipx`. Nuitka and a C compiler are only needed for `--compile`.

## :rocket: Quick Start ##

```bash
# Lightest touch: just rename identifiers
anubis script.py --carbon

# Solid protection: rename + junk + bytecode
anubis script.py --carbon --junk --bcc

# AST hardening: flatten control flow + opaque predicates + encrypted strings
anubis script.py --flatten --opaque --xor-strings --blind

# LLM-resistant: misleading names + encrypted strings + hidden imports
anubis script.py --semantic-noise --xor-strings --blind --dynamic-imports

# Maximum obfuscation
anubis script.py --junk --antidebug --flatten --opaque --carbon --xor-strings --blind --dynamic-imports --bcc
```

Output is written to `<stem>-obf.py` by default. Override with `-o`:

```bash
anubis script.py --carbon --bcc -o dist/protected.py
```

## Usage ##

### Interactive mode

Run with no arguments to be prompted through every option step-by-step:

```bash
anubis
```

### Flag reference

**Source transforms**

| Flag | Description |
|------|-------------|
| `--antidebug` | Inject anti-debugger thread (cross-platform) |
| `--junk` | Inject unreachable junk class/function definitions |
| `--flatten` | Rewrite function bodies as `while True` state machines |
| `--opaque` | Wrap functions in always-true guards with dead branches |
| `--mix-strings` | Replace string literals with `chr()` chains |
| `--xor-strings` | XOR-encrypt string literals with a random key (stronger than `--mix-strings`) |
| `--blind` | Replace integer literals `N` with `(N^R)^R` for random R |
| `--big-script` | Inflate output with ~256 KB of random dead-code blobs |
| `--carbon` | Rename identifiers to random `I`/`l` strings; strip comments and docstrings |
| `--semantic-noise` | Rename identifiers to misleading English names (LLM resistance) |
| `--import-alias` | Obfuscate imported module names with random aliases |
| `--dynamic-imports` | Replace `import X` with XOR-encoded `__import__()` calls |

**Encoding / compilation**

| Flag | Description |
|------|-------------|
| `--encrypt` | AES-encrypt source into self-decrypting one-liner (requires `ancrypt`) |
| `--rft` | RFT: zlib+base64 encode source, exec at runtime |
| `--bcc` | BCC: compile to bytecode, marshal+zlib+base64 loader |
| `--compile` | Compile output to a standalone exe with Nuitka |

**Pipeline control**

| Flag | Description |
|------|-------------|
| `-o PATH` / `--output PATH` | Write output to this path (default: `<stem>-obf.py`) |
| `--ci` | CI/CD mode: no interactive prompts, plain stdout, exit 1 on error |
| `--version` | Print version and exit |

### Pipeline order

Passes always run in this fixed order regardless of the order you specify them on the command line:

```
junk → antidebug → junk → flatten → opaque
     → carbon → semantic-noise
     → mix-strings → xor-strings → blind
     → import-alias → dynamic-imports → big-script
     → encrypt → rft → bcc
```

### Notes

- `--carbon` and `--semantic-noise` both rename identifiers. Using both applies `--carbon` first; for best results, pick one.
- `--encrypt` and `--compile` are mutually exclusive.
- `--bcc` output is Python-version-specific run it on the same interpreter used to obfuscate.

### Building ancrypt

`--encrypt` produces output that imports `ancrypt` at runtime. Compile it once and ship it alongside the obfuscated file:

```bash
uv run --group dev python setup.py build_ext --inplace
# → ancrypt.cpython-*.so  (Linux/macOS)
# → ancrypt.cpython-*.pyd (Windows)
```

## :wrench: CI/CD ##

Pass `--ci` (or rely on the `CI=true` environment variable that GitHub Actions, GitLab CI, and most other platforms set automatically) for pipeline-safe behaviour:

| Behaviour | Normal CLI | CI mode |
|-----------|-----------|---------|
| Banner | printed | suppressed |
| Terminal clear | yes | no |
| Keypress wait | yes | no |
| Success message | coloured ANSI | `Obfuscated: <path>` to stdout |
| Error message | coloured ANSI | `error: <msg>` to stderr |
| Exit code on error | 0 | 1 |

```bash
anubis script.py --ci --carbon --junk --bcc --output dist/script-obf.py
```

### anubis.toml

Pin flags in a config file so pipeline invocations stay short:

```toml
[obfuscate]
carbon = true
junk   = true
bcc    = true
output = "dist/script-obf.py"
```

Place `anubis.toml` in the directory you run `anubis` from, then:

```bash
anubis script.py --ci   # reads anubis.toml automatically
```

CLI flags always override `anubis.toml` values.

### GitHub Actions

```yaml
- name: Install Anubis
  run: pip install git+https://github.com/GRodolphe/Anubis.git

- name: Obfuscate
  run: anubis src/script.py --ci --output dist/script-obf.py
  # CI=true is set automatically by GitHub Actions
```

### GitLab CI

```yaml
obfuscate:
  image: python:3.12-slim
  before_script:
    - pip install git+https://github.com/GRodolphe/Anubis.git
  script:
    - anubis src/script.py --ci --output dist/script-obf.py
```

## Development ##

```bash
git clone https://github.com/GRodolphe/Anubis && cd Anubis
uv sync   # installs package + dev tools (ruff, ty, Cython)
```

```bash
uv run ruff check src/     # lint
uv run ruff format src/    # format
uv run ty check src/       # type-check
uv run pytest              # tests
```

### Adding a new obfuscation pass

1. Implement `def my_pass(code: str) -> str` in `src/anubis/obfuscators.py`.
2. Add a `--my-pass` flag in `_build_parser()` inside `src/anubis/cli.py`.
3. Insert the call at the correct position in `_run_pipeline()`.
4. Add the flag to the interactive prompts in `_interactive()`.
5. Write a test script in `tests/scripts/` and cover it in `.github/workflows/ci.yml`.

## :memo: License ##

MIT see [LICENSE](LICENSE).

&#xa0;

<a href="#top">Back to top</a>
