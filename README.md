**Fork of [Anubis](https://github.com/0sir1ss/Anubis) by [0sir1ss](https://github.com/0sir1ss) — modernized and actively maintained.**

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

</p>


<p align="center">
  <a href="#dart-about">About</a> &#xa0; | &#xa0; 
  <a href="#sparkles-features">Features</a> &#xa0; | &#xa0;
  <a href="#rocket-technologies">Technologies</a> &#xa0; | &#xa0;
  <a href="#white_check_mark-requirements">Requirements</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-starting">Starting</a> &#xa0; | &#xa0;
  <a href="#memo-license">License</a> &#xa0; | &#xa0;
  <a href="https://github.com/0sir1ss" target="_blank">Original Author</a>
</p>

<br>

## :dart: About ##

A Python obfuscator with multiple layers of protection: identifier renaming, junk code injection, custom AES encryption, anti-debugger injection, and optional compilation to a standalone executable via Nuitka.

This fork modernizes the original codebase, fixes reported bugs, and adds new features like import aliasing and a proper CLI interface.

You can see the difference it makes from this source [here](https://github.com/0sir1ss/Anubis/blob/main/example/script.py) to this obfuscated one liner [here](https://github.com/0sir1ss/Anubis/blob/main/example/script-obf.py).

## :sparkles: Features ##

:heavy_check_mark: Anti Debugger — Stop the use of debuggers whilst this program is running (cross-platform)\
:heavy_check_mark: Junk Code — Add junk code to the program\
:heavy_check_mark: Carbon Obfuscation — Rename classes, functions, variables and parameters along with removing comments and docstrings\
:heavy_check_mark: Import Aliasing — Obfuscate imported module names\
:heavy_check_mark: Custom Encryption — A one liner which uses custom AES encryption\
:heavy_check_mark: CLI interface — Run with flags or interactively\
:heavy_check_mark: Compile to exe with Nuitka

## :rocket: Technologies ##

The following tools were used in this project:

- [Python](https://www.python.org/) 3.10+
- [Nuitka](https://pypi.org/project/Nuitka/) (optional, for exe compilation)
- [PyCryptodome](https://pypi.org/project/pycryptodome/)

## :white_check_mark: Requirements ##

Before starting, you need to have [Python](https://www.python.org/) 3.10 or newer installed.

If you wish to compile your project to an exe you will need [Nuitka](https://pypi.org/project/Nuitka/) along with a C compiler. Nuitka will automatically download the MinGW64 compiler if no usable one is found.

## :checkered_flag: Starting ##

```bash
# Clone this project
$ git clone https://github.com/GRodolphe/Anubis

# Access
$ cd Anubis

# Install dependencies
$ pip install -r requirements.txt

# Run interactively
$ python anubis.py

# Or use the CLI directly
$ python anubis.py script.py --junk --carbon --antidebug
$ python anubis.py script.py --encrypt
$ python anubis.py script.py --carbon --import-alias --compile
```

### CLI flags

| Flag | Description |
|------|-------------|
| `--antidebug` | Inject anti-debugger thread |
| `--junk` | Wrap code in junk classes |
| `--carbon` | Rename identifiers offline |
| `--oxyry` | Rename identifiers via oxyry.com |
| `--import-alias` | Obfuscate import names |
| `--encrypt` | One-line AES encryption (requires `ancrypt`) |
| `--compile` | Compile output to exe with Nuitka |

### Building ancrypt

If you use `--encrypt` and distribute without compiling to exe, you need the `ancrypt` module compiled:

```bash
$ pip install Cython
$ python setup.py build_ext --inplace
```

## :memo: License ##

This project is under license from MIT. For more details, see the [LICENSE](LICENSE) file.


Made with :heart: by <a href="https://github.com/GRodolphe" target="_blank">GRodolphe</a>

&#xa0;

<a href="#top">Back to top</a>
