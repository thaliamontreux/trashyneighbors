import argparse
from pathlib import Path

import pymysql


def _split_sql_statements(sql_text: str):
    statements = []
    buf = []
    in_single = False
    in_double = False
    escape = False

    for ch in sql_text:
        if escape:
            buf.append(ch)
            escape = False
            continue

        if ch == "\\":
            buf.append(ch)
            escape = True
            continue

        if ch == "'" and not in_double:
            in_single = not in_single
            buf.append(ch)
            continue

        if ch == '"' and not in_single:
            in_double = not in_double
            buf.append(ch)
            continue

        if ch == ";" and not in_single and not in_double:
            stmt = "".join(buf).strip()
            buf = []
            if stmt:
                statements.append(stmt)
            continue

        buf.append(ch)

    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)

    return statements


def _run_sql_file(conn, sql_path: Path):
    sql_text = sql_path.read_text(encoding="utf-8")
    statements = _split_sql_statements(sql_text)

    with conn.cursor() as cur:
        for stmt in statements:
            s = stmt.strip()
            if not s:
                continue
            try:
                cur.execute(s)
            except pymysql.err.IntegrityError as e:
                if e.args and e.args[0] == 1062:
                    continue
                raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument(
        "--sql",
        action="append",
        required=True,
        help="Path to a .sql file to execute (can be repeated).",
    )
    args = parser.parse_args()

    sql_files = [Path(p).expanduser().resolve() for p in args.sql]
    for p in sql_files:
        if not p.is_file():
            raise SystemExit(f"Missing SQL file: {p}")

    conn = pymysql.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        charset="utf8mb4",
        autocommit=True,
    )

    try:
        for p in sql_files:
            print(f"Executing {p} ...")
            _run_sql_file(conn, p)
    finally:
        conn.close()

    print("Done")


if __name__ == "__main__":
    main()
