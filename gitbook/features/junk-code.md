# Junk Code

**Flag:** `--junk`

Junk code injection wraps the target script with unreachable class and method definitions. These classes are never instantiated in the main code path, so they have no effect at runtime but they increase the volume of code a reverse-engineer must sift through.

## How it works

Two junk blocks are generated: one prepended and one appended to the source. Each block contains between 2 and 5 randomly-named classes. Every class has between 5 and 15 methods, each with random parameter names and a body that calls another random method.

## Example output shape

```python
class XkLmPqRsT:
    def __init__(self):
        self.__AbCdEfGh()
        self.__IjKlMnOp()
    def __AbCdEfGh(self, xYzAbCd, eFgHiJkL):
        return self.__IjKlMnOp()
    def __IjKlMnOp(self, mNoPqRsT):
        return self.__AbCdEfGh()

# ... your actual code here ...

class QwErTyUiOp:
    # another junk class
```

## Notes

- When combined with `--carbon`, all junk identifiers are renamed along with your real code.
- Junk is applied **twice** in the pipeline (before and after `--antidebug`) to surround the anti-debug header.
- The junk classes use double-underscore method names (`__method`) so they do not accidentally shadow any real attribute.
