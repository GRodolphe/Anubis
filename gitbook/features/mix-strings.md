# Mix Strings

**Flag:** `--mix-strings`

Mix Strings replaces every plain string literal in the source with an equivalent `chr()` chain expression. The string value is preserved exactly — the obfuscated code produces the same output — but the readable text disappears from the source file.

## Example

**Before:**

```python
print("hello")
```

**After:**

```python
print((chr(104)+chr(101)+chr(108)+chr(108)+chr(111)))
```

## What is skipped

- Triple-quoted strings (`"""..."""`, `'''...'''`)
- f-strings (`f"..."`)
- Byte literals (`b"..."`)
- Raw strings (`r"..."`)
- Strings longer than 80 characters (to avoid excessive bloat)
- Empty strings

## Notes

- Position-accurate replacement using Python's `tokenize` module ensures no off-by-one errors even when multiple strings appear on the same line.
- Combine with `--carbon` to also rename the variables that hold these strings.
- `--bcc` or `--rft` applied after `--mix-strings` will further hide the `chr()` calls inside an encoded blob.
