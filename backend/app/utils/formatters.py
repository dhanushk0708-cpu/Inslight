def format_val(val: float, fmt: str = "number") -> str:
    """Format numeric values into readable business metrics with Indian numbering and Rupee symbol."""
    if val is None:
        return "0"
    prefix = "-" if val < 0 else ""
    abs_val = abs(val)
    if fmt == "currency":
        curr = "₹"
        if abs_val >= 1e7:
            return f"{prefix}{curr}{abs_val / 1e7:,.2f} Cr"
        if abs_val >= 1e5:
            return f"{prefix}{curr}{abs_val / 1e5:,.2f} L"
        if abs_val >= 1e3:
            return f"{prefix}{curr}{abs_val / 1e3:,.1f} K"
        return f"{prefix}{curr}{abs_val:,.0f}"
    if fmt == "percent":
        return f"{val:.1f}%"
    if abs_val >= 1e7:
        return f"{prefix}{abs_val / 1e7:,.2f} Cr"
    if abs_val >= 1e5:
        return f"{prefix}{abs_val / 1e5:,.2f} L"
    if abs_val >= 1e3:
        return f"{prefix}{abs_val / 1e3:,.1f} K"
    return f"{prefix}{abs_val:,.0f}"
