import pandas as pd


def format_indian_number(number: int | float) -> str:
    """
    Format a number in Indian numbering system.

    Examples:
    - 1234567  → "12,34,567"
    - 12345    → "12,345"
    - -1234567 → "-12,34,567"
    """
    if pd.isna(number):
        return "0"
    if isinstance(number, float):
        number = int(round(number))
    number = int(number)
    negative = number < 0
    s = str(abs(number))

    if len(s) <= 3:
        result = s
    else:
        main_part, last_three = s[:-3], s[-3:]
        pairs = []
        while len(main_part) > 2:
            pairs.insert(0, main_part[-2:])
            main_part = main_part[:-2]
        if main_part:
            pairs.insert(0, main_part)
        result = ",".join(pairs + [last_three])

    return f"-{result}" if negative else result


def format_indian_compact(number: int | float) -> str:
    """Short Indian-style labels for charts: ₹40k, ₹4L, ₹4C."""
    if pd.isna(number):
        return "₹0"
    n = int(round(float(number)))
    if n < 0:
        return f"-{format_indian_compact(-n)}"
    if n < 1_000:
        return f"₹{n}"
    if n < 1_00_000:          # < 1 lakh → k
        val = round(n / 1_000, 1)
        s = f"{val:.1f}".rstrip("0").rstrip(".")
        return f"₹{s}k"
    if n < 1_00_00_000:       # < 1 crore → L
        val = round(n / 1_00_000, 1)
        s = f"{val:.1f}".rstrip("0").rstrip(".")
        return f"₹{s}L"
    val = round(n / 1_00_00_000, 1)   # crores → C
    s = f"{val:.1f}".rstrip("0").rstrip(".")
    return f"₹{s}C"
