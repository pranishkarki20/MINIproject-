# Member Allocation, 20 Students

Mini Project 4: Application Log Monitoring and Error Analysis System
Course 25PCCS202, Unit IV, Prof. Abhishek Das

The project is 8 files and 34 functions. This maps all 20 members onto
specific functions, so everyone has something concrete to read and something
concrete to say.

Fill in the name and USN before you send this to the group.

---

## How to use this

Read your own functions first, then read the two files next to yours in the
pipeline so you know what comes in and what goes out. The brief says every
student must understand how the project works in detail, and the faculty may
ask any of you to inspect a particular function or run a different query.

The order the program runs in:

```
main.py -> read_log.py -> validate.py -> analyse.py
        -> write_csv.py -> write_json.py -> make_summary.py -> search.py
```

---

## Allocation

| # | Name | USN | Read these functions | What to be able to say |
| --- | --- | --- | --- | --- |
| 01 | ______ | ______ | `main.py`: `main()`, plus the path constants at the top | The five stages in order, why each one stops the run if it fails, and why the program returns an exit code |
| 02 | ______ | ______ | `main.py`: `process()` | The two levels of exception handling. The outer `try` is about the whole file, the inner one is about one line. Explain the `else` after the loop and the `finally` |
| 03 | ______ | ______ | `read_log.py`: `read_lines()`, `read_log()` | `with open()` and `enumerate`, why `errors="replace"` is used, and how the file extension decides whether the text reader or the CSV reader runs |
| 04 | ______ | ______ | `read_log.py`: `APACHE_LINE`, `parse_apache_line()` | The Combined Log Format layout, and why a regex is needed instead of splitting on spaces. Show what the named groups give you |
| 05 | ______ | ______ | `read_log.py`: `read_csv_rows()`, `pick_fields()`, `ALIASES` | The `csv.DictReader` path, the alias table, and the `response_ms` bug where a missing alias made every duration 0 without raising anything |
| 06 | ______ | ______ | `read_log.py`: `first_number()`, and the nginx duration in `parse_apache_line()` | That nginx `$request_time` is fractional seconds while a CSV column is milliseconds, so the unit has to be stated and never guessed |
| 07 | ______ | ______ | `validate.py`: `to_time()`, `check_time()` | The six timestamp layouts, why an impossible date like 32/Dec is rejected, and the `0::00` bug caused by slicing a timestamp instead of parsing it |
| 08 | ______ | ______ | `validate.py`: `check_status()`, `build_record()` | That 999 converts to an int happily but is not a status code, and the order the checks run in and why |
| 09 | ______ | ______ | `validate.py`: `check_duration()`, `check_size()` | Why an absent duration stays `None` instead of becoming 0, and why a `-` size is not a reason to reject the whole line |
| 10 | ______ | ______ | `analyse.py`: `STATUS_REASONS`, `classify()`, `reason()`, `add_labels()` | The five categories, `if` / `elif` / `else`, and why 4xx and 5xx are kept apart instead of lumped together as errors |
| 11 | ______ | ______ | `analyse.py`: `request_counts()` | How the error percentage is worked out, and that failed requests means 4xx plus 5xx |
| 12 | ______ | ______ | `analyse.py`: `performance()` | Why average response time is `None` on this dataset instead of 0, and how response size is used as the substitute for finding slow requests |
| 13 | ______ | ______ | `analyse.py`: `traffic()` | `Counter`, `most_common()`, how the busiest hour is found, and why the client IP count is only 2 on this dataset |
| 14 | ______ | ______ | `analyse.py`: `error_details()` | That errors are counted by code **and** by URL, and why that second grouping is what turns a count into a finding |
| 15 | ______ | ______ | `analyse.py`: `findings()`, `rejected_summary()` | The 45.1% result: 204 of 452 404s are one scanner path. And how rejected lines are tallied by reason instead of dumped as free text |
| 16 | ______ | ______ | `analyse.py`: `error_clusters()` | That all nine 500s look spread over nine hours, but grouped by page, six land on `/126.php` inside 16 seconds. That is an incident, not noise |
| 17 | ______ | ______ | `write_csv.py`: `write_csv()`; `search.py`: `show()` | Why `newline=""` is required, why `None` becomes an empty cell instead of the word None, and how search output is capped at 20 rows |
| 18 | ______ | ______ | `write_json.py`: `DATASET`, `build_report()`, `write_json()` | The report structure, and why the DOI, URL and licence are written into the JSON so a number cannot be separated from its source |
| 19 | ______ | ______ | `make_summary.py`: `read_report()`, `get()` | That the JSON is re-opened from disk rather than reused from memory, which is what the brief asks for. Explain the `try` / `except` / `else` / `finally` and why `get()` avoids a `KeyError` |
| 20 | ______ | ______ | `make_summary.py`: `make_text()`, `write_text()`; `search.py`: `search()` | How the text report is laid out from the read-back dictionary, and how the menu validates a letter typed as a status code or a code of 999 |

---

## Extra deliverables

These are not code, and the light-est members should take them so nobody looks
underworked.

| Item | Who |
| --- | --- |
| Project report: problem statement, objectives, methodology | 01, 02, 03 |
| Dataset description and citation, field table | 04, 05, 06 |
| Validation rules section of the report | 07, 08, 09 |
| Results and interpretation section | 10 to 16 |
| Output design and sample outputs | 17, 18 |
| Limitations, references, and the demonstration script | 19, 20 |

---

## Screenshots to capture before submission

Section 4 of the brief asks for screenshots or sample outputs. Each member
should have these three:

1. Your own functions open in the editor.
2. The program running, with the output your functions produce visible.
3. One invalid input being rejected. `16` and `15` can show the malformed
   record report, `20` can show the menu refusing a bad status code. This is
   the best screenshot to have, because it proves you ran the code rather than
   only read it.

---

## If the faculty changes the input

Be ready for these, they are the likely requests:

- "Use a different log." Change `INPUT_FILE` in `main.py` to a CSV or another
  text log and run it.
- "Show me every 500." Menu option 1, type `500`.
- "What is the error rate if you count redirects as failures?" That is
  `analyse.request_counts()`, one line.
- "Why is response time missing?" README section 2. The Combined Log Format
  does not record it, and the program says so instead of inventing it.
- "Explain this function." Yours. Know the three lines around it too.
