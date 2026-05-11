# Import Alias

**Flag:** `--import-alias`

Import Alias rewrites every `import X` statement to `import X as <obfuscated>` and replaces all usages of the original module name throughout the file. This hides which modules the script depends on from casual inspection.

## Example

**Before:**

```python
import math
import hashlib

print(math.sqrt(9))
digest = hashlib.sha256(b"hello").hexdigest()
```

**After:**

```python
import math as IlIlIIlIII
import hashlib as IIlIlIlIll

print(IlIlIIlIII.sqrt(9))
digest = IIlIlIlIll.sha256(b"hello").hexdigest()
```

## What is handled

- Simple `import X` statements
- Multi-import `import X, Y` statements (each name aliased separately)
- All usages of the original name in the file body

## What is not handled

- `from X import Y` statements (the module name `X` does not appear in the resulting code, so aliasing it has no effect)
- Names already aliased with `as` in the original source

## Notes

- Combine with `--carbon` to also rename variables and function names alongside the import aliases.
- The aliased names follow the same `I`/`l` random format as Carbon.
