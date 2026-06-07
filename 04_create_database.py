"""Create the final SQLite database for the flight booking project."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


DB_PATH = Path("flight-booking.db")
FILTERED_DIR = Path("filtered")
GENERATED_DIR = Path("generated")


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE airports (
    airport_code TEXT(3) PRIMARY KEY,
    airport_name TEXT NOT NULL,
    city TEXT,
    latitude REAL,
    longitude REAL
);

CREATE TABLE airlines (
    airline_code TEXT(2) PRIMARY KEY,
    airline_name TEXT NOT NULL
);

CREATE TABLE planes (
    tail_number TEXT(6) PRIMARY KEY,
    aircraft_type TEXT NOT NULL,
    total_seats INTEGER NOT NULL CHECK (total_seats > 0),
    owner_airline TEXT(2) NOT NULL,
    FOREIGN KEY (owner_airline) REFERENCES airlines(airline_code)
);

CREATE TABLE flights (
    airline_code TEXT(2) NOT NULL,
    flight_code TEXT(4) NOT NULL,
    origin_airport_code TEXT(3) NOT NULL,
    dest_airport_code TEXT(3) NOT NULL,
    tail_number TEXT(6) NOT NULL,
    price REAL NOT NULL CHECK (price >= 0),
    PRIMARY KEY (airline_code, flight_code),
    FOREIGN KEY (airline_code) REFERENCES airlines(airline_code),
    FOREIGN KEY (origin_airport_code) REFERENCES airports(airport_code),
    FOREIGN KEY (dest_airport_code) REFERENCES airports(airport_code),
    FOREIGN KEY (tail_number) REFERENCES planes(tail_number),
    CHECK (origin_airport_code <> dest_airport_code)
);

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    password TEXT
);

CREATE TABLE bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airline_code TEXT(2) NOT NULL,
    flight_code TEXT(4) NOT NULL,
    seat_number TEXT(4) NOT NULL,
    customer_id INTEGER NOT NULL,
    transaction_date DATE NOT NULL,
    FOREIGN KEY (airline_code, flight_code)
        REFERENCES flights(airline_code, flight_code),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    UNIQUE (airline_code, flight_code, seat_number)
);

CREATE INDEX idx_flights_route
    ON flights(origin_airport_code, dest_airport_code);

CREATE INDEX idx_bookings_customer
    ON bookings(customer_id);

"""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing input CSV: {path}. Run the previous scripts first.")

    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def insert_rows(
    conn: sqlite3.Connection,
    table: str,
    columns: list[str],
    rows: list[dict[str, str]],
) -> None:
    placeholders = ", ".join("?" for _ in columns)
    column_sql = ", ".join(columns)
    sql = f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})"
    conn.executemany(sql, ([row[column] for column in columns] for row in rows))


def create_database() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.executescript(
        """
        DROP TABLE IF EXISTS bookings;
        DROP TABLE IF EXISTS flights;
        DROP TABLE IF EXISTS planes;
        DROP TABLE IF EXISTS customers;
        DROP TABLE IF EXISTS airlines;
        DROP TABLE IF EXISTS airports;
        """
    )
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_SQL)

    insert_rows(
        conn,
        "airports",
        ["airport_code", "airport_name", "city", "latitude", "longitude"],
        read_csv(FILTERED_DIR / "airports.csv"),
    )
    insert_rows(
        conn,
        "airlines",
        ["airline_code", "airline_name"],
        read_csv(FILTERED_DIR / "airlines.csv"),
    )
    insert_rows(
        conn,
        "planes",
        ["tail_number", "aircraft_type", "total_seats", "owner_airline"],
        read_csv(GENERATED_DIR / "planes.csv"),
    )
    insert_rows(
        conn,
        "flights",
        [
            "airline_code",
            "flight_code",
            "origin_airport_code",
            "dest_airport_code",
            "tail_number",
            "price",
        ],
        read_csv(GENERATED_DIR / "flights.csv"),
    )
    insert_rows(
        conn,
        "customers",
        ["customer_id", "first_name", "last_name", "email", "phone", "password"],
        read_csv(GENERATED_DIR / "customers.csv"),
    )
    insert_rows(
        conn,
        "bookings",
        [
            "booking_id",
            "airline_code",
            "flight_code",
            "seat_number",
            "customer_id",
            "transaction_date",
        ],
        read_csv(GENERATED_DIR / "bookings.csv"),
    )

    conn.commit()

    for table in ("airports", "airlines", "planes", "flights", "customers", "bookings"):
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count}")

    conn.close()
    print(f"Database created: {DB_PATH}")


if __name__ == "__main__":
    create_database()
