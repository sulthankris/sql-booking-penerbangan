"""Generate deterministic synthetic data for the final database.

Outputs:
- generated/planes.csv
- generated/flights.csv
- generated/customers.csv
- generated/bookings.csv

The random seed is fixed so the same input CSVs produce the same output CSVs.
"""

from __future__ import annotations

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path


SEED = 20260521
FILTERED_DIR = Path("filtered")
GENERATED_DIR = Path("generated")

BOOKING_COUNT = 900
CUSTOMER_COUNT = 300

AIRCRAFT_BY_AIRLINE = {
    "GA": [("Boeing 737-800", 162), ("Airbus A330-300", 287), ("Boeing 777-300ER", 314)],
    "JT": [("Boeing 737-800", 189), ("Boeing 737-900ER", 215)],
    "QG": [("Airbus A320-200", 180), ("Airbus A320neo", 180)],
    "ID": [("Boeing 737-800", 162), ("Airbus A320-200", 156)],
    "QZ": [("Airbus A320-200", 180), ("Airbus A320neo", 186)],
    "SJ": [("Boeing 737-800", 189), ("Boeing 737-500", 120)],
}

PLANE_COUNTS = {
    "GA": 15,
    "JT": 18,
    "QG": 12,
    "ID": 10,
    "QZ": 8,
    "SJ": 8,
}

TAIL_PREFIX = {
    "GA": "G",
    "JT": "L",
    "QG": "C",
    "ID": "B",
    "QZ": "A",
    "SJ": "S",
}

FIRST_NAMES = [
    "Adi",
    "Agus",
    "Andi",
    "Ayu",
    "Budi",
    "Citra",
    "Dewi",
    "Dian",
    "Eka",
    "Eko",
    "Farah",
    "Fitri",
    "Hana",
    "Indra",
    "Intan",
    "Joko",
    "Lina",
    "Made",
    "Nadia",
    "Putri",
    "Rizky",
    "Sari",
    "Teguh",
    "Wahyu",
]

LAST_NAMES = [
    "Ananda",
    "Hartono",
    "Hidayat",
    "Kusuma",
    "Lestari",
    "Nugroho",
    "Pratama",
    "Pratiwi",
    "Saputra",
    "Sari",
    "Setiawan",
    "Susanto",
    "Utami",
    "Wahyuni",
    "Wijaya",
]


def read_dicts(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing input CSV: {path}. Run the previous script first.")

    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def write_dicts(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    value = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * radius_km * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def generate_tail_number(airline_code: str, index: int) -> str:
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    prefix = TAIL_PREFIX.get(airline_code, airline_code[0])
    first_suffix = letters[index // len(letters)]
    second_suffix = letters[index % len(letters)]
    return f"PK-{prefix}{first_suffix}{second_suffix}"


def generate_planes(airline_codes: list[str], rng: random.Random) -> list[dict[str, object]]:
    planes: list[dict[str, object]] = []

    for airline_code in airline_codes:
        aircraft_options = AIRCRAFT_BY_AIRLINE.get(airline_code, [("Boeing 737-800", 180)])
        plane_count = PLANE_COUNTS.get(airline_code, 6)

        for index in range(plane_count):
            aircraft_type, total_seats = rng.choice(aircraft_options)
            planes.append(
                {
                    "tail_number": generate_tail_number(airline_code, index),
                    "aircraft_type": aircraft_type,
                    "total_seats": total_seats,
                    "owner_airline": airline_code,
                }
            )

    return planes


def generate_flights(
    routes: list[dict[str, str]],
    airports: dict[str, dict[str, str]],
    planes: list[dict[str, object]],
    rng: random.Random,
) -> list[dict[str, object]]:
    tails_by_airline: dict[str, list[str]] = {}
    for plane in planes:
        tails_by_airline.setdefault(str(plane["owner_airline"]), []).append(str(plane["tail_number"]))

    flight_counter: dict[str, int] = {}
    flights: list[dict[str, object]] = []

    for route in routes:
        airline_code = route["airline_code"]
        origin_code = route["origin_airport_code"]
        dest_code = route["dest_airport_code"]

        origin = airports[origin_code]
        dest = airports[dest_code]
        distance_km = haversine_km(
            float(origin["latitude"]),
            float(origin["longitude"]),
            float(dest["latitude"]),
            float(dest["longitude"]),
        )

        flight_counter[airline_code] = flight_counter.get(airline_code, 1000) + 1
        price = 350_000 + distance_km * 1_150 + rng.randint(-75_000, 175_000)
        price = max(350_000, min(2_750_000, price))
        price = round(price / 1000) * 1000

        flights.append(
            {
                "airline_code": airline_code,
                "flight_code": str(flight_counter[airline_code]),
                "origin_airport_code": origin_code,
                "dest_airport_code": dest_code,
                "tail_number": rng.choice(tails_by_airline[airline_code]),
                "price": int(price),
            }
        )

    return flights


def generate_customers(rng: random.Random) -> list[dict[str, object]]:
    customers: list[dict[str, object]] = []

    for customer_id in range(1, CUSTOMER_COUNT + 1):
        first_name = rng.choice(FIRST_NAMES)
        last_name = rng.choice(LAST_NAMES)
        email = f"{first_name.lower()}.{last_name.lower()}{customer_id:03d}@example.com"
        phone = f"08{rng.randint(1000000000, 9999999999)}"

        customers.append(
            {
                "customer_id": customer_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "password": "pass123",
            }
        )

    return customers


def build_seat_pool(total_seats: int) -> list[str]:
    seat_letters = "ABCDEF"
    row_count = math.ceil(total_seats / len(seat_letters))
    seats = [f"{row}{letter}" for row in range(1, row_count + 1) for letter in seat_letters]
    return seats[:total_seats]


def generate_bookings(
    flights: list[dict[str, object]],
    planes: list[dict[str, object]],
    customer_count: int,
    rng: random.Random,
) -> list[dict[str, object]]:
    seats_by_tail = {
        str(plane["tail_number"]): build_seat_pool(int(plane["total_seats"]))
        for plane in planes
    }
    available_seats_by_flight = {
        (str(flight["airline_code"]), str(flight["flight_code"])): seats_by_tail[str(flight["tail_number"])].copy()
        for flight in flights
    }

    start_date = date(2026, 1, 1)
    end_date = date(2026, 5, 21)
    day_span = (end_date - start_date).days

    bookings: list[dict[str, object]] = []
    selectable_flights = flights.copy()

    for booking_id in range(1, BOOKING_COUNT + 1):
        flight = rng.choice(selectable_flights)
        flight_key = (str(flight["airline_code"]), str(flight["flight_code"]))
        seat_pool = available_seats_by_flight[flight_key]

        seat_number = rng.choice(seat_pool)
        seat_pool.remove(seat_number)
        if not seat_pool:
            selectable_flights = [
                item
                for item in selectable_flights
                if (str(item["airline_code"]), str(item["flight_code"])) != flight_key
            ]

        bookings.append(
            {
                "booking_id": booking_id,
                "airline_code": flight_key[0],
                "flight_code": flight_key[1],
                "seat_number": seat_number,
                "customer_id": rng.randint(1, customer_count),
                "transaction_date": (start_date + timedelta(days=rng.randint(0, day_span))).isoformat(),
            }
        )

    return bookings


def main() -> None:
    rng = random.Random(SEED)

    airport_rows = read_dicts(FILTERED_DIR / "airports.csv")
    airline_rows = read_dicts(FILTERED_DIR / "airlines.csv")
    route_rows = read_dicts(FILTERED_DIR / "routes.csv")

    airports = {row["airport_code"]: row for row in airport_rows}
    airline_codes = [row["airline_code"] for row in airline_rows]

    planes = generate_planes(airline_codes, rng)
    flights = generate_flights(route_rows, airports, planes, rng)
    customers = generate_customers(rng)
    bookings = generate_bookings(flights, planes, len(customers), rng)

    write_dicts(
        GENERATED_DIR / "planes.csv",
        ["tail_number", "aircraft_type", "total_seats", "owner_airline"],
        planes,
    )
    write_dicts(
        GENERATED_DIR / "flights.csv",
        [
            "airline_code",
            "flight_code",
            "origin_airport_code",
            "dest_airport_code",
            "tail_number",
            "price",
        ],
        flights,
    )
    write_dicts(
        GENERATED_DIR / "customers.csv",
        ["customer_id", "first_name", "last_name", "email", "phone", "password"],
        customers,
    )
    write_dicts(
        GENERATED_DIR / "bookings.csv",
        [
            "booking_id",
            "airline_code",
            "flight_code",
            "seat_number",
            "customer_id",
            "transaction_date",
        ],
        bookings,
    )

    print(f"Random seed: {SEED}")
    print(f"Planes written: {len(planes)}")
    print(f"Flights written: {len(flights)}")
    print(f"Customers written: {len(customers)}")
    print(f"Bookings written: {len(bookings)}")


if __name__ == "__main__":
    main()
