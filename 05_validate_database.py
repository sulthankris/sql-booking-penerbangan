"""Validate the generated SQLite database."""

from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("flight-booking.db")
TABLES = ("airports", "airlines", "planes", "flights", "customers", "bookings")


def fail(message: str) -> None:
    raise SystemExit(f"Validation failed: {message}")


def expect_zero(conn: sqlite3.Connection, sql: str, message: str) -> None:
    value = conn.execute(sql).fetchone()[0]
    if value != 0:
        fail(f"{message}: {value}")


def main() -> None:
    if not DB_PATH.exists():
        fail(f"missing database file {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    foreign_key_issues = conn.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_key_issues:
        fail(f"foreign key issues found: {foreign_key_issues}")

    expect_zero(
        conn,
        """
        SELECT COUNT(*)
        FROM airports
        WHERE airport_code IS NULL OR TRIM(airport_code) = '' OR airport_code = '\\N'
        """,
        "invalid airport primary keys",
    )
    expect_zero(
        conn,
        """
        SELECT COUNT(*)
        FROM airlines
        WHERE airline_code IS NULL OR TRIM(airline_code) = '' OR airline_code = '\\N'
        """,
        "invalid airline primary keys",
    )
    expect_zero(
        conn,
        """
        SELECT COUNT(*)
        FROM flights
        WHERE origin_airport_code = dest_airport_code
        """,
        "flights with same origin and destination",
    )
    expect_zero(
        conn,
        """
        SELECT COUNT(*)
        FROM (
            SELECT airline_code, flight_code, seat_number, COUNT(*) AS duplicate_count
            FROM bookings
            GROUP BY airline_code, flight_code, seat_number
            HAVING duplicate_count > 1
        )
        """,
        "duplicate booked seats on the same flight",
    )

    print("Table counts:")
    for table in TABLES:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"- {table}: {count}")

    print("Sample analytical checks:")
    top_routes = conn.execute(
        """
        SELECT
            f.origin_airport_code,
            f.dest_airport_code,
            COUNT(b.booking_id) AS booking_count
        FROM bookings AS b
        JOIN flights AS f
            ON b.airline_code = f.airline_code
            AND b.flight_code = f.flight_code
        GROUP BY f.origin_airport_code, f.dest_airport_code
        ORDER BY booking_count DESC
        LIMIT 5
        """
    ).fetchall()
    print("- top routes by bookings:", top_routes)

    avg_price_by_airline = conn.execute(
        """
        SELECT airline_code, ROUND(AVG(price), 0) AS avg_price
        FROM flights
        GROUP BY airline_code
        ORDER BY avg_price DESC
        """
    ).fetchall()
    print("- average price by airline:", avg_price_by_airline)

    conn.close()
    print("Validation passed.")


if __name__ == "__main__":
    main()
