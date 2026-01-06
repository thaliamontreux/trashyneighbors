import argparse
import json
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


def _load_json_lines(path: Path):
    records = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-file",
        required=True,
        help="Path to fielddata.txt (JSON lines).",
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

    input_file = Path(args.input_file).expanduser().resolve()
    output_sql = Path(args.output_sql).expanduser().resolve()

    if not input_file.is_file():
        raise SystemExit(f"Missing input file: {input_file}")

    output_sql.parent.mkdir(parents=True, exist_ok=True)

    records = _load_json_lines(input_file)

    ref_tables = []
    vehicle_colors = []
    vehicle_types = []
    vehicle_conditions = []
    vehicle_makes = []
    nuisance_categories = []
    nuisance_items = []
    email_templates = []
    user_submitted_vehicle_model_statuses = []
    import_manifests = []

    for rec in records:
        if not isinstance(rec, dict):
            continue

        record_type = rec.get("record_type")
        if record_type == "REFERENCE_TABLE":
            table = rec.get("table")
            key_fields = rec.get("key_fields")
            mode = rec.get("mode")
            if table and isinstance(key_fields, list):
                ref_tables.append(
                    (
                        table,
                        json.dumps(
                            key_fields,
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                        mode or "",
                    )
                )
            continue

        if record_type == "IMPORT_MANIFEST":
            import_key = rec.get("import_key")
            if not import_key:
                continue

            import_manifests.append(
                (
                    import_key,
                    rec.get("priority"),
                    rec.get("source_name"),
                    rec.get("source_url"),
                    rec.get("licensing_note"),
                    rec.get("installer_behavior"),
                    json.dumps(
                        rec.get("tables_target") or [],
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        rec.get("references") or [],
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                )
            )
            continue

        if record_type != "SEED":
            continue

        table = rec.get("table")
        row = rec.get("row")
        if not table or not isinstance(row, dict):
            continue

        if table == "ref_vehicle_color":
            name = row.get("color_name")
            if name:
                vehicle_colors.append((name,))
        elif table == "ref_vehicle_type":
            name = row.get("type_name")
            if name:
                vehicle_types.append((name,))
        elif table == "ref_vehicle_condition":
            name = row.get("condition_name")
            if name:
                vehicle_conditions.append((name,))
        elif table == "ref_vehicle_make":
            name = row.get("make_name")
            if name:
                vehicle_makes.append((name,))
        elif table == "ref_nuisance_category":
            name = row.get("category_name")
            if name:
                nuisance_categories.append((name,))
        elif table == "ref_nuisance_item":
            category_name = row.get("category_name")
            item_name = row.get("item_name")
            if category_name and item_name:
                nuisance_items.append((category_name, item_name))
        elif table == "ref_email_template":
            template_key = row.get("template_key")
            subject = row.get("subject")
            body_text = row.get("body_text")
            if template_key and subject and body_text:
                email_templates.append((template_key, subject, body_text))
        elif table == "ref_user_submitted_vehicle_model_status":
            status_key = row.get("status_key")
            status_label = row.get("status_label")
            if status_key and status_label:
                user_submitted_vehicle_model_statuses.append(
                    (status_key, status_label)
                )

    def _unique_single_col(rows):
        seen = set()
        out = []
        for (v,) in rows:
            if v in seen:
                continue
            seen.add(v)
            out.append((v,))
        return out

    vehicle_colors = _unique_single_col(vehicle_colors)
    vehicle_types = _unique_single_col(vehicle_types)
    vehicle_conditions = _unique_single_col(vehicle_conditions)
    vehicle_makes = _unique_single_col(vehicle_makes)
    nuisance_categories = _unique_single_col(nuisance_categories)

    with output_sql.open("w", encoding="utf-8", newline="\n") as out:
        out.write("SET NAMES utf8mb4;\n")
        out.write("SET FOREIGN_KEY_CHECKS=0;\n")
        out.write("START TRANSACTION;\n\n")

        if args.drop_first:
            out.write("DROP TABLE IF EXISTS ref_import_manifest;\n")
            out.write("DROP TABLE IF EXISTS ref_email_template;\n")
            out.write(
                "DROP TABLE IF EXISTS "
                "ref_user_submitted_vehicle_model_status;\n"
            )
            out.write("DROP TABLE IF EXISTS ref_nuisance_item;\n")
            out.write("DROP TABLE IF EXISTS ref_nuisance_category;\n")
            out.write("DROP TABLE IF EXISTS ref_vehicle_make;\n")
            out.write("DROP TABLE IF EXISTS ref_vehicle_condition;\n")
            out.write("DROP TABLE IF EXISTS ref_vehicle_type;\n")
            out.write("DROP TABLE IF EXISTS ref_vehicle_color;\n")
            out.write("DROP TABLE IF EXISTS ref_zip_city;\n")
            out.write("DROP TABLE IF EXISTS ref_reference_table;\n\n")

        out.write(
            "CREATE TABLE IF NOT EXISTS ref_reference_table (\n"
            "  ref_table_id INT NOT NULL AUTO_INCREMENT,\n"
            "  table_name VARCHAR(128) NOT NULL,\n"
            "  key_fields_json JSON NOT NULL,\n"
            "  upsert_mode VARCHAR(32) NOT NULL,\n"
            "  PRIMARY KEY (ref_table_id),\n"
            "  UNIQUE KEY uk_ref_reference_table_name (table_name)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 "
            "COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        out.write(
            "CREATE TABLE IF NOT EXISTS ref_vehicle_color (\n"
            "  color_id INT NOT NULL AUTO_INCREMENT,\n"
            "  color_name VARCHAR(128) NOT NULL,\n"
            "  PRIMARY KEY (color_id),\n"
            "  UNIQUE KEY uk_ref_vehicle_color_name (color_name)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 "
            "COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        out.write(
            "CREATE TABLE IF NOT EXISTS ref_vehicle_type (\n"
            "  type_id INT NOT NULL AUTO_INCREMENT,\n"
            "  type_name VARCHAR(128) NOT NULL,\n"
            "  PRIMARY KEY (type_id),\n"
            "  UNIQUE KEY uk_ref_vehicle_type_name (type_name)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 "
            "COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        out.write(
            "CREATE TABLE IF NOT EXISTS ref_vehicle_condition (\n"
            "  condition_id INT NOT NULL AUTO_INCREMENT,\n"
            "  condition_name VARCHAR(255) NOT NULL,\n"
            "  PRIMARY KEY (condition_id),\n"
            "  UNIQUE KEY uk_ref_vehicle_condition_name (condition_name)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 "
            "COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        out.write(
            "CREATE TABLE IF NOT EXISTS ref_vehicle_make (\n"
            "  make_id INT NOT NULL AUTO_INCREMENT,\n"
            "  make_name VARCHAR(128) NOT NULL,\n"
            "  PRIMARY KEY (make_id),\n"
            "  UNIQUE KEY uk_ref_vehicle_make_name (make_name)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 "
            "COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        out.write(
            "CREATE TABLE IF NOT EXISTS ref_nuisance_category (\n"
            "  category_id INT NOT NULL AUTO_INCREMENT,\n"
            "  category_name VARCHAR(255) NOT NULL,\n"
            "  PRIMARY KEY (category_id),\n"
            "  UNIQUE KEY uk_ref_nuisance_category_name (category_name)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 "
            "COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        out.write(
            "CREATE TABLE IF NOT EXISTS ref_nuisance_item (\n"
            "  item_id INT NOT NULL AUTO_INCREMENT,\n"
            "  category_id INT NOT NULL,\n"
            "  item_name VARCHAR(255) NOT NULL,\n"
            "  PRIMARY KEY (item_id),\n"
            "  UNIQUE KEY uk_ref_nuisance_item (category_id, item_name),\n"
            "  KEY idx_ref_nuisance_item_name (item_name),\n"
            "  CONSTRAINT fk_ref_nuisance_item_category "
            "FOREIGN KEY (category_id)\n"
            "    REFERENCES ref_nuisance_category(category_id)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 "
            "COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        out.write(
            "CREATE TABLE IF NOT EXISTS ref_zip_city (\n"
            "  zip5 CHAR(5) NOT NULL,\n"
            "  city VARCHAR(128) NOT NULL,\n"
            "  state CHAR(2) NOT NULL,\n"
            "  PRIMARY KEY (zip5, city, state),\n"
            "  KEY idx_ref_zip_city_zip5 (zip5),\n"
            "  KEY idx_ref_zip_city_state_city (state, city)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 "
            "COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        out.write(
            "CREATE TABLE IF NOT EXISTS "
            "ref_email_template (\n"
            "  template_id INT NOT NULL AUTO_INCREMENT,\n"
            "  template_key VARCHAR(128) NOT NULL,\n"
            "  subject VARCHAR(255) NOT NULL,\n"
            "  body_text TEXT NOT NULL,\n"
            "  PRIMARY KEY (template_id),\n"
            "  UNIQUE KEY uk_ref_email_template_key (template_key)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 "
            "COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        out.write(
            "CREATE TABLE IF NOT EXISTS "
            "ref_user_submitted_vehicle_model_status (\n"
            "  status_id INT NOT NULL AUTO_INCREMENT,\n"
            "  status_key VARCHAR(64) NOT NULL,\n"
            "  status_label VARCHAR(255) NOT NULL,\n"
            "  PRIMARY KEY (status_id),\n"
            "  UNIQUE KEY uk_ref_user_vehicle_model_status_key (status_key)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 "
            "COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        out.write(
            "CREATE TABLE IF NOT EXISTS ref_import_manifest (\n"
            "  import_manifest_id INT NOT NULL AUTO_INCREMENT,\n"
            "  import_key VARCHAR(128) NOT NULL,\n"
            "  priority INT NULL,\n"
            "  source_name VARCHAR(255) NULL,\n"
            "  source_url VARCHAR(2048) NULL,\n"
            "  licensing_note TEXT NULL,\n"
            "  installer_behavior TEXT NULL,\n"
            "  tables_target_json JSON NOT NULL,\n"
            "  references_json JSON NOT NULL,\n"
            "  PRIMARY KEY (import_manifest_id),\n"
            "  UNIQUE KEY uk_ref_import_manifest_key (import_key)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 "
            "COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        def write_upsert_values(table, columns, rows, update_cols=None):
            if not rows:
                return

            if update_cols is None:
                update_cols = list(columns)

            updates = ", ".join(f"{c}=VALUES({c})" for c in update_cols)

            for batch in _batched(rows, args.batch_size):
                out.write(
                    f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n"
                )
                values_sql = ",\n".join(
                    "(" + ", ".join(_sql_quote(v) for v in row) + ")"
                    for row in batch
                )
                out.write(values_sql)
                out.write(f"\nON DUPLICATE KEY UPDATE {updates};\n\n")

        write_upsert_values(
            "ref_reference_table",
            ["table_name", "key_fields_json", "upsert_mode"],
            ref_tables,
            update_cols=["key_fields_json", "upsert_mode"],
        )
        write_upsert_values(
            "ref_vehicle_color",
            ["color_name"],
            vehicle_colors,
            update_cols=["color_name"],
        )
        write_upsert_values(
            "ref_vehicle_type",
            ["type_name"],
            vehicle_types,
            update_cols=["type_name"],
        )
        write_upsert_values(
            "ref_vehicle_condition",
            ["condition_name"],
            vehicle_conditions,
            update_cols=["condition_name"],
        )
        write_upsert_values(
            "ref_vehicle_make",
            ["make_name"],
            vehicle_makes,
            update_cols=["make_name"],
        )
        write_upsert_values(
            "ref_nuisance_category",
            ["category_name"],
            nuisance_categories,
            update_cols=["category_name"],
        )

        if nuisance_items:
            for batch in _batched(nuisance_items, args.batch_size):
                selects = []
                for category_name, item_name in batch:
                    selects.append(
                        "SELECT category_id, "
                        f"{_sql_quote(item_name)} AS item_name "
                        "FROM ref_nuisance_category WHERE category_name="
                        f"{_sql_quote(category_name)}"
                    )

                out.write(
                    "INSERT INTO ref_nuisance_item (category_id, item_name)\n"
                )
                out.write("\nUNION ALL\n".join(selects))
                out.write(
                    "\nON DUPLICATE KEY UPDATE "
                    "item_name=item_name;\n\n"
                )

        write_upsert_values(
            "ref_user_submitted_vehicle_model_status",
            ["status_key", "status_label"],
            user_submitted_vehicle_model_statuses,
            update_cols=["status_label"],
        )

        write_upsert_values(
            "ref_email_template",
            ["template_key", "subject", "body_text"],
            email_templates,
            update_cols=["subject", "body_text"],
        )

        write_upsert_values(
            "ref_import_manifest",
            [
                "import_key",
                "priority",
                "source_name",
                "source_url",
                "licensing_note",
                "installer_behavior",
                "tables_target_json",
                "references_json",
            ],
            import_manifests,
            update_cols=[
                "priority",
                "source_name",
                "source_url",
                "licensing_note",
                "installer_behavior",
                "tables_target_json",
                "references_json",
            ],
        )

        out.write("COMMIT;\n")
        out.write("SET FOREIGN_KEY_CHECKS=1;\n")

    print(f"Wrote SQL: {output_sql}")
    print(f"Reference tables: {len(ref_tables)}")
    print(f"Vehicle colors: {len(vehicle_colors)}")
    print(f"Vehicle types: {len(vehicle_types)}")
    print(f"Vehicle conditions: {len(vehicle_conditions)}")
    print(f"Vehicle makes: {len(vehicle_makes)}")
    print(f"Nuisance categories: {len(nuisance_categories)}")
    print(f"Nuisance items: {len(nuisance_items)}")
    print(f"Email templates: {len(email_templates)}")
    print(
        "User submitted vehicle model statuses: "
        f"{len(user_submitted_vehicle_model_statuses)}"
    )
    print(f"Import manifests: {len(import_manifests)}")


if __name__ == "__main__":
    main()
