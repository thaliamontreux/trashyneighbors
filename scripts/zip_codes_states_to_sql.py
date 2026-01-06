import argparse
import csv
from pathlib import Path


def _sql_quote(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    s = s.replace("\\", "\\\\").replace("'", "''")
    return f"'{s}'"


def _write_insert(out, table, columns, rows):
    out.write(f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n")
    out.write(
        ",\n".join(
            "(" + ", ".join(_sql_quote(v) for v in row) + ")" for row in rows
        )
    )
    out.write(";\n\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-csv",
        required=True,
        help="Path to zip_codes_states.csv",
    )
    parser.add_argument(
        "--output-sql",
        required=True,
        help="Output .sql file path.",
    )
    parser.add_argument(
        "--table",
        default="zip_code_location",
        help="Target table name.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=2000,
        help="Number of rows per INSERT statement.",
    )
    parser.add_argument(
        "--drop-first",
        action="store_true",
        help="Include DROP TABLE statement before CREATE TABLE.",
    )
    args = parser.parse_args()

    input_csv = Path(args.input_csv).expanduser().resolve()
    output_sql = Path(args.output_sql).expanduser().resolve()

    if not input_csv.is_file():
        raise SystemExit(f"Missing input CSV: {input_csv}")

    output_sql.parent.mkdir(parents=True, exist_ok=True)

    expected_cols = [
        "zip_code",
        "latitude",
        "longitude",
        "city",
        "state",
        "county",
    ]

    with (
        input_csv.open("r", encoding="utf-8", newline="") as f,
        output_sql.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as out,
    ):
        reader = csv.DictReader(f)
        if reader.fieldnames != expected_cols:
            raise SystemExit(
                "Unexpected CSV header.\n"
                f"Expected: {expected_cols}\n"
                f"Got: {reader.fieldnames}\n"
                "If your file differs, tell me and I will adapt the importer."
            )

        out.write("SET NAMES utf8mb4;\n")
        out.write("SET FOREIGN_KEY_CHECKS=0;\n")
        out.write("START TRANSACTION;\n\n")

        if args.drop_first:
            out.write(f"DROP TABLE IF EXISTS {args.table};\n\n")

        out.write(
            f"CREATE TABLE IF NOT EXISTS {args.table} (\n"
            "  zip_code CHAR(5) NOT NULL,\n"
            "  latitude DECIMAL(9,6) NULL,\n"
            "  longitude DECIMAL(9,6) NULL,\n"
            "  city VARCHAR(128) NOT NULL,\n"
            "  state CHAR(2) NOT NULL,\n"
            "  county VARCHAR(128) NOT NULL,\n"
            "  PRIMARY KEY (zip_code, city, state, county),\n"
            "  KEY idx_zip_code (zip_code),\n"
            "  KEY idx_state (state),\n"
            "  KEY idx_city (city),\n"
            "  KEY idx_state_city (state, city)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 "
            "COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        batch = []
        total = 0

        for row in reader:
            zip_code = (row.get("zip_code") or "").strip().strip('"')
            if not zip_code:
                continue
            # Preserve leading zeros and normalize to 5 chars when possible
            zip_code = zip_code.zfill(5)

            city = (row.get("city") or "").strip().strip('"')
            state = (row.get("state") or "").strip().strip('"')
            county = (row.get("county") or "").strip().strip('"')

            lat_raw = row.get("latitude")
            lon_raw = row.get("longitude")

            latitude = None
            longitude = None

            try:
                if lat_raw not in (None, ""):
                    latitude = float(lat_raw)
                if lon_raw not in (None, ""):
                    longitude = float(lon_raw)
            except ValueError:
                # Keep NULLs if parsing fails
                latitude = None
                longitude = None

            # county participates in PK; keep non-null
            if county == "":
                county = "UNKNOWN"

            batch.append((zip_code, latitude, longitude, city, state, county))
            total += 1

            if len(batch) >= args.batch_size:
                _write_insert(
                    out,
                    args.table,
                    [
                        "zip_code",
                        "latitude",
                        "longitude",
                        "city",
                        "state",
                        "county",
                    ],
                    batch,
                )
                batch = []

        if batch:
            columns = [
                "zip_code",
                "latitude",
                "longitude",
                "city",
                "state",
                "county",
            ]
            _write_insert(out, args.table, columns, batch)

        out.write("COMMIT;\n")
        out.write("SET FOREIGN_KEY_CHECKS=1;\n")

    print(f"Wrote SQL: {output_sql}")
    print(f"Rows: {total}")


if __name__ == "__main__":
    main()
