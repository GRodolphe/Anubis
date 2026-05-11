# Installation

Anubis requires Python **3.10 or later**.

## pipx recommended

[pipx](https://pipx.pypa.io/) installs Anubis in an isolated environment and makes the `anubis` command available globally.

```bash
# Install directly from GitHub
pipx install git+https://github.com/GRodolphe/Anubis.git

# Or from a local clone
git clone https://github.com/GRodolphe/Anubis && cd Anubis
pipx install .
```

## uv project venv

```bash
git clone https://github.com/GRodolphe/Anubis && cd Anubis
uv sync
uv run anubis --help
```

## pip

```bash
pip install git+https://github.com/GRodolphe/Anubis.git
```

## Verify

```bash
anubis --version
```

## Optional: ancrypt (AES encryption)

The `--encrypt` flag requires the `ancrypt` native extension. Build it once from the repo root:

```bash
uv run --group dev python setup.py build_ext --inplace
# → ancrypt.cpython-*.so  (Linux/macOS)
# → ancrypt.cpython-*.pyd (Windows)
```

Ship `ancrypt.*.so` / `ancrypt.*.pyd` alongside the obfuscated file it is imported at runtime to decrypt and execute the source.

## Optional: Nuitka (exe compilation)

The `--compile` flag calls [Nuitka](https://nuitka.net/) to produce a standalone executable. Install it separately:

```bash
pip install nuitka
```

A C compiler is also required (GCC on Linux/macOS, MinGW64 on Windows).
