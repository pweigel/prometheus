def regularize_string(s: str) -> str:
    """Helper fnuction to regularize strings

    params
    ______
    s: string to regularize

    returns
    _______
    s: regularized string
    """
    s = s.replace(" ", "")
    s = s.replace("_", "")
    s = s.upper()
    return s