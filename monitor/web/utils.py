def format_bytes(bytes: int, suffix="B"):
    """Scale bytes to its proper format.
    e.g:
        1253656 => '1.20 MB'
        1253656678 => '1.17 GB'
    Args:
        bytes (int): Numeric size to format
        suffix (str): Format of introduced size: 'B', 'K', 'M', 'G', 'T', 'P'
    Returns:
        string: Formatted size
    """
    bytes_format = bytes
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes_format < factor:
            return f"{bytes_format:.2f} {unit}{suffix}"
        bytes_format /= factor
    return bytes_format
