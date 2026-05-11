class ValidationError(Exception):
    pass


def parse_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValidationError("not an integer: " + str(value))


def safe_divide(a, b):
    if b == 0:
        raise ZeroDivisionError("division by zero")
    return a / b


inputs = ["42", "7", "bad", "0", "100"]
parsed = []
for val in inputs:
    try:
        parsed.append(parse_int(val))
    except ValidationError as exc:
        print("error:", exc)

print(parsed)

pairs = [(10, 2), (9, 3), (5, 0), (8, 4)]
for a, b in pairs:
    try:
        result = safe_divide(a, b)
        print(result)
    except ZeroDivisionError as exc:
        print("error:", exc)
