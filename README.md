# Application Log Monitoring and Error Analysis System

Mini Project 4 for **25PCCS202 Python Programming**, Unit IV: File Handling,
CSV, JSON and Exception Handling.

A Python program that reads a real web server access log, works out which
requests succeeded and which failed, counts the errors and the busiest pages,
writes a processed CSV and a JSON report, reads that JSON back to build a
readable summary, and then lets the user search the records.

---

## 1. How to run

```bash
python main.py
```

Python 3.8 or newer. Nothing to install. On Windows, if plain `python` opens
Python 2, use `py -3 main.py`.

The log is read from `data/web-access.log.1`. To use another log, change
`INPUT_FILE` at the top of `main.py`. A CSV export works too, as does an nginx
log that records request times.

---

## 2. Dataset

| Item | Value |
| --- | --- |
| Title | Web Server Log Dataset |
| Author | Anonim |
| Publisher | Zenodo, 2026-05-03 |
| DOI | [10.5281/zenodo.20001206](https://doi.org/10.5281/zenodo.20001206) |
| Page | https://zenodo.org/records/20001206 |
| Direct download | https://zenodo.org/api/records/20001206/files/organization-x.zip/content |
| Licence | MIT |
| File used | `organization-x/log/apache2/web-access.log.1` from that archive |
| Records | 17,757 |
| Time span | 06 Oct 2025 07:35 to 07 Oct 2025 07:34, a full 24 hours |

The archive holds raw log files from two public sector organisations in
Indonesia, called Organization X and Organization Y. These were collected from
a live Apache server and published for research into reconstructing web
application attacks.

The file in `data/` is the original log copied out of the archive unchanged. It
was not cleaned, sorted, filtered or edited, so every number the program prints
comes from real traffic.

### Fields

Apache's Combined Log Format, one request per line:

```
255.102.154.224 - - [06/Oct/2025:07:35:12 +0700] "GET /1.php HTTP/1.0" 200 8571 "https://sub1.domain1.com/3.php" "Mozilla/5.0 (Windows NT 10.0..."
```

| Field | Meaning here |
| --- | --- |
| IP address | Client address. The publisher anonymised these into one address. |
| ident, user | Always `-`. Apache does not use RFC 1413 and the visitors were anonymous. |
| timestamp | Local time the request was served, with a `+0700` offset. |
| method | Request type. GET, HEAD, POST, OPTIONS and PUT all appear. |
| path | Requested resource. 1,444 distinct resources appear. |
| protocol | HTTP version. All traffic here is HTTP/1.0. |
| status | HTTP status code. 200, 302, 304, 206, 404, 405 and 500 all occur. |
| bytes | Response size in bytes. |
| referer | Page the request came from, or `-`. 288 distinct values. |
| user agent | Software that made the request. 248 distinct agents: real browsers plus uptime bots `Uptime-Kuma/1.23.13` (2,766 hits) and `HetrixTools` (2,181 hits). |

---

## 3. The files

| File | Lines | What it does |
| --- | --- | --- |
| `main.py` | 124 | Runs the five stages. Holds the paths and the two-level `try` / `except` / `else` / `finally`. |
| `read_log.py` | 170 | Opens the log and splits each line into fields. A regex for a text log, `csv.DictReader` for a CSV. |
| `validate.py` | 145 | Checks each field and converts it to a real type. Raises `ValueError` with a reason. |
| `analyse.py` | 295 | Counts categories, errors, resources, sizes and hours. Groups errors by URL. |
| `write_csv.py` | 45 | Writes `output/processed_logs.csv`. |
| `write_json.py` | 67 | Builds and writes `output/summary_report.json`, citation included. |
| `make_summary.py` | 187 | Reads that JSON back off the disk and lays it out as `output/final_summary.txt`. |
| `search.py` | 88 | The interactive menu to find records by status code or error type. |

The order the program runs in:

```
data/web-access.log.1
   -> read_log      split every line into fields
   -> validate      one record, or a reason it was rejected
   -> analyse       categories, counts, error breakdown
   -> write_csv     output/processed_logs.csv
   -> write_json    output/summary_report.json
   -> make_summary  read the JSON back, write output/final_summary.txt
   -> search        interactive
```

---

## 4. Unit IV concepts, and where each one is used

| Requirement | Where |
| --- | ---|
| File handling with `with open()` | `read_log.read_lines`, `read_log.read_csv_rows`, and all four writers. |
| Read and write operations | Reads a text log, writes CSV, JSON and a text file. |
| Process a CSV or text dataset | Text log by default. CSV automatically when the file ends in `.csv`. |
| Regular expressions | `read_log.APACHE_LINE`, because a user agent is full of spaces. |
| Identify successful, client, server and failed requests | `analyse.classify` and `analyse.request_counts`. |
| Error percentage | `request_statistics.error_percentage`, 2.60% on this dataset. |
| Frequent errors | `analyse.error_details`, by code and by URL. |
| Frequently accessed resources | `analyse.traffic`, top 10 of 1,444. |
| High response time requests | `analyse.performance`. The Combined Log Format does not record duration, so the report says so and uses response size instead. |
| User specifies an error type or status code | `search.search`, options 1 and 2. |
| Missing or malformed records handled | `main.process` catches per line and stores the line number and reason. |
| `try` | Outer, around the whole read. Inner, around each single line. |
| `except` | `FileNotFoundError`, `PermissionError`, `UnicodeDecodeError`, `ValueError`, `TypeError`, `OSError`, `json.JSONDecodeError`, `EOFError`, `KeyboardInterrupt`. All named, no bare `except:`. |
| `else` | After the record loop in `main.process`, and after the JSON parse in `make_summary.read_report`. |
| `finally` | After the read stage and after the JSON read stage, so they run on success and on error. |
| Specific exception types, not generic | Each handler names one type and prints a different message. |
| JSON read back into Python | `make_summary.read_report` re-opens the file. The summary is built from what was read, not from the dictionary the program already had. |
| Functions and modularity | 34 functions across 8 files, no classes. |
| No hard coded answers | Every statistic is counted from the log at run time. |

---

## 5. Testing

Tested on four inputs.

| Input | Result |
| --- | --- |
| The real Apache log | 17,757 valid, 0 malformed. 452 404s, 9 500s, 1 405. Error rate 2.60%. |
| A CSV export with a `response_ms` column | Durations read correctly. Average 1347.33 ms, 2 slow requests. |
| An nginx log appending `$request_time` | Read as fractional seconds. Average 2522.67 ms, 2 slow requests. |
| A copy of the real log with 4 lines damaged | 401 records kept. Rejections reported as `Line does not match the Apache Combined Log Format`, `Empty record`, `Invalid timestamp format` and `Invalid HTTP status code`, each with its line number. |

Invalid input at the menu was also tested: a letter instead of a status code, a
status code of 999, and an unknown error type all print a message and ask again
instead of crashing.

Two bugs found and fixed while building this:

- **Every response time was 0.** The list of accepted duration column names did
  not include `response_ms`, which is what the file actually used, so the lookup
  fell through to its default of `"0"`. Nothing raised. A wrong answer that
  never errors is the worst kind of bug.
- **Busiest hour printed `0::00`.** The hour was taken by slicing
  `timestamp[12:14]`, which is right for an Apache timestamp and wrong for an
  ISO one. It now parses the timestamp instead of slicing it.

---

## 6. Results

```
Valid records             : 17757
Malformed records         : 0
Successful requests (2xx) : 10,003
Redirects (3xx)           : 7,292
Client errors (4xx)       : 453
Server errors (5xx)       : 9
Error percentage          : 2.60%
Average response size     : 8,571.3 bytes
Largest response          : 1,319,785 bytes
Heavy transfers           : 339
Total data sent           : 145.15 MB
Busiest hour              : 09:00
Distinct resources        : 1,444
```

---

## 7. References

1. Anonim. *Web Server Log Dataset*. Zenodo, 2026. DOI: 10.5281/zenodo.20001206. MIT licence.
2. Apache Software Foundation. *Log Files*, Combined Log Format. https://httpd.apache.org/docs/trunk/logs.html
3. nginx. *Module ngx_http_log_module*, `$request_time`. https://nginx.org/en/docs/http/ngx_http_log_module.html
4. MDN Web Docs. *HTTP response status codes*. https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
5. Python Software Foundation. Standard library documentation for `csv`, `json`, `re`, `datetime` and the `with` statement. https://docs.python.org/3/library/
