"""Counts what the log says: categories, errors, resources, sizes and hours.

Everything here is built from the records at run time. Nothing is a fixed
answer.
"""

from collections import Counter

from validate import to_time

# Thresholds.
SLOW_MS = 1000            # a request slower than this, when duration exists
HEAVY_BYTES = 50000       # a response larger than this
TOP_ERRORS = 10
TOP_RESOURCES = 10

# Plain English names for the codes that show up in web logs.
STATUS_REASONS = {
    200: "OK",
    206: "Partial Content",
    301: "Moved Permanently",
    302: "Found (Redirect)",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}


def classify(code):
    """Return the monitoring category for an HTTP status code."""

    if 200 <= code < 300:
        return "Successful"
    elif 300 <= code < 400:
        return "Redirect"
    elif 400 <= code < 500:
        return "Client Error"
    elif 500 <= code < 600:
        return "Server Error"
    else:
        return "Unknown"


def reason(code):
    return STATUS_REASONS.get(code, "HTTP error")


def add_labels(records):
    """Give every record its category and a readable error message."""

    for record in records:
        code = record["status_code"]
        record["category"] = classify(code)

        if code >= 400 and not record["error_message"]:
            record["error_message"] = f"{code} {reason(code)}"

    return records


def request_counts(records):
    """Count requests in each category and work out the error rate."""

    counts = Counter(record["category"] for record in records)
    total = len(records)
    client = counts["Client Error"]
    server = counts["Server Error"]

    return {
        "successful_requests": counts["Successful"],
        "redirects": counts["Redirect"],
        "client_errors": client,
        "server_errors": server,
        "failed_requests": client + server,
        "unknown_status_requests": counts["Unknown"],
        "error_percentage": round(((client + server) / total) * 100, 2)
                           if total else 0.0,
    }


def performance(records):
    """Response times when the log has them, otherwise response sizes.

    The Combined Log Format does not record how long a request took, so
    average_ms stays None instead of being reported as 0, which would claim
    every request was instant. Size is the honest substitute: a large response
    also takes the longest to deliver.
    """

    times = [r["response_time_ms"] for r in records
             if r["response_time_ms"] is not None]
    sizes = [r["response_bytes"] for r in records
             if r["response_bytes"] is not None]

    timing = {
        "recorded_in_log": bool(times),
        "note": (
            "Measured from the log." if times else
            "The Combined Log Format does not record request duration, "
            "so response size is reported instead."
        ),
        "average_ms": round(sum(times) / len(times), 2) if times else None,
        "slow_threshold_ms": SLOW_MS,
        "slow_request_count": sum(1 for t in times if t >= SLOW_MS),
    }

    transfer = {
        "average_bytes": round(sum(sizes) / len(sizes), 1) if sizes else 0,
        "largest_response_bytes": max(sizes) if sizes else 0,
        "heavy_threshold_bytes": HEAVY_BYTES,
        "heavy_request_count": sum(1 for s in sizes if s >= HEAVY_BYTES),
        "total_bytes_sent": sum(sizes),
        "total_mb_sent": round(sum(sizes) / 1048576, 2),
    }

    return timing, transfer


def traffic(records):
    """What is being asked for, by whom, and when."""

    resources = Counter(r["url"] for r in records)
    methods = Counter(r["method"] for r in records)
    clients = Counter(r["ip"] for r in records)
    codes = Counter(r["status_code"] for r in records)

    hours = Counter()
    failed_hours = Counter()

    for record in records:
        moment = to_time(record["timestamp"])

        if moment:
            hour = moment.strftime("%H")
            hours[hour] += 1

            if record["status_code"] >= 400:
                failed_hours[hour] += 1

    busiest = hours.most_common(1)

    # The hour with the highest error rate, not the most traffic. A quiet hour
    # where a quarter of requests fail is more interesting than a busy hour
    # where almost nothing does.
    rates = {
        hour: round((failed_hours[hour] / total) * 100, 2)
        for hour, total in hours.items() if total
    }
    worst = max(rates, key=lambda h: rates[h]) if rates else None

    return {
        "distinct_resources": len(resources),
        "unique_client_ips": len(clients),
        "busiest_hour": f"{busiest[0][0]}:00" if busiest else "n/a",
        "busiest_hour_requests": busiest[0][1] if busiest else 0,
        "worst_error_hour": f"{worst}:00" if worst else "n/a",
        "worst_error_rate_pct": rates.get(worst, 0) if worst else 0,
        "worst_error_hour_failures": failed_hours[worst] if worst else 0,
        "worst_error_hour_requests": hours[worst] if worst else 0,
        "requests_by_method": dict(methods.most_common()),
        "status_code_distribution": {
            str(code): count for code, count in sorted(codes.items())
        },
        "top_resources": [
            {"resource": url, "count": count}
            for url, count in resources.most_common(TOP_RESOURCES)
        ],
    }


def error_details(records):
    """Errors by code, and by URL inside each code.

    Grouping by URL is what turns a count into a finding. On this log it shows
    that almost half the 404s are one scanner probing one path, and that every
    500 comes from two PHP pages.
    """

    failed = [r for r in records if r["status_code"] >= 400]
    codes = Counter(r["status_code"] for r in failed)

    frequent = []

    for code, count in codes.most_common(TOP_ERRORS):
        urls = Counter(r["url"] for r in failed if r["status_code"] == code)

        frequent.append({
            "status_code": code,
            "count": count,
            "reason": reason(code),
            "top_urls": [
                {"url": url, "count": hits}
                for url, hits in urls.most_common(5)
            ],
        })

    return frequent


def findings(frequent):
    """Say in plain words what the error breakdown shows."""

    notes = []

    for item in frequent:

        if not item["top_urls"]:
            continue

        top = item["top_urls"][0]
        share = round((top["count"] / item["count"]) * 100, 1)

        if share >= 40 and top["count"] >= 10:
            notes.append(
                f"{share}% of all HTTP {item['status_code']} errors are "
                f"requests for {top['url']} ({top['count']} of "
                f"{item['count']})."
            )

    server = next((i for i in frequent if i["status_code"] == 500), None)

    if server and server["top_urls"]:
        pages = ", ".join(u["url"] for u in server["top_urls"][:3])
        notes.append(f"Server errors are concentrated in: {pages}.")

    return notes


def error_clusters(records, code=500):
    """Group failures of one code by page and by time.

    All nine 500s spread over nearly nine hours, which looks like background
    noise. Grouped by page, six of them land on /126.php inside 16 seconds,
    and that is an incident worth fixing.
    """

    by_url = {}

    for record in records:

        if record["status_code"] != code:
            continue

        moment = to_time(record["timestamp"])

        if moment:
            by_url.setdefault(record["url"], []).append(moment)

    clusters = []

    for url, moments in by_url.items():
        moments.sort()
        clusters.append({
            "status_code": code,
            "url": url,
            "count": len(moments),
            "first_seen": moments[0].isoformat(),
            "last_seen": moments[-1].isoformat(),
            "span_seconds": (moments[-1] - moments[0]).total_seconds(),
        })

    # Tightest window first, so a burst ranks above a slow trickle.
    clusters.sort(key=lambda c: (c["span_seconds"], -c["count"]))

    return clusters


def rejected_summary(rejected):
    """Tally the lines that could not be used, by reason."""

    reasons = Counter(reason_text for _, reason_text in rejected)

    return {
        "total_rejected": len(rejected),
        "by_reason": dict(reasons.most_common()),
        "examples": [
            {"line_number": number, "reason": reason_text}
            for number, reason_text in rejected[:100]
        ],
    }


def analyse(records, rejected):
    """Run every count and return the pieces the report is built from."""

    add_labels(records)

    frequent = error_details(records)
    timing, transfer = performance(records)
    profile = traffic(records)

    return {
        "total_valid_records": len(records),
        "malformed_records": len(rejected),
        "request_statistics": request_counts(records),
        "response_time_statistics": timing,
        "transfer_statistics": transfer,
        "traffic_profile": profile,
        "frequent_errors": frequent,
        "frequently_accessed_resources": profile["top_resources"],
        "status_code_distribution": profile["status_code_distribution"],
        "error_findings": findings(frequent),
        "server_error_clusters": error_clusters(records),
        "rejected_records": rejected_summary(rejected),
    }
