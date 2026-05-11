# Opaque Predicates

**Flag:** `--opaque`

Wraps every function body inside an always-true conditional. The `else` branch contains unreachable dead code. A static analyser or LLM must prove the predicate is always true before it can ignore the dead branch — and the predicate is specifically designed to make that proof non-trivial.

## How it works

Each function body is wrapped in:

```python
if (lambda _x: <always_true_expr>)(n):
    <original body>
else:
    <dead junk>
```

Three predicate variants are used at random:

| Predicate | Why it's always true |
|---|---|
| `(lambda _x: _x \| 1 != 0)(n)` | OR-ing any integer with 1 gives a non-zero result |
| `(lambda _x: _x * _x >= 0)(n)` | Any integer squared is non-negative |
| `(lambda _x: (_x ^ _x) == 0)(n)` | XOR of any value with itself is always zero |

## Example

**Before:**

```python
def greet(name):
    print("Hello, " + name)
```

**After:**

```python
def greet(name):
    if (lambda _x: _x * _x >= 0)(42):
        print("Hello, " + name)
    else:
        _dead = 7391
        pass
```

## What it defeats

- **Dead-code elimination in static analysis** — the analyser must evaluate the predicate to know the else branch is unreachable.
- **LLM deobfuscation** — LLMs tend to consider both branches as potentially live, adding semantic noise to their interpretation.
- **Diff-based analysis** — the additional branch structure obscures where the real code is.

## Notes

- Functions with a body of only `pass` are skipped.
- Pairs well with `--flatten` (applied first) so the predicate wraps the already-flattened state machine.
- The dead else branch variable is named with a random string (further obscured by `--carbon`).
