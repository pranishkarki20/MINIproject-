"""Interactive search over the records already read.

The brief asks that the user be able to specify an error type or a status code
and get the matching records back. Every branch checks what was typed instead
of trusting it.
"""

from analyse import reason

LIMIT = 20


def show(matches):
    """Print up to the limit and say how many were left out."""

    print(f"\nMatching records: {len(matches)}")

    for record in matches[:LIMIT]:
        print(
            f"{record['timestamp']} | {record['ip']} | "
            f"{record['method']} | {record['url']} | "
            f"HTTP {record['status_code']} | "
            f"{record['response_bytes']} bytes | {record['category']}"
        )

    if len(matches) > LIMIT:
        print(f"... and {len(matches) - LIMIT} more in the processed CSV.")


def search(records):
    """Run the menu until the user exits, or until input runs out."""

    print("\n" + "=" * 58)
    print("SEARCH LOG RECORDS")
    print("=" * 58)
    print("1. Search by HTTP status code (for example 404)")
    print("2. Search by error type (client / server / all)")
    print("3. Exit")

    while True:

        try:
            choice = input("\nEnter your choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            # Happens when the program is run with piped input.
            print("\nNo more input. Search ended.")
            return

        if choice == "3":
            print("Search finished.")
            return

        elif choice == "1":
            text = input("Enter HTTP status code: ").strip()

            try:
                code = int(text)
            except ValueError:
                print(f"Invalid status code: {text!r} is not a number")
                continue

            if not 100 <= code <= 599:
                print("Invalid status code: it must be between 100 and 599")
                continue

            matches = [r for r in records if r["status_code"] == code]
            print(f"HTTP {code} is {reason(code)}.")

        elif choice == "2":
            kind = input("Enter client, server, or all: ").strip().lower()

            wanted = {
                "client": ["Client Error"],
                "server": ["Server Error"],
                "all": ["Client Error", "Server Error"],
            }.get(kind)

            if wanted is None:
                print("Enter client, server, or all.")
                continue

            matches = [r for r in records if r["category"] in wanted]

        else:
            print("Please enter 1, 2, or 3.")
            continue

        show(matches)
