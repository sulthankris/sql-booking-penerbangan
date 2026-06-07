# Project Overview – Indonesian Domestic Flight Ticket Sales Database and Manager Dashboard

## 1. Background & Introduction

This project builds a lightweight relational database for **Indonesian domestic flight ticket sales**. The main purpose is to show how flight, customer, aircraft, and booking data can be structured, connected, queried, and analyzed using SQL.

The project is not positioned as a finished public airline website. It is a **database mini project with a manager-facing web interface**. The web interface is used by an airline ticket-sales manager or system operator to demonstrate and manage the ticket-booking workflow.

Indonesian domestic flights involve many airports, airlines, aircraft, routes, customers, and ticket transactions. Managing this information in separate files would make it difficult to search, validate, and analyze the data. A relational database is suitable because it can:

- store each main object in a clear table;
- connect tables through primary keys and foreign keys;
- support route search and booking simulation;
- run analytical SQL queries for simple business insights;
- support a GUI for adding, viewing, filtering, and querying data.

The data is a **composite of real and synthetic sources**. Real public data is used where available, while synthetic data is generated where realistic open data is difficult to obtain.

### Data Source Approach

A complete open dataset of Indonesian flight schedules with aircraft assignments, customer bookings, seat numbers, and ticket prices is difficult to obtain. For that reason, this project combines:

- **OpenFlights data** for airport metadata, airline metadata, and domestic route structures.
- **Synthetic data** for aircraft registrations, customer accounts, bookings, seat numbers, transaction dates, and ticket prices.

This approach keeps the project realistic enough for analysis while remaining feasible for a classroom mini project.

---

## 2. System Scope and User Role

The primary user of the system is the **manager/operator**, not the end customer.

The database contains customer data and booking data, but customers are treated as **data subjects** in the simulation. The manager uses the GUI to simulate what would happen in a customer-facing ticket system, while also having access to management and analysis features required by the database mini project.

### Manager Capabilities

Through the GUI, the manager can:

1. **Manage and inspect database records**  
   View tables such as airports, airlines, planes, flights, customers, and bookings.

2. **Simulate customer registration/login**  
   Add or select a customer profile to represent a customer using the ticket system.

3. **Simulate ticket search and booking**  
   Search available tickets by airport search fields, select a customer through a search dropdown, select a flight, choose an available seat, and create a booking.

4. **Maintain master data**  
   Add controlled records for airlines, airports, planes, and flights through table-specific forms.

5. **Run SQL queries and view query results**  
   Execute predefined or custom SQLite `SELECT` queries to support SQL demonstration and analysis.

6. **Generate simple insights**  
   Use query results to summarize booking counts, popular routes, airline activity, average prices, or other simple patterns in the data.

### Important Clarification

The SQL query feature and full database browsing feature are **manager-only features**. A real customer-facing website should not allow customers to browse the whole database or run arbitrary SQL queries. In this project, those features exist because the assignment requires database interaction, SQL implementation, testing, and insight generation.

The GUI is designed as a **simple local website using Streamlit, but with Jupyter-level logic**. It avoids Flask/Django, HTML/CSS/JavaScript, an intricate login system, an API layer, and ORM tools. The interface is limited to Python widgets, SQLite queries, buttons, maps, and result tables.

---

## 3. Mini Project Requirement Coverage

| Requirement | Project Coverage |
|-------------|------------------|
| Minimum 5 entities | The design uses 6 entities: `airports`, `airlines`, `planes`, `flights`, `customers`, and `bookings`. |
| ER Diagram | The ERD shows entities, attributes, primary keys, foreign keys, relationships, and cardinalities. |
| Minimum 8 SQL queries | Queries include filtering, joins, grouping, ordering, and aggregate functions such as `COUNT`, `AVG`, `MIN`, and `MAX`. |
| Simple GUI | The manager dashboard supports adding records, displaying tables, searching/filtering data, booking simulation, map display, and query results. |
| Query testing | SQL queries, GUI inserts, and database integrity checks can be tested against the SQLite database. |
| Simple insights | The data supports insights such as most booked routes, airlines with the most bookings, average ticket price by route, and booking trends by transaction date. |

---

## 4. Database Structure (6 Tables)

All tables follow Third Normal Form (3NF). The schema uses natural IATA codes as primary keys where they are meaningful and stable:

- `airports.airport_code` stores the 3-letter airport IATA code, such as `CGK`, `DPS`, or `SUB`.
- `airlines.airline_code` stores the 2-letter airline IATA code, such as `GA`, `JT`, or `QG`.

Using these real aviation codes makes the relationships easier to understand because foreign keys contain recognizable values such as airport and airline codes.

### 4.1 `airports`
**Source:** Real – OpenFlights `airports.dat`, filtered for `country = 'Indonesia'`.

| Attribute | Type | Key | Description | Source Detail |
|-----------|------|-----|-------------|---------------|
| `airport_code` | TEXT(3) | PRIMARY KEY | 3-letter airport IATA code, e.g., `CGK`, `DPS`, `SUB` | From OpenFlights `IATA` column; rows with `\N` discarded |
| `airport_name` | TEXT | NOT NULL | Full airport name | From `name` column |
| `city` | TEXT | | City served by the airport | From `city` column |
| `latitude` | REAL | | Decimal latitude | From `lat` column; used by the GUI map |
| `longitude` | REAL | | Decimal longitude | From `lon` column; used by the GUI map |

`country` is not stored because this database is already filtered to Indonesian airports only.

---

### 4.2 `airlines`
**Source:** Real – OpenFlights `airlines.dat`, filtered for active Indonesian carriers, plus manually added major missing airlines where needed.

| Attribute | Type | Key | Description | Source Detail |
|-----------|------|-----|-------------|---------------|
| `airline_code` | TEXT(2) | PRIMARY KEY | 2-letter airline IATA code, e.g., `GA`, `JT`, `QG` | From OpenFlights `IATA` column; blank entries skipped |
| `airline_name` | TEXT | NOT NULL | Full airline name | From `name` column |

`airline_code` is used as the main identifier because it is stable, short, and already used by route and flight data.

---

### 4.3 `planes`
**Source:** Synthetic – generated based on realistic Indonesian fleet data such as aircraft types, seat capacities, and registration prefixes.

| Attribute | Type | Key | Description | Source Detail |
|-----------|------|-----|-------------|---------------|
| `tail_number` | TEXT(6) | PRIMARY KEY | Aircraft registration, e.g., `PK-Gxx`, `PK-Lxx` | Synthetic; follows Indonesian civil aircraft registration pattern |
| `aircraft_type` | TEXT | NOT NULL | Model and variant, e.g., `Boeing 737-800`, `Airbus A320-200` | Curated from real fleet compositions |
| `total_seats` | INTEGER | NOT NULL | Seat capacity for the aircraft | Based on typical real-world seat configurations |
| `owner_airline` | TEXT(2) | FOREIGN KEY → `airlines.airline_code` | Airline that owns or operates the aircraft | Assigned according to likely fleet ownership |

---

### 4.4 `flights`
**Source:** Core structural data from OpenFlights `routes.dat`, filtered to Indonesian domestic routes. Flight codes, prices, and aircraft assignments are synthetically generated.

| Attribute | Type | Key | Description | Source Detail |
|-----------|------|-----|-------------|---------------|
| `airline_code` | TEXT(2) | PRIMARY KEY + FOREIGN KEY → `airlines.airline_code` | Airline operating the flight | From route airline IATA code |
| `flight_code` | TEXT(4) | PRIMARY KEY | Flight code within that airline, e.g., `1001`, `1042` | Synthetic; generated per airline |
| `origin_airport_code` | TEXT(3) | FOREIGN KEY → `airports.airport_code` | Departure airport code | From route origin IATA code |
| `dest_airport_code` | TEXT(3) | FOREIGN KEY → `airports.airport_code` | Destination airport code | From route destination IATA code |
| `tail_number` | TEXT(6) | FOREIGN KEY → `planes.tail_number` | Aircraft assigned to the flight | Synthetic; selected from the airline's planes |
| `price` | REAL | NOT NULL | Ticket price in Indonesian rupiah (IDR) | Synthetic; generated based on route distance/category |

The primary key is the composite pair **(`airline_code`, `flight_code`)**. This reflects real aviation usage: a flight code is only guaranteed to be unique within its airline, not globally across all airlines.

Flights are treated as **route catalogue entries**, so departure and arrival times are outside the current project scope.

---

### 4.5 `customers`
**Source:** Fully artificial. No real customer data is used.

| Attribute | Type | Key | Description | Source Detail |
|-----------|------|-----|-------------|---------------|
| `customer_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique customer identifier | Auto-generated |
| `first_name` | TEXT | NOT NULL | Customer first name | Synthetic Indonesian-style names |
| `last_name` | TEXT | NOT NULL | Customer last name | Synthetic |
| `email` | TEXT | UNIQUE NOT NULL | Login identifier for the simulated customer account | Synthetic unique emails |
| `phone` | TEXT | | Phone number in Indonesian format | Synthetic |
| `password` | TEXT | | Plain-text password for mock login simulation only | Static/simple demo values |

Plain-text passwords are used only for educational/demo purposes. A real system would store password hashes and enforce stronger authentication rules.

---

### 4.6 `bookings`
**Source:** Fully artificial – generated by linking customers and flights, then assigning seats and transaction dates.

| Attribute | Type | Key | Description | Source Detail |
|-----------|------|-----|-------------|---------------|
| `booking_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique booking identifier | Auto-generated |
| `airline_code` | TEXT(2) | COMPOSITE FOREIGN KEY → `flights(airline_code, flight_code)` | Airline code of the booked flight | Copied from selected flight |
| `flight_code` | TEXT(4) | COMPOSITE FOREIGN KEY → `flights(airline_code, flight_code)` | Flight code of the booked flight | Copied from selected flight |
| `seat_number` | TEXT(4) | UNIQUE with flight | Assigned seat, e.g., `12A` | Synthetic or selected during booking simulation |
| `customer_id` | INTEGER | FOREIGN KEY → `customers.customer_id` | Customer connected to the booking | Selected customer profile |
| `transaction_date` | DATE | NOT NULL | Date when the booking transaction was made | Synthetic or generated at booking time |

`bookings` references `flights` through the composite foreign key **(`airline_code`, `flight_code`) → `flights(airline_code, flight_code)`**.

#### Why `transaction_date` is included

`transaction_date` records **when the customer booking/payment action happened**. This is useful even though flights are not date-specific, because it supports:

- booking history;
- sorting recent bookings;
- basic sales reports by day or month;
- simple trend analysis for presentation insights.

This date represents the **booking/payment date**, not the flight departure date.

---

## 5. Typical Manager Workflow

1. The manager opens the dashboard.
2. The manager searches for available tickets by origin/destination airport search fields.
3. The map displays all candidate route paths and highlights routes with available tickets using curved flight arcs.
4. The manager selects one customer, selects one ticket, chooses an available seat, and creates a booking.
5. The manager checks the new booking in the database browser.
6. The manager optionally adds master data through controlled forms.
7. The manager runs SQL queries to answer analytical questions, such as:
   - Which routes have the most bookings?
   - Which airline has the most bookings?
   - What is the average ticket price by route?
   - How many bookings happened per transaction date?

This workflow keeps the GUI aligned with the database course requirements instead of pretending to be a complete real-world airline sales platform.

---

## 6. Data Pipeline Summary

| Step | Action | Input Files / Code | Output Table(s) |
|------|--------|--------------------|-----------------|
| 1 | Download raw OpenFlights data | `airports.dat`, `airlines.dat`, `routes.dat` | Raw source files |
| 2 | Filter for Indonesian airports, airlines, and domestic routes | `02_filter_indonesia.py` | `filtered/airports.csv`, `filtered/airlines.csv`, `filtered/routes.csv` |
| 3 | Prepare natural-key columns and generate synthetic values | `03_generate_synthetic_data.py` | generated `flight_code`, prices, planes, customers, bookings |
| 4 | Generate deterministic CSV outputs | `03_generate_synthetic_data.py` | `generated/planes.csv`, `generated/flights.csv`, `generated/customers.csv`, `generated/bookings.csv` |
| 5 | Create SQLite schema and import data | `04_create_database.py` | All 6 tables in `flight-booking.db` |
| 6 | Validate database integrity and sample analytical queries | `05_validate_database.py` | Row counts, foreign-key check, duplicate-seat check, sample insights |

---

## 7. Key Design Decisions

- **Manager-facing system:** The main system user is the manager/operator. Customer actions are simulated through the manager dashboard.
- **Natural IATA keys:** `airport_code` and `airline_code` use real aviation identifiers directly, making joins easier to read and closer to real-world flight data.
- **Composite flight identity:** Flights are identified by `airline_code` + `flight_code`, because flight codes are airline-specific.
- **Route-only flights:** No departure/arrival date or time columns are stored. Each flight row represents a reusable route catalogue entry.
- **`transaction_date` belongs in `bookings`:** It records when the customer booked or paid, without implying that the flight itself has a scheduled date.
- **`planes` table kept for 3NF:** Aircraft details such as type and seat count are stored once and referenced by flights through `tail_number`.
- **Latitude/longitude retained:** These support the GUI map and route visualizations.
- **Plain-text passwords are demo-only:** This is acceptable for a local classroom mock-up but not for a real production system.
