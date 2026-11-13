"""Checks one parsed line and converts its fields to real types.

A line only becomes a record if every field is usable. Anything else raises
ValueError with a reason, and main.py counts it as a rejected line instead of
stopping.
"""

from datetime import datetime

# Timestamp layouts real logs use, tried in this order.
TIME_FORMATS = [
    "%d/%b/%Y:%H:%M:%S %z",   # Apache and nginx
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
]


def to_time(value):
    """Return a datetime for a timestamp string, or None."""

    text = str(value).strip()

    if not text:
        return None

    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return None


def check_time(value):
    """Return the timestamp unchanged if it is real, else raise.

    Raises on an impossible date too, so 32/Dec is rejected even though it
    looks like a timestamp.
    """

    text = str(value).strip()

    if not text:
        return ""

    if to_time(text) is None:
        raise ValueError(f"Invalid timestamp format: {text!r}")

    return text


def check_status(value):
    """Return an HTTP status code as an int.

    999 converts to an int happily but is not a status code, so the range is
    checked as well as the type.
    """

    text = str(value).strip()

    if not text:
        raise ValueError("Missing HTTP status code")

    try:
        code = int(text)
    except ValueError:
        raise ValueError(f"Invalid HTTP status code: {text!r}") from None

    if not 100 <= code <= 599:
        raise ValueError("Invalid HTTP status code")

    return code


def check_duration(value, unit="ms"):
    """Return a response time in milliseconds, or None if the log has none.

    A bare number is read in whatever unit the caller says. A CSV writes
    milliseconds and nginx $request_time is fractional seconds, so guessing
    here would be wrong half the time.
    """

    text = str(value).strip().lower()

    if not text:
        return None

    if text.endswith("ms"):
        number = float(text[:-2])
    elif text.endswith("s"):
        number = float(text[:-1]) * 1000
    else:
        number = float(text)

        if unit == "s":
            number *= 1000

    if number < 0:
        raise ValueError("Negative response time")

    return number


def check_size(value):
    """Return the response size in bytes, or None when the log wrote "-"."""

    text = str(value).strip()

    if not text or text == "-":
        return None

    if text.isdigit():
        return int(text)

    raise ValueError(f"Invalid response size: {text!r}")


def build_record(number, fields):
    """Turn one dictionary of strings into a record, or raise ValueError."""

    url = str(fields.get("url", "")).strip()

    if not url:
        raise ValueError("Missing requested resource")

    record = {
        "line_number": number,
        "timestamp": check_time(fields.get("timestamp", "")),
        "ip": str(fields.get("ip", "")).strip(),
        "method": str(fields.get("method", "")).strip() or "UNKNOWN",
        "url": url,
        "status_code": check_status(fields.get("status_code", "")),
        "response_bytes": check_size(fields.get("response_bytes", "")),
        "response_time_ms": check_duration(
            fields.get("response_time", ""),
            fields.get("time_unit", "ms"),
        ),
        "error_message": str(fields.get("error_message", "")).strip(),
    }

    return record
