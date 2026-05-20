import os
import psycopg2
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
        dbname=os.getenv("POSTGRES_DB", "macrolens"),
        user=os.getenv("POSTGRES_USER", os.environ.get("USER")),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )


def log_result(conn, table_name: str, check_name: str, status: str, message: str):
    """Write a validation result to the validation_log table."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO validation_log (table_name, check_name, status, message, checked_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (table_name, check_name, status, message, datetime.now(timezone.utc)))
    conn.commit()


def check_row_count(conn, table_name: str, min_rows: int = 1) -> bool:
    """Fail if table has fewer rows than expected."""
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cur.fetchone()[0]

    status = "PASS" if count >= min_rows else "FAIL"
    message = f"Row count: {count} (min expected: {min_rows})"
    log_result(conn, table_name, "row_count", status, message)
    print(f"[{status}] {table_name} row_count — {message}")
    return status == "PASS"


def check_nulls(conn, table_name: str, column: str) -> bool:
    """Fail if any nulls exist in a critical column."""
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {column} IS NULL;")
        null_count = cur.fetchone()[0]

    status = "PASS" if null_count == 0 else "FAIL"
    message = f"Null count in {column}: {null_count}"
    log_result(conn, table_name, f"null_check_{column}", status, message)
    print(f"[{status}] {table_name} null_check_{column} — {message}")
    return status == "PASS"


def check_value_range(conn, table_name: str, column: str, min_val: float, max_val: float) -> bool:
    """Warn if values fall outside expected range."""
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT COUNT(*) FROM {table_name}
            WHERE {column} < %s OR {column} > %s;
        """, (min_val, max_val))
        out_of_range = cur.fetchone()[0]

    status = "PASS" if out_of_range == 0 else "WARN"
    message = f"Out-of-range values in {column}: {out_of_range} (expected {min_val}–{max_val})"
    log_result(conn, table_name, f"range_check_{column}", status, message)
    print(f"[{status}] {table_name} range_check_{column} — {message}")
    return status != "FAIL"


def run_all_validations() -> bool:
    """Run all validation checks. Returns True if no FAILs."""
    conn = get_connection()
    all_passed = True

    print("\n--- Validating raw_macro_indicators ---")
    all_passed &= check_row_count(conn, "raw_macro_indicators", min_rows=100)
    all_passed &= check_nulls(conn, "raw_macro_indicators", "value")
    all_passed &= check_nulls(conn, "raw_macro_indicators", "date")
    all_passed &= check_value_range(conn, "raw_macro_indicators", "value", -50, 50000)

    print("\n--- Validating raw_sector_prices ---")
    all_passed &= check_row_count(conn, "raw_sector_prices", min_rows=0)
    all_passed &= check_nulls(conn, "raw_sector_prices", "close")
    all_passed &= check_nulls(conn, "raw_sector_prices", "date")

    conn.close()

    print(f"\n{'All validations passed.' if all_passed else 'Some validations FAILED — check validation_log.'}")
    return all_passed


if __name__ == "__main__":
    run_all_validations()