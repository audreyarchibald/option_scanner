import numpy as np

def safe_divide(a, b, default=0.0):
    """
    Safe division handling zero divisor.
    """
    return np.divide(a, b, out=np.full_like(a, default, dtype=float), where=b!=0)

def clamp(value, min_val, max_val):
    """
    Clamp value between min and max.
    """
    return np.clip(value, min_val, max_val)
