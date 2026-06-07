"""Prepare clean Indonesian airport, airline, and route CSV files.

Outputs:
- filtered/airports.csv
- filtered/airlines.csv
- filtered/routes.csv

The output columns already match the final database naming convention.
"""

from __future__ import annotations

import csv
from pathlib import Path


RAW_DIR = Path("raw_data")
FILTERED_DIR = Path("filtered")

AIRPORTS_FILE = RAW_DIR / "airports.dat"
AIRLINES_FILE = RAW_DIR / "airlines.dat"
ROUTES_FILE = RAW_DIR / "routes.dat"

# Keep airlines that have useful Indonesian domestic route data in OpenFlights.
# Names are fixed here so manually enriched airlines have consistent labels.
TARGET_AIRLINES = {
    "GA": "Garuda Indonesia",
    "JT": "Lion Air",
    "QG": "Citilink",
    "ID": "Batik Air",
    "QZ": "Indonesia AirAsia",
    "SJ": "Sriwijaya Air",
}


def is_valid_iata(value: str, length: int) -> bool:
    value = value.strip().upper()
    return len(value) == length and value != r"\N" and value.isalnum()


def read_openflights_csv(path: Path) -> list[list[str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing raw data file: {path}. Run 01_download.py first.")

    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.reader(file))


def write_csv(path: Path, header: list[str], rows: list[tuple]) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)


def prepare_airports() -> dict[str, tuple[str, str, str, float, float]]:
    airports: dict[str, tuple[str, str, str, float, float]] = {}

    for row in read_openflights_csv(AIRPORTS_FILE):
        if len(row) < 8:
            continue

        name = row[1].strip()
        city = row[2].strip()
        country = row[3].strip()
        airport_code = row[4].strip().upper()

        if country != "Indonesia" or not is_valid_iata(airport_code, 3):
            continue

        try:
            latitude = float(row[6])
            longitude = float(row[7])
        except ValueError:
            continue

        airports[airport_code] = (airport_code, name, city, latitude, longitude)

    return dict(sorted(airports.items()))


def prepare_routes(valid_airports: set[str]) -> list[tuple[str, str, str]]:
    seen_routes: set[tuple[str, str, str]] = set()

    for row in read_openflights_csv(ROUTES_FILE):
        if len(row) < 5:
            continue

        airline_code = row[0].strip().upper()
        origin_airport_code = row[2].strip().upper()
        dest_airport_code = row[4].strip().upper()

        if airline_code not in TARGET_AIRLINES:
            continue
        if origin_airport_code not in valid_airports:
            continue
        if dest_airport_code not in valid_airports:
            continue
        if origin_airport_code == dest_airport_code:
            continue

        seen_routes.add((airline_code, origin_airport_code, dest_airport_code))

    return sorted(seen_routes)


def prepare_airlines(routes: list[tuple[str, str, str]]) -> dict[str, tuple[str, str]]:
    route_airline_codes = {airline_code for airline_code, _, _ in routes}
    airlines = {
        airline_code: (airline_code, airline_name)
        for airline_code, airline_name in TARGET_AIRLINES.items()
        if airline_code in route_airline_codes
    }

    # Cross-check the raw file so obvious upstream naming differences are visible.
    raw_airline_codes = set()
    for row in read_openflights_csv(AIRLINES_FILE):
        if len(row) >= 4 and is_valid_iata(row[3], 2):
            raw_airline_codes.add(row[3].strip().upper())

    missing_from_raw = sorted(set(airlines) - raw_airline_codes)
    if missing_from_raw:
        print("Manual airline names used for:", ", ".join(missing_from_raw))

    return dict(sorted(airlines.items()))


def main() -> None:
    airports = prepare_airports()
    routes = prepare_routes(set(airports))
    airlines = prepare_airlines(routes)

    write_csv(
        FILTERED_DIR / "airports.csv",
        ["airport_code", "airport_name", "city", "latitude", "longitude"],
        list(airports.values()),
    )
    write_csv(
        FILTERED_DIR / "airlines.csv",
        ["airline_code", "airline_name"],
        list(airlines.values()),
    )
    write_csv(
        FILTERED_DIR / "routes.csv",
        ["airline_code", "origin_airport_code", "dest_airport_code"],
        routes,
    )

    print(f"Airports written: {len(airports)}")
    print(f"Airlines written: {len(airlines)}")
    print(f"Routes written: {len(routes)}")


if __name__ == "__main__":
    main()
