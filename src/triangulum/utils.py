from importlib import metadata


def get_current_version() -> str:
    return metadata.version("triangulum")


def fill_string(
    string: str,
    to_len: int,
    char: str = " ",
) -> str:
    """
    Fill a string with whitespace (or truncate) until the desired length is reached.
    """
    len_str = len(string)
    if len_str == to_len:
        return string
    elif len_str < to_len:
        difference = to_len - len_str
        return string + (char * difference)
    else:
        return string[:to_len]