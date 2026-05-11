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
  <a href="#dart-about">About</a> &#xa0; | &#xa0;
  <a href="#sparkles-features">Features</a> &#xa0; | &#xa0;
  <a href="#white_check_mark-requirements">Requirements</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-installation">Installation</a> &#xa0; | &#xa0;
  <a href="#usage">Usage</a> &#xa0; | &#xa0;
  <a href="#memo-license">License</a>
</p>

<br>

## :dart: About ##

A Python source-code obfuscator with multiple protection layers: control flow flattening, opaque predicates,
XOR string encryption, identifier renaming, junk code injection, custom AES encryption, anti-debugger injection,
and optional compilation to a standalone executable via Nuitka.

This fork modernizes the original codebase, fixes reported bugs, and adds new features including AST-level
obfuscation passes and LLM deobfuscation resistance (based on research from arxiv:2512.16538 and arxiv:2410.05797).

## :sparkles: Features ##

:heavy_check_mark: **Control Flow Flattening** Rewrites every function body as a `while True` state-machine\
:heavy_check_mark: **Opaque Predicates** Wraps functions in always-true guards with unreachable dead branches\
:heavy_check_mark: **XOR String Encryption** Encrypts string literals with a random key; plaintext never appears in source or .pyc\
:heavy_check_mark: **Constant Blinding** Hides integer literals by replacing `N` with `(N^R)^R`\
:heavy_check_mark: **Dynamic Imports** Replaces `import X` with XOR-encoded `__import__()` calls\
:heavy_check_mark: **Semantic Noise** Renames identifiers to misleading English names to resist LLM-based deobfuscation\
:heavy_check_mark: **Anti-Debugger** Kills known debugger processes at runtime (cross-platform; fixes #29 / #18)\
:heavy_check_mark: **Junk Code** Injects unreachable class/function definitions\
:heavy_check_mark: **Mix Strings** Replaces string literals with `chr()` chains: `"hi"` → `(chr(104)+chr(105))`\
:heavy_check_mark: **Big Script** Inflates output with ~256 KB of random dead-code blobs\
:heavy_check_mark: **Carbon** Renames identifiers, removes comments & docstrings (offline, fixes #31)\
:heavy_check_mark: **Import Aliasing** Obfuscates imported module names (feature #26)\
:heavy_check_mark: **AES Encryption** Encrypts source into a self-decrypting one-liner\
:heavy_check_mark: **RFT** Run From Text: encodes entire source as `zlib+base64` and `exec()`s it\
:heavy_check_mark: **BCC** Bytecode Compilation: `compile()` → `marshal` → `zlib` → `base64` loader stub\
:heavy_check_mark: **CLI interface** Use flags or interactive prompts\
:heavy_check_mark: **Nuitka compilation** Compile the obfuscated output to a standalone exe

## :white_check_mark: Requirements ##

- Python **3.10+**
- [`uv`](https://docs.astral.sh/uv/) or [`pipx`](https://pipx.pypa.io/) for installation
- Nuitka + a C compiler (only if using `--compile`)

## :checkered_flag: Installation ##

### Recommended pipx (isolated, globally available `anubis` command)

```bash
# Install pipx if you don't have it
uv tool install pipx

# Install directly from GitHub
pipx install git+https://github.com/GRodolphe/Anubis.git

# Or install from a local clone
git clone https://github.com/GRodolphe/Anubis && cd Anubis
pipx install .
```

### Alternative uv (project venv)

```bash
git clone https://github.com/GRodolphe/Anubis && cd Anubis
uv sync
uv run anubis --help
```

### Alternative pip

```bash
pip install git+https://github.com/GRodolphe/Anubis.git
```

## Usage ##

### Interactive mode

```bash
anubis
```

Prompts you through every option step-by-step.

### CLI mode

```bash
# Rename identifiers + add junk
anubis script.py --carbon --junk

# Full protection: junk + anti-debug + rename + encrypt
anubis script.py --junk --antidebug --carbon --mix-strings --encrypt

# AST-level hardening: flatten control flow + opaque predicates + XOR strings
anubis script.py --flatten --opaque --xor-strings --blind

# LLM-resistant: semantic noise + XOR strings + dynamic imports
anubis script.py --semantic-noise --xor-strings --blind --dynamic-imports

# Maximum obfuscation: all passes + bytecode compilation
anubis script.py --junk --antidebug --flatten --opaque --carbon --xor-strings --blind --dynamic-imports --bcc

# Bytecode compilation (hardest to decompile)
anubis script.py --carbon --mix-strings --bcc

# Double-encode: RFT then BCC
anubis script.py --carbon --rft --bcc

# Inflate + rename + alias imports + compile to exe
anubis script.py --big-script --carbon --import-alias --compile

# CI/CD pipeline plain output, exit 1 on error, custom output path
anubis script.py --carbon --bcc --ci --output dist/script-obf.py
```

### Flag reference

**Source transforms**

| Flag | Description |
|------|-------------|
| `--antidebug` | Inject anti-debugger thread (cross-platform) |
| `--junk` | Wrap code in unreachable junk class definitions |
| `--flatten` | Rewrite function bodies as `while True` state machines |
| `--opaque` | Wrap functions in always-true guards with dead branches |
| `--mix-strings` | Replace string literals with `chr()` chains |
| `--xor-strings` | XOR-encrypt string literals with a random key (stronger than `--mix-strings`) |
| `--blind` | Replace integer literals `N` with `(N^R)^R` for random R |
| `--big-script` | Inflate output with ~256 KB of random dead-code blobs |
| `--carbon` | Rename identifiers to random `I`/`l` strings |
| `--semantic-noise` | Rename identifiers to misleading English names (LLM resistance) |
| `--import-alias` | Obfuscate imported module names with random aliases |
| `--dynamic-imports` | Replace `import X` with XOR-encoded `__import__()` calls |

**Encoding / compilation**

| Flag | Description |
|------|-------------|
| `--encrypt` | AES-encrypt source into self-decrypting one-liner (requires `ancrypt`) |
| `--rft` | RFT: zlib+base64 encode source, exec at runtime |
| `--bcc` | BCC: compile to bytecode, marshal+zlib+base64 loader |
| `--compile` | Compile output to exe with Nuitka |

**Pipeline control**

| Flag | Description |
|------|-------------|
| `-o PATH` / `--output PATH` | Write output to this path (default: `<stem>-obf.py`) |
| `--ci` | CI/CD mode: no interactive prompts, plain stdout, exit 1 on error |
| `--version` | Print version and exit |

### Pipeline order

When multiple flags are combined, passes always run in this fixed order regardless of the order you specify them:

```
junk → antidebug → junk → flatten → opaque
→ carbon → semantic-noise
→ mix-strings → xor-strings → blind
→ import-alias → dynamic-imports → big-script
→ encrypt → rft → bcc
```

### CI/CD mode

Pass `--ci` (or set `CI=true` in the environment, which GitHub Actions and GitLab CI do automatically) to get pipeline-safe output:

- No banner, no terminal clears, no keypress waits
- Plain `Obfuscated: <path>` to stdout on success
- Errors go to stderr; process exits with code 1

```bash
# In any pipeline script
anubis script.py --ci --carbon --junk --bcc --output dist/script-obf.py
```

### anubis.toml

Pin your obfuscation flags in a config file so pipelines stay short:

```toml
[obfuscate]
carbon = true
junk   = true
bcc    = true
output = "dist/script-obf.py"
```

Then just run:

```bash
anubis script.py --ci
```

CLI flags always override `anubis.toml` values.

### Building ancrypt

`--encrypt` produces output that imports `ancrypt` at runtime. Compile it once and ship it alongside the obfuscated file:

```bash
uv run --group dev python setup.py build_ext --inplace
# → ancrypt.cpython-*.so  (Linux/macOS)
# → ancrypt.cpython-*.pyd (Windows)
```

## Development ##

```bash
git clone https://github.com/GRodolphe/Anubis && cd Anubis

# Install package + dev tools (ruff, ty, Cython)
uv sync

# Lint
uv run ruff check src/

# Format
uv run ruff format src/

# Type-check
uv run ty check src/
```

## :memo: License ##

MIT see [LICENSE](LICENSE).

&#xa0;

<a href="#top">Back to top</a>
