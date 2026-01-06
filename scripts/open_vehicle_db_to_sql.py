import argparse
import json
import os
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


def _batched(iterable, batch_size):
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Path to open-vehicle-db repo root or to its data folder.",
    )
    parser.add_argument(
        "--output-sql",
        required=True,
        help="Output .sql file path.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of rows per INSERT statement.",
    )
    parser.add_argument(
        "--drop-first",
        action="store_true",
        help="Include DROP TABLE statements before CREATE TABLE.",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir).expanduser().resolve()
    output_sql = Path(args.output_sql).expanduser().resolve()

    if (input_dir / "data").is_dir():
        data_dir = input_dir / "data"
    else:
        data_dir = input_dir

    makes_models_path = data_dir / "makes_and_models.json"
    styles_dir = data_dir / "styles"

    if not makes_models_path.is_file():
        raise SystemExit(f"Missing required file: {makes_models_path}")
    if not styles_dir.is_dir():
        raise SystemExit(f"Missing required directory: {styles_dir}")

    makes_models = _load_json(makes_models_path)

    output_sql.parent.mkdir(parents=True, exist_ok=True)

    make_id_by_slug = {}
    model_id_by_make_slug_and_name = {}

    next_make_id = 1
    next_model_id = 1
    next_style_id = 1

    make_rows = []
    model_rows = []
    model_year_rows = []
    style_rows = []
    style_year_rows = []

    for make in makes_models:
        make_slug = make.get("make_slug")
        make_name = make.get("make_name")
        if not make_slug or not make_name:
            raise SystemExit(f"Invalid make entry missing make_slug/make_name: {make}")

        first_year = make.get("first_year")
        last_year = make.get("last_year")

        make_id = next_make_id
        next_make_id += 1
        make_id_by_slug[make_slug] = make_id

        make_rows.append((make_id, make_slug, make_name, first_year, last_year))

        models = make.get("models") or {}
        if not isinstance(models, dict):
            raise SystemExit(f"Invalid models structure for make {make_name}: expected object")

        for model_key, model_info in models.items():
            if not isinstance(model_info, dict):
                continue
            model_name = model_info.get("model_name") or model_key
            model_id = next_model_id
            next_model_id += 1

            model_id_by_make_slug_and_name[(make_slug, model_name)] = model_id
            model_rows.append((model_id, make_id, model_name))

            years = model_info.get("years") or []
            if not isinstance(years, list):
                raise SystemExit(f"Invalid years for model {model_name} ({make_name})")

            for y in years:
                if isinstance(y, int):
                    model_year_rows.append((model_id, y))

    for make_slug, make_id in make_id_by_slug.items():
        style_path = styles_dir / f"{make_slug}.json"
        if not style_path.is_file():
            continue

        style_doc = _load_json(style_path)
        if not isinstance(style_doc, dict):
            raise SystemExit(f"Invalid style JSON in {style_path}")

        for model_name, styles in style_doc.items():
            if not isinstance(styles, dict):
                continue

            model_id = model_id_by_make_slug_and_name.get((make_slug, model_name))
            if model_id is None:
                model_id = next_model_id
                next_model_id += 1

                model_id_by_make_slug_and_name[(make_slug, model_name)] = model_id
                model_rows.append((model_id, make_id, model_name))

            for style_name, style_info in styles.items():
                if not isinstance(style_info, dict):
                    style_info = {"value": style_info}

                years = style_info.get("years") or []
                if not isinstance(years, list):
                    years = []

                style_id = next_style_id
                next_style_id += 1

                style_rows.append(
                    (
                        style_id,
                        make_id,
                        model_id,
                        style_name,
                        json.dumps(style_info, ensure_ascii=False, separators=(",", ":")),
                    )
                )

                for y in years:
                    if isinstance(y, int):
                        style_year_rows.append((style_id, y))

    with output_sql.open("w", encoding="utf-8", newline="\n") as out:
        out.write("SET NAMES utf8mb4;\n")
        out.write("SET FOREIGN_KEY_CHECKS=0;\n")
        out.write("START TRANSACTION;\n\n")

        if args.drop_first:
            out.write("DROP TABLE IF EXISTS vehicle_style_year;\n")
            out.write("DROP TABLE IF EXISTS vehicle_style;\n")
            out.write("DROP TABLE IF EXISTS vehicle_model_year;\n")
            out.write("DROP TABLE IF EXISTS vehicle_model;\n")
            out.write("DROP TABLE IF EXISTS vehicle_make;\n\n")

        out.write(
            "CREATE TABLE IF NOT EXISTS vehicle_make (\n"
            "  make_id INT NOT NULL,\n"
            "  make_slug VARCHAR(64) NOT NULL,\n"
            "  make_name VARCHAR(128) NOT NULL,\n"
            "  first_year SMALLINT NULL,\n"
            "  last_year SMALLINT NULL,\n"
            "  PRIMARY KEY (make_id),\n"
            "  UNIQUE KEY uk_vehicle_make_slug (make_slug),\n"
            "  KEY idx_vehicle_make_name (make_name)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        out.write(
            "CREATE TABLE IF NOT EXISTS vehicle_model (\n"
            "  model_id INT NOT NULL,\n"
            "  make_id INT NOT NULL,\n"
            "  model_name VARCHAR(128) NOT NULL,\n"
            "  PRIMARY KEY (model_id),\n"
            "  UNIQUE KEY uk_vehicle_model_make_name (make_id, model_name),\n"
            "  KEY idx_vehicle_model_name (model_name),\n"
            "  CONSTRAINT fk_vehicle_model_make FOREIGN KEY (make_id) REFERENCES vehicle_make(make_id)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        out.write(
            "CREATE TABLE IF NOT EXISTS vehicle_model_year (\n"
            "  model_id INT NOT NULL,\n"
            "  year SMALLINT NOT NULL,\n"
            "  PRIMARY KEY (model_id, year),\n"
            "  KEY idx_vehicle_model_year_year (year),\n"
            "  CONSTRAINT fk_vehicle_model_year_model FOREIGN KEY (model_id) REFERENCES vehicle_model(model_id)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        out.write(
            "CREATE TABLE IF NOT EXISTS vehicle_style (\n"
            "  style_id INT NOT NULL,\n"
            "  make_id INT NOT NULL,\n"
            "  model_id INT NOT NULL,\n"
            "  style_name VARCHAR(255) NOT NULL,\n"
            "  style_info_json JSON NOT NULL,\n"
            "  PRIMARY KEY (style_id),\n"
            "  UNIQUE KEY uk_vehicle_style_make_model_name (make_id, model_id, style_name(191)),\n"
            "  KEY idx_vehicle_style_name (style_name),\n"
            "  CONSTRAINT fk_vehicle_style_make FOREIGN KEY (make_id) REFERENCES vehicle_make(make_id),\n"
            "  CONSTRAINT fk_vehicle_style_model FOREIGN KEY (model_id) REFERENCES vehicle_model(model_id)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        out.write(
            "CREATE TABLE IF NOT EXISTS vehicle_style_year (\n"
            "  style_id INT NOT NULL,\n"
            "  year SMALLINT NOT NULL,\n"
            "  PRIMARY KEY (style_id, year),\n"
            "  KEY idx_vehicle_style_year_year (year),\n"
            "  CONSTRAINT fk_vehicle_style_year_style FOREIGN KEY (style_id) REFERENCES vehicle_style(style_id)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        def write_insert(table, columns, rows):
            for batch in _batched(rows, args.batch_size):
                out.write(f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n")
                values_sql = ",\n".join(
                    "(" + ", ".join(_sql_quote(v) for v in row) + ")" for row in batch
                )
                out.write(values_sql)
                out.write(";\n")
            out.write("\n")

        write_insert(
            "vehicle_make",
            ["make_id", "make_slug", "make_name", "first_year", "last_year"],
            make_rows,
        )
        write_insert(
            "vehicle_model",
            ["model_id", "make_id", "model_name"],
            model_rows,
        )
        write_insert(
            "vehicle_model_year",
            ["model_id", "year"],
            model_year_rows,
        )
        write_insert(
            "vehicle_style",
            ["style_id", "make_id", "model_id", "style_name", "style_info_json"],
            style_rows,
        )
        write_insert(
            "vehicle_style_year",
            ["style_id", "year"],
            style_year_rows,
        )

        out.write("COMMIT;\n")
        out.write("SET FOREIGN_KEY_CHECKS=1;\n")

    print(f"Wrote SQL: {output_sql}")
    print(f"Makes: {len(make_rows)}")
    print(f"Models: {len(model_rows)}")
    print(f"Model years: {len(model_year_rows)}")
    print(f"Styles: {len(style_rows)}")
    print(f"Style years: {len(style_year_rows)}")


if __name__ == "__main__":
    main()
