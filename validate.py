
from datetime import datetime

TIME_FORMATS = [
    "%d/%b/%Y:%H:%M:%S %z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
]


def to_time(value):

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

    text = str(value).strip()

    if not text:
        return ""

    if to_time(text) is None:
        raise ValueError(f"Invalid timestamp format: {text!r}")

    return text


def check_status(value):

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

    text = str(value).strip()

    if not text or text == "-":
        return None

    if text.isdigit():
        return int(text)

    raise ValueError(f"Invalid response size: {text!r}")


def build_record(number, fields):

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
