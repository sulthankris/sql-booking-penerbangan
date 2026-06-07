from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st


DB_PATH = Path(__file__).with_name("flight-booking.db")
MAP_STYLE = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
TABLES = ["airports", "airlines", "planes", "flights", "customers", "bookings"]
DATABASE_PAGE_SIZE = 25
ADD_BOOKING_PANEL_HEIGHT = 690

TABLE_METADATA = {
    "airports": {
        "description": "Data master bandara Indonesia.",
        "primary_key": "airport_code",
        "foreign_keys": [],
        "constraints": ["airport_code dan airport_name wajib diisi"],
    },
    "airlines": {
        "description": "Data master maskapai penerbangan.",
        "primary_key": "airline_code",
        "foreign_keys": [],
        "constraints": ["airline_code dan airline_name wajib diisi"],
    },
    "planes": {
        "description": "Data pesawat yang dimiliki atau dioperasikan oleh maskapai.",
        "primary_key": "tail_number",
        "foreign_keys": ["owner_airline -> airlines.airline_code"],
        "constraints": ["total_seats > 0"],
    },
    "flights": {
        "description": "Entri katalog rute dengan maskapai, pesawat, dan harga.",
        "primary_key": "airline_code + flight_code",
        "foreign_keys": [
            "airline_code -> airlines.airline_code",
            "origin_airport_code -> airports.airport_code",
            "dest_airport_code -> airports.airport_code",
            "tail_number -> planes.tail_number",
        ],
        "constraints": ["origin_airport_code <> dest_airport_code", "price >= 0"],
    },
    "customers": {
        "description": "Akun pelanggan sintetis yang digunakan untuk simulasi pemesanan.",
        "primary_key": "customer_id",
        "foreign_keys": [],
        "constraints": ["email bersifat unik", "first_name, last_name, dan email wajib diisi"],
    },
    "bookings": {
        "description": "Transaksi pemesanan tiket.",
        "primary_key": "booking_id",
        "foreign_keys": [
            "customer_id -> customers.customer_id",
            "airline_code + flight_code -> flights.airline_code + flights.flight_code",
        ],
        "constraints": ["UNIQUE(airline_code, flight_code, seat_number)", "transaction_date wajib diisi"],
    },
}

INSERT_CONSTRAINTS = {
    "airlines": [
        "airline_code adalah primary key dan harus unik.",
        "airline_code dan airline_name wajib diisi.",
    ],
    "airports": [
        "airport_code adalah primary key dan harus unik.",
        "airport_code dan airport_name wajib diisi.",
        "latitude dan longitude harus berupa angka.",
    ],
    "planes": [
        "tail_number adalah primary key dan harus unik.",
        "owner_airline harus ada di airlines.airline_code.",
        "total_seats harus lebih dari 0.",
    ],
    "flights": [
        "airline_code + flight_code adalah composite primary key.",
        "airline_code, origin_airport_code, dest_airport_code, dan tail_number harus sudah ada.",
        "origin_airport_code dan dest_airport_code tidak boleh sama.",
        "price harus 0 atau lebih.",
        "tail_number harus milik airline_code yang dipilih.",
    ],
}

PREDEFINED_QUERIES = {
    "1. Penerbangan dari CGK ke DPS": {
        "description": "SELECT dengan WHERE dan ORDER BY untuk rute tertentu.",
        "sql": """
            SELECT
                f.airline_code,
                a.airline_name,
                f.flight_code,
                f.origin_airport_code,
                f.dest_airport_code,
                f.tail_number,
                p.aircraft_type,
                f.price
            FROM flights AS f
            JOIN airlines AS a ON f.airline_code = a.airline_code
            JOIN planes AS p ON f.tail_number = p.tail_number
            WHERE f.origin_airport_code = 'CGK'
              AND f.dest_airport_code = 'DPS'
            ORDER BY f.price ASC
        """,
    },
    "2. Riwayat pemesanan pelanggan": {
        "description": "JOIN bookings, customers, dan flights untuk menampilkan riwayat pemesanan.",
        "sql": """
            SELECT
                b.booking_id,
                c.customer_id,
                c.first_name || ' ' || c.last_name AS customer_name,
                b.transaction_date,
                b.airline_code,
                b.flight_code,
                f.origin_airport_code,
                f.dest_airport_code,
                b.seat_number
            FROM bookings AS b
            JOIN customers AS c ON b.customer_id = c.customer_id
            JOIN flights AS f
                ON b.airline_code = f.airline_code
                AND b.flight_code = f.flight_code
            ORDER BY b.transaction_date DESC, b.booking_id DESC
            LIMIT 100
        """,
    },
    "3. Jumlah pemesanan per maskapai": {
        "description": "GROUP BY maskapai dengan agregat COUNT.",
        "sql": """
            SELECT
                a.airline_code,
                a.airline_name,
                COUNT(b.booking_id) AS booking_count
            FROM airlines AS a
            LEFT JOIN bookings AS b ON a.airline_code = b.airline_code
            GROUP BY a.airline_code, a.airline_name
            ORDER BY booking_count DESC
        """,
    },
    "4. Jumlah pemesanan per rute": {
        "description": "GROUP BY rute untuk menemukan pasangan asal-tujuan yang populer.",
        "sql": """
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
            LIMIT 20
        """,
    },
    "5. Harga rata-rata per rute": {
        "description": "GROUP BY rute dengan agregat AVG, MIN, dan MAX.",
        "sql": """
            SELECT
                origin_airport_code,
                dest_airport_code,
                COUNT(*) AS flight_count,
                ROUND(AVG(price), 0) AS average_price,
                MIN(price) AS cheapest_price,
                MAX(price) AS highest_price
            FROM flights
            GROUP BY origin_airport_code, dest_airport_code
            ORDER BY average_price DESC
            LIMIT 20
        """,
    },
    "6. Penerbangan paling mahal": {
        "description": "ORDER BY harga menurun.",
        "sql": """
            SELECT
                f.airline_code,
                a.airline_name,
                f.flight_code,
                f.origin_airport_code,
                f.dest_airport_code,
                f.price
            FROM flights AS f
            JOIN airlines AS a ON f.airline_code = a.airline_code
            ORDER BY f.price DESC
            LIMIT 20
        """,
    },
    "7. Penerbangan paling murah": {
        "description": "ORDER BY harga menaik.",
        "sql": """
            SELECT
                f.airline_code,
                a.airline_name,
                f.flight_code,
                f.origin_airport_code,
                f.dest_airport_code,
                f.price
            FROM flights AS f
            JOIN airlines AS a ON f.airline_code = a.airline_code
            ORDER BY f.price ASC
            LIMIT 20
        """,
    },
    "8. Pemesanan berdasarkan tanggal transaksi": {
        "description": "GROUP BY tanggal transaksi untuk analisis tren sederhana.",
        "sql": """
            SELECT
                transaction_date,
                COUNT(*) AS booking_count
            FROM bookings
            GROUP BY transaction_date
            ORDER BY transaction_date ASC
        """,
    },
}


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@st.cache_data(ttl=30)
def run_select(query: str, params: tuple = ()) -> pd.DataFrame:
    conn = get_connection()
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def execute_write(query: str, params: tuple = ()) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(query, params)
        conn.commit()
        return int(cursor.lastrowid)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def clear_query_cache() -> None:
    st.cache_data.clear()


def normalize_code(value: str) -> str:
    return value.strip().upper()


def format_rupiah(value: object) -> str:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return "Rp 0"
    return f"Rp {amount:,.0f}".replace(",", ".")


def parse_optional_price(value: str) -> int | None:
    value = value.strip().replace(".", "").replace(",", "")
    if not value:
        return None
    if not value.isdigit():
        raise ValueError("Harga maksimum harus berupa angka, misalnya 1000000.")
    return int(value)


def table_count(table: str) -> int:
    return int(run_select(f"SELECT COUNT(*) AS total FROM {table}").iloc[0]["total"])


def filter_dataframe(df: pd.DataFrame, search_text: str) -> pd.DataFrame:
    if not search_text.strip() or df.empty:
        return df
    search_text = search_text.strip().lower()
    mask = df.astype(str).apply(
        lambda row: row.str.lower().str.contains(search_text, regex=False).any(),
        axis=1,
    )
    return df[mask]


def initialize_session_state() -> None:
    defaults = {
        "origin_airport_search": "Jakarta",
        "dest_airport_search": "Denpasar",
        "airline_search": "",
        "max_price_search": "",
        "customer_search_booking": "",
        "selected_ticket_key": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_data(ttl=30)
def search_airports(search_text: str) -> pd.DataFrame:
    term = search_text.strip().lower()
    if not term:
        return run_select(
            """
            SELECT airport_code, city, airport_name, latitude, longitude
            FROM airports
            ORDER BY airport_code
            """
        )

    pattern = f"%{term}%"
    return run_select(
        """
        SELECT airport_code, city, airport_name, latitude, longitude
        FROM airports
        WHERE LOWER(airport_code) LIKE ?
           OR LOWER(city) LIKE ?
           OR LOWER(airport_name) LIKE ?
        ORDER BY
            CASE
                WHEN LOWER(airport_code) = ? THEN 0
                WHEN LOWER(city) = ? THEN 1
                WHEN LOWER(airport_name) LIKE ? THEN 2
                ELSE 3
            END,
            city,
            airport_code
        """,
        (pattern, pattern, pattern, term, term, pattern),
    )


@st.cache_data(ttl=30)
def search_airlines(search_text: str) -> pd.DataFrame:
    term = search_text.strip().lower()
    if not term:
        return run_select(
            """
            SELECT airline_code, airline_name
            FROM airlines
            ORDER BY airline_code
            """
        )

    pattern = f"%{term}%"
    return run_select(
        """
        SELECT airline_code, airline_name
        FROM airlines
        WHERE LOWER(airline_code) LIKE ?
           OR LOWER(airline_name) LIKE ?
        ORDER BY airline_code
        """,
        (pattern, pattern),
    )


@st.cache_data(ttl=30)
def load_airport_map_data() -> pd.DataFrame:
    return run_select(
        """
        SELECT airport_code, airport_name, city, latitude, longitude
        FROM airports
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
        ORDER BY airport_code
        """
    )


@st.cache_data(ttl=30)
def load_flight_details(airline_code: str, flight_code: str) -> pd.DataFrame:
    return run_select(
        """
        SELECT
            f.airline_code,
            a.airline_name,
            f.flight_code,
            f.origin_airport_code,
            f.dest_airport_code,
            f.tail_number,
            p.aircraft_type,
            p.total_seats,
            f.price
        FROM flights AS f
        JOIN airlines AS a ON f.airline_code = a.airline_code
        JOIN planes AS p ON f.tail_number = p.tail_number
        WHERE f.airline_code = ?
          AND f.flight_code = ?
        """,
        (airline_code, flight_code),
    )


@st.cache_data(ttl=30)
def load_booked_seats(airline_code: str, flight_code: str) -> pd.DataFrame:
    return run_select(
        """
        SELECT seat_number
        FROM bookings
        WHERE airline_code = ?
          AND flight_code = ?
        ORDER BY seat_number
        """,
        (airline_code, flight_code),
    )


@st.cache_data(ttl=30)
def lookup_customer_by_email(email: str) -> pd.DataFrame:
    email = email.strip().lower()
    if not email:
        return pd.DataFrame()

    return run_select(
        """
        SELECT customer_id, first_name, last_name, email
        FROM customers
        WHERE LOWER(email) = ?
        """,
        (email,),
    )


@st.cache_data(ttl=30)
def search_customers(search_text: str) -> pd.DataFrame:
    term = search_text.strip().lower()
    if not term:
        return run_select(
            """
            SELECT customer_id, first_name, last_name, email
            FROM customers
            ORDER BY customer_id DESC
            LIMIT 30
            """
        )

    pattern = f"%{term}%"
    return run_select(
        """
        SELECT customer_id, first_name, last_name, email
        FROM customers
        WHERE CAST(customer_id AS TEXT) = ?
           OR LOWER(email) LIKE ?
           OR LOWER(first_name) LIKE ?
           OR LOWER(last_name) LIKE ?
           OR LOWER(first_name || ' ' || last_name) LIKE ?
        ORDER BY
            CASE
                WHEN LOWER(email) = ? THEN 0
                WHEN CAST(customer_id AS TEXT) = ? THEN 1
                ELSE 2
            END,
            customer_id DESC
        LIMIT 30
        """,
        (term, pattern, pattern, pattern, pattern, term, term),
    )


def value_exists(table: str, column: str, value: str) -> bool:
    allowed = {
        "airports": {"airport_code"},
        "airlines": {"airline_code"},
        "planes": {"tail_number"},
        "flights": {"airline_code", "flight_code"},
    }
    if table not in allowed or column not in allowed[table]:
        raise ValueError("Unsupported existence check")

    count = run_select(
        f"SELECT COUNT(*) AS total FROM {table} WHERE {column} = ?",
        (value,),
    ).iloc[0]["total"]
    return int(count) > 0


def build_seat_pool(total_seats: int) -> list[str]:
    seat_letters = "ABCDEF"
    seats = []
    row_number = 1
    while len(seats) < total_seats:
        for seat_letter in seat_letters:
            seats.append(f"{row_number}{seat_letter}")
            if len(seats) == total_seats:
                break
        row_number += 1
    return seats


def available_seats_for_flight(airline_code: str, flight_code: str) -> list[str]:
    flight = load_flight_details(airline_code, flight_code)
    if flight.empty:
        return []

    total_seats = int(flight.iloc[0]["total_seats"])
    booked = set(load_booked_seats(airline_code, flight_code)["seat_number"].tolist())
    return [seat for seat in build_seat_pool(total_seats) if seat not in booked]


def airport_options(search_text: str, label_when_all: str) -> list[tuple[tuple[str, ...], str]]:
    airports = search_airports(search_text)
    if airports.empty:
        return [((), "Tidak ada bandara yang cocok")]

    codes = tuple(str(code) for code in airports["airport_code"].tolist())
    options = [(codes, f"{label_when_all} ({len(codes)} airports)")]
    for row in airports.itertuples(index=False):
        label = f"{row.city} | {row.airport_name} ({row.airport_code})"
        options.append(((row.airport_code,), label))
    return options


def customer_options(search_text: str) -> list[tuple[int | None, str]]:
    customers = search_customers(search_text)
    options: list[tuple[int | None, str]] = [(None, "Belum ada pelanggan dipilih")]
    for row in customers.itertuples(index=False):
        label = f"{row.first_name} {row.last_name} | {row.email} (ID {row.customer_id})"
        options.append((int(row.customer_id), label))
    if len(options) == 1:
        options.append((None, "Tidak ada pelanggan yang cocok"))
    return options


def airline_options(search_text: str) -> list[tuple[str, str]]:
    airlines = search_airlines(search_text)
    options = [("", "Semua maskapai")]
    for row in airlines.itertuples(index=False):
        options.append((row.airline_code, f"{row.airline_name} ({row.airline_code})"))
    return options


def as_code_list(codes: tuple[str, ...] | list[str] | str) -> list[str]:
    if isinstance(codes, str):
        return [codes] if codes else []
    return [str(code) for code in codes if str(code)]


def add_in_filter(
    where_clauses: list[str],
    params: list[object],
    column: str,
    values: list[str],
) -> None:
    if not values:
        where_clauses.append("1 = 0")
        return
    placeholders = ", ".join("?" for _ in values)
    where_clauses.append(f"{column} IN ({placeholders})")
    params.extend(values)


def search_available_flights(
    origin_airport_codes: tuple[str, ...] | list[str] | str,
    dest_airport_codes: tuple[str, ...] | list[str] | str,
    airline_code: str,
    max_price: int | None,
) -> pd.DataFrame:
    where_clauses = []
    params: list[object] = []

    add_in_filter(where_clauses, params, "f.origin_airport_code", as_code_list(origin_airport_codes))
    add_in_filter(where_clauses, params, "f.dest_airport_code", as_code_list(dest_airport_codes))
    if airline_code:
        where_clauses.append("f.airline_code = ?")
        params.append(airline_code)
    if max_price is not None:
        where_clauses.append("f.price <= ?")
        params.append(max_price)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    result = run_select(
        f"""
        SELECT
            f.airline_code,
            a.airline_name,
            f.flight_code,
            f.origin_airport_code,
            origin.city AS origin_city,
            origin.airport_name AS origin_airport_name,
            f.dest_airport_code,
            destination.city AS dest_city,
            destination.airport_name AS dest_airport_name,
            f.tail_number,
            p.aircraft_type,
            p.total_seats,
            COUNT(b.booking_id) AS booked_seats,
            p.total_seats - COUNT(b.booking_id) AS available_seats,
            f.price
        FROM flights AS f
        JOIN airlines AS a ON f.airline_code = a.airline_code
        JOIN airports AS origin ON f.origin_airport_code = origin.airport_code
        JOIN airports AS destination ON f.dest_airport_code = destination.airport_code
        JOIN planes AS p ON f.tail_number = p.tail_number
        LEFT JOIN bookings AS b
            ON f.airline_code = b.airline_code
            AND f.flight_code = b.flight_code
        {where_sql}
        GROUP BY
            f.airline_code,
            a.airline_name,
            f.flight_code,
            f.origin_airport_code,
            origin.city,
            origin.airport_name,
            f.dest_airport_code,
            destination.city,
            destination.airport_name,
            f.tail_number,
            p.aircraft_type,
            p.total_seats,
            f.price
        HAVING available_seats > 0
        ORDER BY f.price ASC
        """,
        tuple(params),
    )

    if not result.empty:
        result["price_display"] = result["price"].map(format_rupiah)
    return result


def routes_from_dataframe(df: pd.DataFrame, limit: int = 120) -> list[dict[str, str]]:
    if df.empty:
        return []
    if not {"origin_airport_code", "dest_airport_code"}.issubset(df.columns):
        return []

    routes = []
    seen = set()
    for row in df[["origin_airport_code", "dest_airport_code"]].dropna().itertuples(index=False):
        origin_code = str(row.origin_airport_code)
        dest_code = str(row.dest_airport_code)
        if not origin_code or not dest_code or origin_code == dest_code:
            continue
        key = (origin_code, dest_code)
        if key in seen:
            continue
        seen.add(key)
        routes.append({"origin_airport_code": origin_code, "dest_airport_code": dest_code})
        if len(routes) >= limit:
            break
    return routes


def candidate_routes_from_airport_codes(
    origin_airport_codes: list[str],
    dest_airport_codes: list[str],
    limit: int = 180,
) -> list[dict[str, str]]:
    routes = []
    seen = set()
    for origin_code in origin_airport_codes:
        for dest_code in dest_airport_codes:
            if not origin_code or not dest_code or origin_code == dest_code:
                continue
            key = (origin_code, dest_code)
            if key in seen:
                continue
            seen.add(key)
            routes.append({"origin_airport_code": origin_code, "dest_airport_code": dest_code})
            if len(routes) >= limit:
                return routes
    return routes


def render_map_view(
    routes: list[dict[str, str]] | None = None,
    highlight_routes: list[dict[str, str]] | None = None,
    selected_route: dict[str, str] | None = None,
    height: int = 620,
) -> None:
    airports = load_airport_map_data().copy()
    airports["tooltip_text"] = (
        "<b>" + airports["airport_code"] + "</b><br/>" + airports["airport_name"] + "<br/>" + airports["city"]
    )

    routes = routes or []
    if highlight_routes is None:
        muted_routes: list[dict[str, str]] = []
        highlighted_routes = routes
    else:
        muted_routes = routes
        highlighted_routes = highlight_routes
    selected_route = selected_route or {}
    airport_lookup = airports.set_index("airport_code")
    endpoint_codes: set[str] = set()
    muted_arc_rows = []
    highlighted_arc_rows = []

    def append_arc(route: dict[str, str], target_rows: list[dict[str, object]]) -> None:
        origin_code = route.get("origin_airport_code", "")
        dest_code = route.get("dest_airport_code", "")
        if origin_code not in airport_lookup.index or dest_code not in airport_lookup.index:
            return
        if origin_code == dest_code:
            return

        origin = airport_lookup.loc[origin_code]
        destination = airport_lookup.loc[dest_code]
        route_label = f"{origin_code} → {dest_code}"
        endpoint_codes.update([origin_code, dest_code])
        target_rows.append(
            {
                "origin_airport_code": origin_code,
                "dest_airport_code": dest_code,
                "source_lon": origin["longitude"],
                "source_lat": origin["latitude"],
                "target_lon": destination["longitude"],
                "target_lat": destination["latitude"],
                "tooltip_text": f"<b>{route_label}</b>",
            }
        )

    for route in muted_routes:
        append_arc(route, muted_arc_rows)

    for route in highlighted_routes:
        append_arc(route, highlighted_arc_rows)

    selected_arc_rows = []
    selected_origin = selected_route.get("origin_airport_code", "")
    selected_dest = selected_route.get("dest_airport_code", "")
    if selected_origin in airport_lookup.index and selected_dest in airport_lookup.index and selected_origin != selected_dest:
        origin = airport_lookup.loc[selected_origin]
        destination = airport_lookup.loc[selected_dest]
        endpoint_codes.update([selected_origin, selected_dest])
        selected_arc_rows.append(
            {
                "origin_airport_code": selected_origin,
                "dest_airport_code": selected_dest,
                "source_lon": origin["longitude"],
                "source_lat": origin["latitude"],
                "target_lon": destination["longitude"],
                "target_lat": destination["latitude"],
                "tooltip_text": f"<b>{selected_origin} → {selected_dest}</b>",
            }
        )

    endpoint_data = airports[airports["airport_code"].isin(endpoint_codes)]
    layers = [
        pdk.Layer(
            "ScatterplotLayer",
            data=airports,
            get_position="[longitude, latitude]",
            get_radius=7000,
            get_fill_color=[28, 112, 184, 95],
            get_line_color=[255, 255, 255, 130],
            line_width_min_pixels=1,
            pickable=True,
        )
    ]

    if muted_arc_rows:
        layers.append(
            pdk.Layer(
                "ArcLayer",
                data=pd.DataFrame(muted_arc_rows),
                get_source_position="[source_lon, source_lat]",
                get_target_position="[target_lon, target_lat]",
                get_source_color=[110, 120, 135, 85],
                get_target_color=[110, 120, 135, 85],
                get_width=1,
                get_height=0.22,
                pickable=True,
            )
        )

    if highlighted_arc_rows:
        layers.append(
            pdk.Layer(
                "ArcLayer",
                data=pd.DataFrame(highlighted_arc_rows),
                get_source_position="[source_lon, source_lat]",
                get_target_position="[target_lon, target_lat]",
                get_source_color=[15, 92, 230, 170],
                get_target_color=[15, 92, 230, 170],
                get_width=3,
                get_height=0.22,
                pickable=True,
            )
        )

    if selected_arc_rows:
        layers.append(
            pdk.Layer(
                "ArcLayer",
                data=pd.DataFrame(selected_arc_rows),
                get_source_position="[source_lon, source_lat]",
                get_target_position="[target_lon, target_lat]",
                get_source_color=[255, 143, 0, 240],
                get_target_color=[255, 143, 0, 240],
                get_width=5,
                get_height=0.22,
                pickable=True,
            )
        )

    if not endpoint_data.empty:
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=endpoint_data,
                get_position="[longitude, latitude]",
                get_radius=19000,
                get_fill_color=[255, 186, 73, 235],
                get_line_color=[5, 45, 100, 230],
                line_width_min_pixels=2,
                pickable=True,
            )
        )
        layers.append(
            pdk.Layer(
                "TextLayer",
                data=endpoint_data,
                get_position="[longitude, latitude]",
                get_text="airport_code",
                get_size=14,
                get_color=[8, 40, 90, 255],
                get_text_anchor="middle",
                get_alignment_baseline="bottom",
            )
        )

    deck = pdk.Deck(
        map_style=MAP_STYLE,
        initial_view_state=pdk.ViewState(
            latitude=-2.6,
            longitude=118.0,
            zoom=4.05,
            pitch=18,
        ),
        layers=layers,
        tooltip={
            "html": "{tooltip_text}",
            "style": {"backgroundColor": "#1f4e79", "color": "white"},
        },
    )
    st.pydeck_chart(deck, width="stretch", height=height)


def render_overview() -> None:
    st.subheader("Dashboard Manajer")
    st.write(
        "Antarmuka ini adalah situs web lokal sederhana menggunakan Streamlit, namun dengan logika setara Jupyter. "
        "Menggunakan widget Python, kueri SQLite, tombol, dan tabel hasil."
    )

    columns = st.columns(3)
    for index, table in enumerate(TABLES):
        with columns[index % 3]:
            st.metric(table, table_count(table))

    st.markdown("### Alur Demonstrasi")
    st.write("1. Cari tiket dan buat pemesanan di tab Tambah Pemesanan.")
    st.write("2. Jelajahi tabel mentah/terbaca di tab Database.")
    st.write("3. Tambahkan catatan data master di tab Manajemen Data.")
    st.write("4. Tambahkan pelanggan jika diperlukan.")
    st.write("5. Jalankan kueri SELECT yang telah disiapkan atau kustom.")


def render_add_booking() -> None:
    map_col, panel_col = st.columns([1.25, 1.1], gap="large", vertical_alignment="center")
    selected_route: dict[str, str] | None = None
    candidate_routes: list[dict[str, str]] = []
    available_routes: list[dict[str, str]] = []
    result = pd.DataFrame()

    with panel_col:
        with st.container(height=ADD_BOOKING_PANEL_HEIGHT, border=False):
            st.subheader("Tambah Pemesanan")
            st.caption("Cari tiket yang cocok, pilih satu kartu tiket, lalu pilih kursi yang tersedia.")

            st.markdown("### Pelanggan")
            customer_search = st.text_input(
                "Cari pelanggan",
                key="customer_search_booking",
                placeholder="Cari berdasarkan nama, email, atau ID pelanggan",
            )
            customer_choice = st.selectbox(
                "Pelanggan",
                customer_options(customer_search),
                format_func=lambda option: option[1],
            )
            selected_customer_id = customer_choice[0]

            st.divider()
            st.markdown("### Cari Tiket")

            origin_search = st.text_input("Cari bandara asal", key="origin_airport_search")
            origin_choice = st.selectbox(
                "Pilih bandara asal",
                airport_options(origin_search, "Semua bandara asal yang cocok"),
                format_func=lambda option: option[1],
            )
            origin_codes = list(origin_choice[0])

            dest_search = st.text_input("Cari bandara tujuan", key="dest_airport_search")
            dest_choice = st.selectbox(
                "Pilih bandara tujuan",
                airport_options(dest_search, "Semua bandara tujuan yang cocok"),
                format_func=lambda option: option[1],
            )
            dest_codes = list(dest_choice[0])

            airline_search = st.text_input("Cari maskapai (opsional)", key="airline_search")
            airline_choice = st.selectbox("Maskapai", airline_options(airline_search), format_func=lambda option: option[1])
            airline_code = airline_choice[0]

            max_price_text = st.text_input("Harga maksimum (opsional)", key="max_price_search", placeholder="1000000")
            try:
                max_price = parse_optional_price(max_price_text)
            except ValueError as error:
                st.error(str(error))
                max_price = None

            if not origin_codes or not dest_codes:
                st.warning("Pilih bandara asal dan tujuan yang valid.")
            else:
                result = search_available_flights(origin_codes, dest_codes, airline_code, max_price)
                candidate_routes = candidate_routes_from_airport_codes(origin_codes, dest_codes)

            st.markdown("### Tiket Tersedia")
            available_routes = routes_from_dataframe(result)
            if result.empty:
                st.info("Tidak ada tiket tersedia untuk pencarian saat ini.")
            else:
                st.caption(
                    f"Ditemukan {len(result)} tiket tersedia di {len(available_routes)} jalur rute tersedia. "
                    "Jalur abu-abu adalah pasangan bandara kandidat; jalur biru memiliki tiket tersedia."
                )

            selected_ticket_key = st.session_state.get("selected_ticket_key", "")
            valid_ticket_keys = set()
            for row in result.itertuples(index=False):
                valid_ticket_keys.add(f"{row.airline_code}|{row.flight_code}")
            if selected_ticket_key and selected_ticket_key not in valid_ticket_keys:
                st.session_state["selected_ticket_key"] = ""
                selected_ticket_key = ""

            if selected_ticket_key and st.button("Batalkan pilihan tiket dan tampilkan semua jalur"):
                st.session_state["selected_ticket_key"] = ""
                st.rerun()

            for row in result.itertuples(index=False):
                ticket_key = f"{row.airline_code}|{row.flight_code}"
                selected = selected_ticket_key == ticket_key
                with st.container(border=True):
                    top_col, action_col = st.columns([3.4, 1.0])
                    with top_col:
                        st.markdown(f"**{row.airline_name} ({row.airline_code} {row.flight_code})**")
                        st.write(
                            f"{row.origin_city} | {row.origin_airport_name} ({row.origin_airport_code}) "
                            f"→ {row.dest_city} | {row.dest_airport_name} ({row.dest_airport_code})"
                        )
                        st.caption(
                            f"Pesawat: {row.aircraft_type} | Tail: {row.tail_number} | "
                            f"Kursi tersedia: {row.available_seats}"
                        )
                    with action_col:
                        st.markdown(f"**{format_rupiah(row.price)}**")
                        if selected:
                            st.success("Dipilih")
                        elif st.button("Pilih", key=f"select_ticket_{ticket_key}"):
                            st.session_state["selected_ticket_key"] = ticket_key
                            st.rerun()

            selected_ticket = ("", "")
            selected_flight_row = None
            available_seats: list[str] = []
            if selected_ticket_key:
                selected_airline_code, selected_flight_code = selected_ticket_key.split("|", 1)
                selected_ticket = (selected_airline_code, selected_flight_code)
                matching_rows = result[
                    (result["airline_code"] == selected_airline_code)
                    & (result["flight_code"] == selected_flight_code)
                ]
                if not matching_rows.empty:
                    selected_flight_row = matching_rows.iloc[0]
                    selected_route = {
                        "origin_airport_code": str(selected_flight_row["origin_airport_code"]),
                        "dest_airport_code": str(selected_flight_row["dest_airport_code"]),
                    }
                    available_seats = available_seats_for_flight(selected_airline_code, selected_flight_code)

            if selected_flight_row is not None:
                st.info(
                    f"Selected ticket: {selected_flight_row['airline_code']} {selected_flight_row['flight_code']} | "
                    f"{selected_flight_row['origin_airport_code']} → {selected_flight_row['dest_airport_code']} | "
                    f"{format_rupiah(selected_flight_row['price'])}"
                )

            transaction_date = st.date_input("Tanggal transaksi", value=date.today())
            if available_seats:
                seat_number = st.selectbox("seat_number tersedia", available_seats)
            else:
                seat_number = ""
                st.selectbox("seat_number tersedia", ["Tidak ada kursi tersedia"], disabled=True)

            if st.button("Buat pemesanan"):
                if not selected_ticket[0] or not selected_ticket[1]:
                    st.error("Pilih tiket yang tersedia sebelum membuat pemesanan.")
                elif selected_customer_id is None:
                    st.error("Pilih pelanggan sebelum membuat pemesanan.")
                elif not seat_number:
                    st.error("Pilih kursi yang tersedia sebelum membuat pemesanan.")
                else:
                    try:
                        booking_id = execute_write(
                            """
                            INSERT INTO bookings (
                                airline_code,
                                flight_code,
                                seat_number,
                                customer_id,
                                transaction_date
                            )
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                selected_ticket[0],
                                selected_ticket[1],
                                seat_number,
                                int(selected_customer_id),
                                transaction_date.isoformat(),
                            ),
                        )
                        clear_query_cache()
                        st.success(f"Pemesanan berhasil ditambahkan dengan booking_id = {booking_id}.")
                    except sqlite3.IntegrityError as error:
                        st.error(f"Tidak dapat membuat pemesanan: {error}")

            st.markdown("### Pemesanan Terbaru")
            st.dataframe(
                run_select(
                    """
                    SELECT
                        b.booking_id,
                        b.transaction_date,
                        c.first_name || ' ' || c.last_name AS customer_name,
                        b.airline_code,
                        b.flight_code,
                        f.origin_airport_code,
                        f.dest_airport_code,
                        b.seat_number
                    FROM bookings AS b
                    JOIN customers AS c ON b.customer_id = c.customer_id
                    JOIN flights AS f
                        ON b.airline_code = f.airline_code
                        AND b.flight_code = f.flight_code
                    ORDER BY b.booking_id DESC
                    LIMIT 10
                    """
                ),
                width="stretch",
            )

    with map_col:
        st.subheader("Peta Rute")
        if selected_route:
            render_map_view([], selected_route=selected_route, height=ADD_BOOKING_PANEL_HEIGHT)
        else:
            render_map_view(candidate_routes, highlight_routes=available_routes, height=ADD_BOOKING_PANEL_HEIGHT)


def database_filter_widgets(table: str) -> dict[str, str]:
    filters: dict[str, str] = {}
    if table == "airports":
        filters["search"] = st.text_input("Filter airport_code, kota, atau nama")
    elif table == "airlines":
        filters["search"] = st.text_input("Filter airline_code atau nama maskapai")
    elif table == "planes":
        col1, col2 = st.columns(2)
        with col1:
            filters["owner_airline"] = normalize_code(st.text_input("owner_airline"))
        with col2:
            filters["search"] = st.text_input("Filter tail_number atau tipe pesawat")
    elif table == "flights":
        col1, col2 = st.columns(2)
        with col1:
            filters["origin"] = normalize_code(st.text_input("origin_airport_code"))
            filters["airline"] = normalize_code(st.text_input("airline_code"))
        with col2:
            filters["destination"] = normalize_code(st.text_input("dest_airport_code"))
            filters["flight_code"] = normalize_code(st.text_input("flight_code"))
    elif table == "customers":
        filters["search"] = st.text_input("Filter nama atau email")
    elif table == "bookings":
        col1, col2 = st.columns(2)
        with col1:
            filters["customer"] = st.text_input("Nama/email atau ID pelanggan")
            filters["airline"] = normalize_code(st.text_input("airline_code"))
        with col2:
            filters["flight_code"] = normalize_code(st.text_input("flight_code"))
            filters["transaction_date"] = st.text_input("Tanggal transaksi YYYY-MM-DD")
    return filters


def database_query(table: str, view_mode: str, filters: dict[str, str]) -> tuple[str, tuple]:
    readable = view_mode == "Tampilan Terbaca"
    params: list[object] = []
    conditions = []

    if table == "airports":
        select_sql = "SELECT a.* FROM airports AS a"
        search = filters.get("search", "").strip().lower()
        if search:
            conditions.append("(LOWER(a.airport_code) LIKE ? OR LOWER(a.city) LIKE ? OR LOWER(a.airport_name) LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        order_sql = "ORDER BY a.airport_code"
    elif table == "airlines":
        if readable:
            select_sql = """
                SELECT
                    a.airline_code,
                    a.airline_name,
                    COUNT(DISTINCT p.tail_number) AS plane_count,
                    COUNT(DISTINCT f.flight_code) AS flight_count
                FROM airlines AS a
                LEFT JOIN planes AS p ON a.airline_code = p.owner_airline
                LEFT JOIN flights AS f ON a.airline_code = f.airline_code
            """
        else:
            select_sql = "SELECT a.* FROM airlines AS a"
        search = filters.get("search", "").strip().lower()
        if search:
            conditions.append("(LOWER(a.airline_code) LIKE ? OR LOWER(a.airline_name) LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        order_sql = "GROUP BY a.airline_code, a.airline_name ORDER BY a.airline_code" if readable else "ORDER BY a.airline_code"
    elif table == "planes":
        if readable:
            select_sql = """
                SELECT
                    p.tail_number,
                    p.aircraft_type,
                    p.total_seats,
                    p.owner_airline,
                    a.airline_name
                FROM planes AS p
                JOIN airlines AS a ON p.owner_airline = a.airline_code
            """
        else:
            select_sql = "SELECT p.* FROM planes AS p"
        if filters.get("owner_airline"):
            conditions.append("p.owner_airline = ?")
            params.append(filters["owner_airline"])
        search = filters.get("search", "").strip().lower()
        if search:
            conditions.append("(LOWER(p.tail_number) LIKE ? OR LOWER(p.aircraft_type) LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        order_sql = "ORDER BY p.owner_airline, p.tail_number"
    elif table == "flights":
        if readable:
            select_sql = """
                SELECT
                    f.airline_code,
                    a.airline_name,
                    f.flight_code,
                    f.origin_airport_code,
                    origin.city AS origin_city,
                    f.dest_airport_code,
                    destination.city AS destination_city,
                    f.tail_number,
                    p.aircraft_type,
                    f.price
                FROM flights AS f
                JOIN airlines AS a ON f.airline_code = a.airline_code
                JOIN airports AS origin ON f.origin_airport_code = origin.airport_code
                JOIN airports AS destination ON f.dest_airport_code = destination.airport_code
                JOIN planes AS p ON f.tail_number = p.tail_number
            """
        else:
            select_sql = "SELECT f.* FROM flights AS f"
        if filters.get("origin"):
            conditions.append("f.origin_airport_code = ?")
            params.append(filters["origin"])
        if filters.get("destination"):
            conditions.append("f.dest_airport_code = ?")
            params.append(filters["destination"])
        if filters.get("airline"):
            conditions.append("f.airline_code = ?")
            params.append(filters["airline"])
        if filters.get("flight_code"):
            conditions.append("f.flight_code = ?")
            params.append(filters["flight_code"])
        order_sql = "ORDER BY f.airline_code, f.flight_code"
    elif table == "customers":
        if readable:
            select_sql = """
                SELECT
                    c.customer_id,
                    c.first_name,
                    c.last_name,
                    c.email,
                    c.phone,
                    COUNT(b.booking_id) AS booking_count
                FROM customers AS c
                LEFT JOIN bookings AS b ON c.customer_id = b.customer_id
            """
        else:
            select_sql = "SELECT c.* FROM customers AS c"
        search = filters.get("search", "").strip().lower()
        if search:
            conditions.append("(LOWER(c.first_name) LIKE ? OR LOWER(c.last_name) LIKE ? OR LOWER(c.email) LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        order_sql = "GROUP BY c.customer_id ORDER BY c.customer_id DESC" if readable else "ORDER BY c.customer_id DESC"
    elif table == "bookings":
        if readable:
            select_sql = """
                SELECT
                    b.booking_id,
                    b.transaction_date,
                    c.first_name || ' ' || c.last_name AS customer_name,
                    c.email,
                    b.airline_code,
                    a.airline_name,
                    b.flight_code,
                    f.origin_airport_code,
                    f.dest_airport_code,
                    b.seat_number,
                    f.price
                FROM bookings AS b
                JOIN customers AS c ON b.customer_id = c.customer_id
                JOIN flights AS f
                    ON b.airline_code = f.airline_code
                    AND b.flight_code = f.flight_code
                JOIN airlines AS a ON f.airline_code = a.airline_code
            """
        else:
            select_sql = "SELECT b.* FROM bookings AS b JOIN customers AS c ON b.customer_id = c.customer_id"
        customer_filter = filters.get("customer", "").strip().lower()
        if customer_filter:
            conditions.append("(CAST(c.customer_id AS TEXT) = ? OR LOWER(c.email) LIKE ? OR LOWER(c.first_name || ' ' || c.last_name) LIKE ?)")
            params.extend([customer_filter, f"%{customer_filter}%", f"%{customer_filter}%"])
        if filters.get("airline"):
            conditions.append("b.airline_code = ?")
            params.append(filters["airline"])
        if filters.get("flight_code"):
            conditions.append("b.flight_code = ?")
            params.append(filters["flight_code"])
        if filters.get("transaction_date"):
            conditions.append("b.transaction_date = ?")
            params.append(filters["transaction_date"].strip())
        order_sql = "ORDER BY b.booking_id DESC"
    else:
        raise ValueError("Unsupported table")

    where_sql = ""
    if conditions:
        where_sql = "WHERE " + " AND ".join(conditions)
    sql = f"{select_sql} {where_sql} {order_sql}"
    return sql, tuple(params)


def render_table_metadata(table: str) -> None:
    metadata = TABLE_METADATA[table]
    row_count_col, details_col = st.columns([1, 4])
    row_count_col.metric("Jumlah Baris", table_count(table))
    constraint_rows = [
        {"Tipe": "Primary key", "Detail": metadata["primary_key"]},
        {
            "Tipe": "Foreign key",
            "Detail": "\n".join(metadata["foreign_keys"]) if metadata["foreign_keys"] else "Tidak ada",
        },
        {"Tipe": "Constraint lain", "Detail": "\n".join(metadata["constraints"])},
    ]
    details_col.table(pd.DataFrame(constraint_rows))
    st.caption(metadata["description"])


def render_database_checks() -> None:
    checks = []
    conn = get_connection()
    try:
        foreign_key_issues = conn.execute("PRAGMA foreign_key_check").fetchall()
    finally:
        conn.close()
    checks.append(
        {
            "Pemeriksaan": "Referensi foreign key",
            "Constraint yang diuji": "Setiap nilai FK harus cocok dengan parent key yang ada.",
            "Hasil": "Lulus" if not foreign_key_issues else f"Gagal: {foreign_key_issues}",
        }
    )

    duplicate_seats = run_select(
        """
        SELECT COUNT(*) AS total
        FROM (
            SELECT airline_code, flight_code, seat_number, COUNT(*) AS duplicate_count
            FROM bookings
            GROUP BY airline_code, flight_code, seat_number
            HAVING duplicate_count > 1
        )
        """
    ).iloc[0]["total"]
    checks.append(
        {
            "Pemeriksaan": "Kursi dipesan duplikat",
            "Constraint yang diuji": "UNIQUE(airline_code, flight_code, seat_number)",
            "Hasil": str(int(duplicate_seats)),
        }
    )

    same_route = run_select(
        """
        SELECT COUNT(*) AS total
        FROM flights
        WHERE origin_airport_code = dest_airport_code
        """
    ).iloc[0]["total"]
    checks.append(
        {
            "Pemeriksaan": "Asal sama dengan tujuan",
            "Constraint yang diuji": "CHECK(origin_airport_code <> dest_airport_code)",
            "Hasil": str(int(same_route)),
        }
    )

    invalid_airports = run_select(
        """
        SELECT COUNT(*) AS total
        FROM airports
        WHERE airport_code IS NULL OR TRIM(airport_code) = '' OR airport_code = '\\N'
        """
    ).iloc[0]["total"]
    checks.append(
        {
            "Pemeriksaan": "airport_code tidak valid",
            "Constraint yang diuji": "airport_code tidak boleh NULL, kosong, atau \\N",
            "Hasil": str(int(invalid_airports)),
        }
    )

    invalid_airlines = run_select(
        """
        SELECT COUNT(*) AS total
        FROM airlines
        WHERE airline_code IS NULL OR TRIM(airline_code) = '' OR airline_code = '\\N'
        """
    ).iloc[0]["total"]
    checks.append(
        {
            "Pemeriksaan": "airline_code tidak valid",
            "Constraint yang diuji": "airline_code tidak boleh NULL, kosong, atau \\N",
            "Hasil": str(int(invalid_airlines)),
        }
    )

    st.table(pd.DataFrame(checks))


def render_database_browser() -> None:
    st.subheader("Database")
    table = st.selectbox("Tabel", TABLES)
    view_mode = st.radio("Mode tampilan", ["Tampilan Terbaca", "Tampilan Mentah"], horizontal=True)
    render_table_metadata(table)

    filters = database_filter_widgets(table)
    sql, params = database_query(table, view_mode, filters)
    total_rows = int(
        run_select(
            f"SELECT COUNT(*) AS total FROM ({sql}) AS filtered_rows",
            params,
        ).iloc[0]["total"]
    )
    total_pages = max(1, (total_rows + DATABASE_PAGE_SIZE - 1) // DATABASE_PAGE_SIZE)
    page = int(
        st.number_input(
            "Halaman",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            help=f"{DATABASE_PAGE_SIZE} baris per halaman.",
        )
    )
    offset = (page - 1) * DATABASE_PAGE_SIZE
    result = run_select(
        f"{sql} LIMIT ? OFFSET ?",
        params + (DATABASE_PAGE_SIZE, offset),
    )

    st.caption(f"Menampilkan halaman {page} dari {total_pages}; {DATABASE_PAGE_SIZE} baris per halaman; {total_rows} baris cocok.")
    st.table(result.reset_index(drop=True))

    with st.expander("Tampilkan kueri SQL"):
        st.code(sql.strip(), language="sql")
        if params:
            st.write("Parameter:", params)

    with st.expander("Pemeriksaan database"):
        st.caption("Setiap pemeriksaan memetakan ke aturan skema atau aturan pembersihan data yang digunakan proyek ini.")
        render_database_checks()


def render_add_customer() -> None:
    st.subheader("Tambah Pelanggan")
    with st.form("add_customer_form"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("Nama depan")
            email = st.text_input("Email")
            password = st.text_input("Kata sandi", value="pass123", type="password")
        with col2:
            last_name = st.text_input("Nama belakang")
            phone = st.text_input("Telepon", value="081234567890")

        submitted = st.form_submit_button("Tambah pelanggan")

    if submitted:
        first_name = first_name.strip()
        last_name = last_name.strip()
        email = email.strip().lower()
        phone = phone.strip()
        password = password.strip()

        if not first_name or not last_name or not email:
            st.error("Nama depan, nama belakang, dan email wajib diisi.")
        else:
            try:
                customer_id = execute_write(
                    """
                    INSERT INTO customers (first_name, last_name, email, phone, password)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (first_name, last_name, email, phone, password),
                )
                clear_query_cache()
                st.success(f"Pelanggan berhasil ditambahkan dengan customer_id = {customer_id}.")
            except sqlite3.IntegrityError as error:
                st.error(f"Tidak dapat menambahkan pelanggan: {error}")

    st.markdown("### Pelanggan Terbaru")
    st.dataframe(
        run_select(
            """
            SELECT customer_id, first_name, last_name, email, phone
            FROM customers
            ORDER BY customer_id DESC
            LIMIT 10
            """
        ),
        width="stretch",
    )


def render_insert_constraints(target: str) -> None:
    st.markdown("**Constraint penyisipan**")
    for rule in INSERT_CONSTRAINTS[target]:
        st.caption(f"- {rule}")


def render_data_maintenance() -> None:
    st.subheader("Manajemen Data")
    st.caption("Formulir penyisipan terkontrol untuk data master. Pemesanan tetap di Tambah Pemesanan; pelanggan tetap di Tambah Pelanggan.")
    target = st.selectbox("Jenis catatan", ["airlines", "airports", "planes", "flights"])
    render_insert_constraints(target)

    if target == "airlines":
        with st.form("add_airline_form"):
            airline_code = normalize_code(st.text_input("airline_code", placeholder="GA"))
            airline_name = st.text_input("airline_name", placeholder="Garuda Indonesia")
            submitted = st.form_submit_button("Tambah maskapai")
        if submitted:
            if not airline_code or not airline_name.strip():
                st.error("airline_code dan airline_name wajib diisi.")
            else:
                try:
                    execute_write(
                        "INSERT INTO airlines (airline_code, airline_name) VALUES (?, ?)",
                        (airline_code, airline_name.strip()),
                    )
                    clear_query_cache()
                    st.success("Maskapai berhasil ditambahkan.")
                except sqlite3.IntegrityError as error:
                    st.error(f"Tidak dapat menambahkan maskapai: {error}")

    elif target == "airports":
        with st.form("add_airport_form"):
            col1, col2 = st.columns(2)
            with col1:
                airport_code = normalize_code(st.text_input("airport_code", placeholder="CGK"))
                airport_name = st.text_input("airport_name")
                city = st.text_input("city")
            with col2:
                latitude = st.text_input("latitude", placeholder="-6.1256")
                longitude = st.text_input("longitude", placeholder="106.6559")
            submitted = st.form_submit_button("Tambah bandara")
        if submitted:
            try:
                lat_value = float(latitude)
                lon_value = float(longitude)
            except ValueError:
                st.error("latitude dan longitude harus berupa angka.")
            else:
                if not airport_code or not airport_name.strip():
                    st.error("airport_code dan airport_name wajib diisi.")
                else:
                    try:
                        execute_write(
                            """
                            INSERT INTO airports (airport_code, airport_name, city, latitude, longitude)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (airport_code, airport_name.strip(), city.strip(), lat_value, lon_value),
                        )
                        clear_query_cache()
                        st.success("Bandara berhasil ditambahkan.")
                    except sqlite3.IntegrityError as error:
                        st.error(f"Tidak dapat menambahkan bandara: {error}")

    elif target == "planes":
        with st.form("add_plane_form"):
            col1, col2 = st.columns(2)
            with col1:
                tail_number = normalize_code(st.text_input("tail_number", placeholder="PK-GZZ"))
                aircraft_type = st.text_input("aircraft_type", placeholder="Boeing 737-800")
            with col2:
                total_seats = st.number_input("total_seats", min_value=1, value=180, step=1)
                owner_airline = normalize_code(st.text_input("owner_airline", placeholder="GA"))
            submitted = st.form_submit_button("Tambah pesawat")
        if submitted:
            if not tail_number or not aircraft_type.strip() or not owner_airline:
                st.error("tail_number, aircraft_type, dan owner_airline wajib diisi.")
            elif not value_exists("airlines", "airline_code", owner_airline):
                st.error("owner_airline harus sudah ada di tabel airlines.")
            else:
                try:
                    execute_write(
                        """
                        INSERT INTO planes (tail_number, aircraft_type, total_seats, owner_airline)
                        VALUES (?, ?, ?, ?)
                        """,
                        (tail_number, aircraft_type.strip(), int(total_seats), owner_airline),
                    )
                    clear_query_cache()
                    st.success("Pesawat berhasil ditambahkan.")
                except sqlite3.IntegrityError as error:
                    st.error(f"Tidak dapat menambahkan pesawat: {error}")

    elif target == "flights":
        with st.form("add_flight_form"):
            col1, col2 = st.columns(2)
            with col1:
                airline_code = normalize_code(st.text_input("airline_code", placeholder="GA"))
                flight_code = normalize_code(st.text_input("flight_code", placeholder="1999"))
                origin_airport_code = normalize_code(st.text_input("origin_airport_code", placeholder="CGK"))
            with col2:
                dest_airport_code = normalize_code(st.text_input("dest_airport_code", placeholder="DPS"))
                tail_number = normalize_code(st.text_input("tail_number", placeholder="PK-GAA"))
                price = st.number_input("price", min_value=0, value=900000, step=50000)
            submitted = st.form_submit_button("Tambah penerbangan")
        if submitted:
            errors = []
            if not airline_code or not flight_code or not origin_airport_code or not dest_airport_code or not tail_number:
                errors.append("Semua field kode penerbangan wajib diisi.")
            if origin_airport_code == dest_airport_code:
                errors.append("origin_airport_code dan dest_airport_code tidak boleh sama.")
            if airline_code and not value_exists("airlines", "airline_code", airline_code):
                errors.append("airline_code harus sudah ada di tabel airlines.")
            if origin_airport_code and not value_exists("airports", "airport_code", origin_airport_code):
                errors.append("origin_airport_code harus sudah ada di tabel airports.")
            if dest_airport_code and not value_exists("airports", "airport_code", dest_airport_code):
                errors.append("dest_airport_code harus sudah ada di tabel airports.")
            if tail_number and not value_exists("planes", "tail_number", tail_number):
                errors.append("tail_number harus sudah ada di tabel planes.")
            elif tail_number:
                plane_owner = run_select(
                    "SELECT owner_airline FROM planes WHERE tail_number = ?",
                    (tail_number,),
                ).iloc[0]["owner_airline"]
                if plane_owner != airline_code:
                    errors.append("tail_number harus milik airline_code yang dipilih.")

            if errors:
                for error in errors:
                    st.error(error)
            else:
                try:
                    execute_write(
                        """
                        INSERT INTO flights (
                            airline_code,
                            flight_code,
                            origin_airport_code,
                            dest_airport_code,
                            tail_number,
                            price
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            airline_code,
                            flight_code,
                            origin_airport_code,
                            dest_airport_code,
                            tail_number,
                            int(price),
                        ),
                    )
                    clear_query_cache()
                    st.success("Penerbangan berhasil ditambahkan.")
                except sqlite3.IntegrityError as error:
                    st.error(f"Tidak dapat menambahkan penerbangan: {error}")


def is_safe_select(query: str) -> bool:
    stripped = query.strip()
    if not stripped:
        return False
    normalized = stripped.rstrip(";").strip()
    if not normalized.lower().startswith("select"):
        return False
    return ";" not in normalized


def render_query_result_with_optional_map(result: pd.DataFrame) -> None:
    routes = routes_from_dataframe(result)
    if routes:
        map_col, table_col = st.columns([1.15, 1.0], gap="large")
        with map_col:
            render_map_view(routes, height=430)
        with table_col:
            st.dataframe(result, width="stretch")
    else:
        st.dataframe(result, width="stretch")


def render_queries_and_insights() -> None:
    st.subheader("Query Database")
    query_name = st.selectbox("Query yang telah disiapkan", list(PREDEFINED_QUERIES))
    query_spec = PREDEFINED_QUERIES[query_name]
    st.caption(query_spec["description"])

    with st.expander("Tampilkan SQL yang telah disiapkan"):
        st.code(query_spec["sql"].strip(), language="sql")

    result = run_select(query_spec["sql"])
    render_query_result_with_optional_map(result)

    st.markdown("### Query SELECT")
    custom_query = st.text_area(
        "SQL kustom",
        value="SELECT * FROM flights LIMIT 10;",
        height=140,
        help="Hanya satu pernyataan SELECT yang diizinkan.",
    )

    if st.button("Jalankan SELECT kustom"):
        if not is_safe_select(custom_query):
            st.error("Hanya satu pernyataan SELECT yang diizinkan di GUI demo ini.")
        else:
            try:
                custom_result = run_select(custom_query.strip())
                render_query_result_with_optional_map(custom_result)
            except Exception as error:
                st.error(f"Query gagal: {error}")


def main() -> None:
    st.set_page_config(page_title="Manajer Pemesanan Tiket", layout="wide")
    st.title("Dashboard Manajer Pemesanan Tiket")

    if not DB_PATH.exists():
        st.error("File database tidak ditemukan: flight-booking.db")
        st.info("Jalankan 01_download.py hingga 05_validate_database.py terlebih dahulu.")
        st.stop()

    initialize_session_state()
    tabs = st.tabs(["Tambah Pemesanan", "Database", "Manajemen Data", "Tambah Pelanggan", "Query Database", "Overview"])

    with tabs[0]:
        render_add_booking()
    with tabs[1]:
        render_database_browser()
    with tabs[2]:
        render_data_maintenance()
    with tabs[3]:
        render_add_customer()
    with tabs[4]:
        render_queries_and_insights()
    with tabs[5]:
        render_overview()

    st.caption(f"Database: {DB_PATH.name}")



if __name__ == "__main__":
    main()
