"""Reads the web server log and splits each line into fields.

Two input types are supported: a raw Apache or nginx text access log, and the
same log exported as CSV. The Combined Log Format looks like this:

    IP ident user [timestamp] "METHOD path protocol" status bytes "referrer" "agent"

A user agent is full of spaces, so a regular expression is used instead of
splitting the line on whitespace.
"""

import csv
import re

APACHE_LINE = re.compile(
    r'^(?P<ip>\S+)\s+(?P<ident>\S+)\s+(?P<user>\S+)\s+'
    r'\[(?P<timestamp>[^\]]+)\]\s+'
    r'"(?P<method>[A-Z]+)\s+(?P<url>\S+)(?:\s+(?P<protocol>[^"]*))?"\s+'
    r'(?P<status_code>\d{3})\s+(?P<response_bytes>\S+)'
    r'(?:\s+"(?P<referer>[^"]*)"\s+"(?P<user_agent>[^"]*)")?'
    r'(?P<trailing>.*)$'
)

# Different log exports name the same column differently. "response_ms" must
# stay in this list: when it was missing, every response time silently became 0.
ALIASES = {
    "timestamp": ["timestamp", "time", "datetime", "@timestamp"],
    "ip": ["ip", "ip_address", "client_ip", "remote_addr", "host"],
    "method": ["method", "request_method", "http_method"],
    "url": ["url", "request", "resource", "path", "request_uri"],
    "protocol": ["protocol", "http_version"],
    "status_code": ["status_code", "status", "http_status", "statuscode"],
    "response_bytes": ["bytes", "response_bytes", "sc_bytes", "size"],
    "response_time": ["response_ms", "response_time_ms", "request_time",
                      "elapsed_time", "total_time", "latency", "duration"],
    "error_message": ["error_message", "error", "message", "reason"],
}


def detect_format(path):
    """Look at the first line and decide whether this is a CSV or a text log.

    Uses readline(), which returns one line and leaves the file position after
    it. Choosing on the file's content rather than its extension means a log
    named .txt that is really CSV, or a CSV saved as .log, still reads.
    """

    with open(path, "r", encoding="utf-8-sig", errors="replace") as file:
        first = file.readline()

    if not first.strip():
        raise ValueError(f"No content to read from {path}")

    # A CSV header is comma separated with no leading IP address.
    if "," in first and not first[:1].isdigit() and "[" not in first:
        return "csv"

    return "text"


def read_lines(path):
    """Return [(line_number, text)] for every line of a text log.

    readlines() loads the whole file as a list of lines. That is fine for a log
    of this size and it makes the line numbering easy to follow.
    """

    with open(path, "r", encoding="utf-8", errors="replace") as file:
        raw = file.readlines()

    return [(number, text) for number, text in enumerate(raw, start=1)]


def read_csv_rows(path):
    """Return [(line_number, fields)] for a log exported as CSV."""

    rows = []

    with open(path, "r", encoding="utf-8-sig", newline="") as file:

        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("CSV file has no header row")

        headers = {name.strip().lower() for name in reader.fieldnames if name}

        for field in ("status_code", "url"):
            if not any(alias in headers for alias in ALIASES[field]):
                raise ValueError(
                    f"Missing required column: {field}. "
                    f"Columns found: {sorted(headers)}"
                )

        # start=2 because line 1 is the header row.
        for number, row in enumerate(reader, start=2):
            rows.append((number, pick_fields(row)))

    return rows


def pick_fields(row):
    """Copy a CSV row into our own field names using the alias table."""

    fields = {}

    for field, aliases in ALIASES.items():
        fields[field] = ""

        for alias in aliases:
            for key, value in row.items():
                if key and key.strip().lower() == alias.lower():
                    if value is not None and str(value).strip():
                        fields[field] = str(value).strip()
                        break
            if fields[field]:
                break

    return fields


def parse_apache_line(line):
    """Split one text log line into raw string fields.

    Raises ValueError when the line is not a web log line at all.
    """

    match = APACHE_LINE.match(line.strip())

    if not match:
        raise ValueError("Line does not match the Apache Combined Log Format")

    parts = match.groupdict()

    return {
        "timestamp": parts["timestamp"] or "",
        "ip": parts["ip"] or "",
        "method": parts["method"] or "",
        "url": parts["url"] or "",
        "protocol": parts["protocol"] or "",
        "status_code": parts["status_code"] or "",
        "response_bytes": parts["response_bytes"] or "",
        "error_message": "",
        # nginx can append $request_time after the user agent, in seconds.
        "response_time": first_number(parts["trailing"]),
        "time_unit": "s",
    }


def first_number(trailing):
    """Return the duration an nginx log appends, or an empty string."""

    for token in (trailing or "").split():
        if token == "-":
            continue
        try:
            float(token)
        except ValueError:
            continue
        return token

    return ""


def read_log(path):
    """Read the log whichever type it is.

    Returns a list of (line_number, fields, error). On a good line error is
    None. On a bad line fields is empty and error says what was wrong, so one
    damaged line never stops the run.
    """

    if detect_format(path) == "csv":
        return [
            (number, fields, None)
            for number, fields in read_csv_rows(path)
        ]

    results = []

    for number, text in read_lines(path):

        if not text.strip():
            results.append((number, {}, "Empty record"))
            continue

        try:
            results.append((number, parse_apache_line(text), None))
        except ValueError as error:
            results.append((number, {}, str(error)))

    return results
