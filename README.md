# Application Log Monitoring and Error Analysis System

Mini Project 4 for **25PCCS202 Python Programming**, Unit IV: File Handling,
CSV, JSON and Exception Handling.

A Python program that reads a real web server access log, works out which
requests succeeded and which failed, counts the errors and the busiest pages,
writes a processed CSV and a JSON report, reads that JSON back to build a
readable summary, and then lets the user search the records.

Nine flat modules, 1,508 lines, plain functions, standard library core with an optional pandas view.

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

| File | Lines | Fns | What it does |
| --- | --- | --- | --- |
| `main.py` | 155 | 2 | Runs the stages. Holds the paths and the two-level `try` / `except` / `else` / `finally`. |
| `read_log.py` | 192 | 7 | Opens the log, sniffs whether it is CSV or text, splits each line into fields. |
| `validate.py` | 145 | 6 | Checks each field and converts it to a real type. Raises `ValueError` with a reason. |
| `analyse.py` | 314 | 11 | Categories, error rate, resources, sizes, hours, errors grouped by code and by URL. |
| `write_csv.py` | 128 | 4 | Writes the processed CSV and the hourly summary, reads the hourly file back to check it. |
| `write_json.py` | 67 | 2 | Builds and writes `output/summary_report.json`, citation included. |
| `make_summary.py` | 298 | 6 | Reads the JSON back, writes the text summary, keeps a run history. |
| `search.py` | 88 | 2 | The interactive menu to find records by status code or error type. |
| `pandas_view.py` | 121 | 1 | Optional. Reads and writes CSV and JSON through pandas and cross-checks the totals. |

Total 1,508 lines and 41 functions. The core uses only the standard library,
and `pandas_view.py` is called inside a `try` that catches `ImportError`, so
the project runs unchanged on a machine without pandas.

The order the program runs in:

```
data/web-access.log.1
   -> read_log      sniff the format, split every line into fields
   -> validate      one record, or a reason it was rejected
   -> analyse       categories, counts, error breakdown
   -> write_csv     processed_logs.csv and hourly_summary.csv, then read back
   -> pandas_view   optional, reads the CSV and writes CSV and JSON
   -> write_json    summary_report.json
   -> make_summary  read the JSON back, write final_summary.txt and run history
   -> search        interactive
```

---

## 4. Unit IV concepts, and where each one is used

The syllabus lists Unit IV as *File Handling, JSON, CSV & Error Management*.
Every item in that list is below, with the function that demonstrates it.

| Syllabus item | Where it is used |
| --- | --- |
| File handling basics: `read` | `make_summary.read_history()` reads the whole history file with `file.read()` |
| File handling basics: `readline` | `read_log.detect_format()` peeks at line one with `readline()` to choose the reader |
| File handling basics: `write` | `make_summary.write_text()` and `write_json.write_json()` |
| File handling basics: `readlines` | `read_log.read_lines()` loads the log with `readlines()` |
| File handling basics: `writelines` | `make_summary.write_text()` writes the report with `writelines()` |
| File modes | `"r"` in `read_log`, `"w"` in the three writers, `"a"` in `make_summary.record_run()` |
| Context manager `with open()` | 11 uses across read and write paths, no bare `open()` left unclosed |
| Working with CSV using the `csv` module | `csv.reader` and `csv.writer` in `write_csv`, `csv.DictReader` in `read_log`, `csv.DictWriter` in `write_csv` |
| JSON handling using the `json` module | `json.dump` in `write_json`, `json.load` in `read_report`, `json.loads` and `json.dumps` in the run history |
| Exception handling: `try` | `main.process()` outer around the read, inner around each record |
| Exception handling: `except` | 23 handlers, each naming a specific type |
| Exception handling: `else` | 10 `else` clauses in total, including after the record loop in `main.process` and after the JSON parse in `read_report` |
| Exception handling: `finally` | `main.process()` and `read_report()`, so the stage marker prints on success and on failure |
| Specific exception types | `FileNotFoundError`, `PermissionError`, `UnicodeDecodeError`, `ValueError`, `TypeError`, `OSError`, `ImportError`, `json.JSONDecodeError`, `EOFError`, `KeyboardInterrupt`. No bare `except:` |
| Raising exceptions | `read_log.parse_apache_line`, `read_log.detect_format`, `read_log.read_csv_rows`, `validate.check_time`, `check_status`, `check_duration`, `check_size`, `build_record` all `raise ValueError` with a reason |
| Introduction to pandas for CSV and JSON | `pandas_view.summarise()` does `read_csv`, `groupby`, `to_csv`, `to_json` and `read_json`, then checks its totals against the standard library |

And the requirements named in the project brief itself:

| Brief requirement | Where |
| --- | --- |
| Identify successful, client, server and failed requests | `analyse.classify` and `analyse.request_counts` |
| Error percentage | `request_statistics.error_percentage`, 2.60% on this dataset |
| Frequent errors | `analyse.error_details`, by code and by URL |
| Frequently accessed resources | `analyse.traffic`, top 10 of 1,444 |
| High response time requests | `analyse.performance`. The format records no duration, so it says so and uses response size |
| User specifies an error type or status code | `search.search`, options 1 and 2 |
| Missing or malformed records handled | `main.process` catches per line, `analyse.rejected_summary` tallies by reason |
| JSON read back and used for the summary | `make_summary.read_report` re-opens the file, `make_text` reads only from it |
| Analysis, output and interpretation | Section 7 |
| Code quality, modularity | 9 modules, 41 functions, no classes, standard library core |

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

## 6. Outputs

| File | Size | What it is for |
| --- | --- | --- |
| `output/processed_logs.csv` | 17,758 lines | One row per valid request, for opening in a spreadsheet |
| `output/hourly_summary.csv` | 25 lines | Hour by hour totals, written with `csv.writer` |
| `output/summary_report.json` | 18 top-level keys | All statistics plus the dataset citation. What `make_summary` re-reads |
| `output/final_summary.txt` | 88 lines | The human report, built from the JSON read back off disk |
| `output/run_history.txt` | one line per run | Appended in mode `"a"`, so repeat runs can be compared |
| `output/hourly_pandas.csv` | 25 lines | The same hourly table written by pandas instead of `csv.writer` |
| `output/pandas_summary.json` | 25 rows | Written by `to_json()`, then read back by `pd.read_json()` |

Two of these exist to prove the others are right. `write_csv.read_hourly()`
reads `hourly_summary.csv` back with `csv.reader` and checks the requests add
up to the number analysed, and `pandas_view` compares its own totals against
the standard library result. Both checks pass and both are printed in the
summary under `OUTPUT SELF-CHECK` and `PANDAS CROSS-CHECK`.

### 6.1 Processed CSV columns

timestamp, ip, method, url, status_code, response_bytes, response_time_ms,
category, error_message. Two real rows:

```
timestamp,ip,method,url,status_code,response_bytes,response_time_ms,category,error_message
06/Oct/2025:07:35:12 +0700,255.102.154.224,GET,/1.php,200,8571,,Successful,
06/Oct/2025:07:38:16 +0700,255.102.154.224,GET,/4.png,404,656,,Client Error,404 Not Found
```

### 6.2 Run history format

One compact JSON object per line, appended each run and read back with
`json.loads()` line by line:

```
{"run": 3, "at": "2026-11-17T12:31:44", "records": 17757, "rejected": 0, "error_pct": 2.6, "total_mb": 145.15}
```

---

## 7. Results

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
Busiest hour              : 09:00 (1,976 requests)
Worst hour for errors     : 10:00 at 12.59% (219 of 1,740)
Distinct resources        : 1,444
```

### What the new checks found

**The errors are not spread evenly across the day.** Hour 10:00 returned 219
failures out of 1,740 requests, a 12.59% error rate against 2.60% for the day
as a whole. All 219 were 404s. A quiet hour with a fifth of its requests
failing is more interesting than the busiest hour with almost none, which is
why `analyse.traffic()` reports the worst error rate separately from the busiest
hour rather than only reporting volume.

**One file accounts for most of the bandwidth.** `/images/1.ico` sent
78,190,881 bytes, which is more than half of the 152,200,617 bytes the whole log
transferred. Ranking by total bytes sent, rather than by request count, points at
a different resource than ranking by count does: `/1.php` has the most requests
but `/images/1.ico` has the most traffic.

**Both self-checks passed.** `write_csv.read_hourly()` reads the hourly file back
with `csv.reader` and the 24 hour rows add up to 17,757, matching the number of
records analysed. The pandas view reports the same 17,757 rows, the same busiest
hour of 09:00 and the same 1,976 requests, and its JSON round trip came back
intact.

Two engines written independently, one in the standard library and one in pandas,
agreeing on every figure is the strongest correctness evidence in the project.

---

## 8. References

1. Anonim. *Web Server Log Dataset*. Zenodo, 2026. DOI: 10.5281/zenodo.20001206. MIT licence.
2. Apache Software Foundation. *Log Files*, Combined Log Format. https://httpd.apache.org/docs/trunk/logs.html
3. nginx. *Module ngx_http_log_module*, `$request_time`. https://nginx.org/en/docs/http/ngx_http_log_module.html
4. MDN Web Docs. *HTTP response status codes*. https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
5. Python Software Foundation. Standard library documentation for `csv`, `json`, `re`, `datetime` and the `with` statement. https://docs.python.org/3/library/
