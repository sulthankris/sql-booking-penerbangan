# Gambaran Umum Proyek – Database Penjualan Tiket Penerbangan Domestik Indonesia dan Dashboard Manajer

## Daftar Isi

1. [Ringkasan Proyek](#1-ringkasan-proyek)
2. [Latar Belakang, Tujuan, dan Peran Pengguna](#2-latar-belakang-tujuan-dan-peran-pengguna)
   - [2.1 Latar Belakang](#21-latar-belakang)
   - [2.2 Tujuan Proyek](#22-tujuan-proyek)
   - [2.3 Peran Pengguna Sistem](#23-peran-pengguna-sistem)
3. [Sumber Data dan Pipeline Reproducible](#3-sumber-data-dan-pipeline-reproducible)
   - [3.1 Sumber Data Nyata](#31-sumber-data-nyata)
   - [3.2 Data Sintetis](#32-data-sintetis)
   - [3.3 Urutan Script Data](#33-urutan-script-data)
4. [Rancangan Database](#4-rancangan-database)
   - [4.1 Entitas dan Relasi](#41-entitas-dan-relasi)
   - [4.2 Struktur Tabel Relasional](#42-struktur-tabel-relasional)
   - [4.3 Constraint dan Keputusan Desain](#43-constraint-dan-keputusan-desain)
5. [Implementasi Menggunakan SQL](#5-implementasi-menggunakan-sql)
   - [5.1 Pembuatan Tabel](#51-pembuatan-tabel)
   - [5.2 Import Data dengan INSERT](#52-import-data-dengan-insert)
   - [5.3 Contoh Kueri Analitik](#53-contoh-kueri-analitik)
6. [Implementasi GUI Sederhana](#6-implementasi-gui-sederhana)
   - [6.1 Teknologi GUI](#61-teknologi-gui)
   - [6.2 Struktur Tab GUI](#62-struktur-tab-gui)
   - [6.3 Peta Rute](#63-peta-rute)
7. [Skenario Demo Website](#7-skenario-demo-website)
   - [7.1 Tambah Customer](#71-tambah-customer)
   - [7.2 Tambah Booking](#72-tambah-booking)
   - [7.3 Database Browser](#73-database-browser)
   - [7.4 Manajemen Data](#74-manajemen-data)
   - [7.5 Query Database dan Custom Query](#75-query-database-dan-custom-query)
8. [Testing](#8-testing)
   - [8.1 Testing Pipeline Data](#81-testing-pipeline-data)
   - [8.2 Testing Constraint Database](#82-testing-constraint-database)
   - [8.3 Testing GUI](#83-testing-gui)
   - [8.4 Testing Deployment](#84-testing-deployment)
9. [Kesimpulan dan Insight](#9-kesimpulan-dan-insight)
10. [Lampiran Referensi File](#10-lampiran-referensi-file)

---

## 1. Ringkasan Proyek

Proyek ini membangun **database relasional penjualan tiket penerbangan domestik Indonesia** dengan GUI sederhana berbasis Streamlit. Sistem ini digunakan sebagai **dashboard manajer/operator**, bukan sebagai website pelanggan publik yang lengkap.

Fokus proyek:

- merancang database dengan minimal 5 entitas;
- membuat implementasi SQLite dengan `CREATE TABLE`, `INSERT`, `PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE`, dan `CHECK`;
- menyediakan GUI untuk melihat, mencari, memfilter, menambahkan record, dan menjalankan query;
- melakukan testing terhadap query, constraint, dan alur GUI;
- menghasilkan insight sederhana dari data penerbangan dan pemesanan.

Database akhir bernama:

```text
flight-booking.db
```

Jumlah tabel utama:

| Tabel | Fungsi |
|-------|--------|
| `airports` | Data bandara Indonesia. |
| `airlines` | Data maskapai. |
| `planes` | Data pesawat dan kapasitas kursi. |
| `flights` | Data katalog rute penerbangan dan harga. |
| `customers` | Data pelanggan sintetis. |
| `bookings` | Data transaksi pemesanan tiket. |

Jumlah data pada seed database:

| Tabel | Jumlah Baris |
|-------|--------------|
| `airports` | 136 |
| `airlines` | 6 |
| `planes` | 71 |
| `flights` | 577 |
| `customers` | 300 |
| `bookings` | 900 |

---

## 2. Latar Belakang, Tujuan, dan Peran Pengguna

### 2.1 Latar Belakang

Penerbangan domestik Indonesia melibatkan banyak bandara, maskapai, pesawat, rute, pelanggan, dan transaksi tiket. Jika data tersebut disimpan dalam file terpisah, proses pencarian, validasi, dan analisis akan sulit dilakukan.

Database relasional cocok untuk studi kasus ini karena:

- setiap objek utama dapat disimpan dalam tabel yang jelas;
- relasi antarobjek dapat dijaga menggunakan primary key dan foreign key;
- data dapat difilter, digabungkan, dikelompokkan, dan dianalisis menggunakan SQL;
- GUI sederhana dapat dibuat untuk mempermudah demonstrasi query dan pemesanan.

Dataset terbuka yang lengkap untuk jadwal penerbangan Indonesia, harga tiket, data pelanggan, dan pemesanan sulit diperoleh. Oleh karena itu, proyek ini menggabungkan data nyata dan data sintetis.

### 2.2 Tujuan Proyek

Tujuan proyek ini adalah:

1. Merancang database relasional untuk penjualan tiket penerbangan domestik Indonesia.
2. Mengimplementasikan skema database SQLite berdasarkan ERD dan tabel relasional.
3. Mengisi database dengan gabungan data nyata dan data sintetis yang reproducible.
4. Menyediakan GUI sederhana untuk menambah data, menampilkan data, mencari/memfilter data, dan menampilkan hasil query.
5. Menyusun minimal 8 query SQL yang mencakup `SELECT ... WHERE`, `JOIN`, `GROUP BY`, `ORDER BY`, dan fungsi agregat.
6. Melakukan testing terhadap query, constraint database, dan alur GUI.
7. Menghasilkan insight sederhana dari hasil query.

### 2.3 Peran Pengguna Sistem

Pengguna utama sistem adalah **manajer/operator**.

Klarifikasi penting:

- pelanggan bukan pengguna utama GUI;
- pelanggan adalah subjek data dalam simulasi;
- manajer dapat mensimulasikan alur pelanggan seperti tambah pelanggan, cari tiket, dan buat booking;
- manajer juga dapat melihat tabel database, menambah data master, dan menjalankan query SQL.

Alasan framing ini digunakan:

- fitur database browser dan custom SQL tidak realistis untuk pelanggan umum;
- tugas mini project memang membutuhkan demonstrasi database, SQL, GUI, testing, dan insight;
- dashboard manajer membuat fitur administrasi dan analisis menjadi masuk akal.

---

## 3. Sumber Data dan Pipeline Reproducible

### 3.1 Sumber Data Nyata

Data nyata berasal dari **OpenFlights**:

| File | Digunakan Untuk |
|------|-----------------|
| `airports.dat` | Metadata bandara, kota, negara, kode IATA, latitude, longitude. |
| `airlines.dat` | Metadata maskapai dan kode IATA maskapai. |
| `routes.dat` | Struktur rute penerbangan dari bandara asal ke bandara tujuan. |

Data OpenFlights difilter agar hanya memuat konteks Indonesia:

- `airports`: hanya bandara dengan `country = 'Indonesia'` dan IATA valid;
- `airlines`: maskapai Indonesia yang digunakan dalam rute domestik;
- `routes`: hanya rute domestik Indonesia dengan bandara asal dan tujuan yang valid.

### 3.2 Data Sintetis

Data sintetis dibuat karena data pelanggan, transaksi booking, nomor kursi, harga tiket, dan penugasan pesawat tidak tersedia lengkap secara terbuka.

Data sintetis yang dibuat:

| Data | Cara Pembuatan |
|------|----------------|
| Pesawat | Berdasarkan tipe pesawat umum di armada Indonesia, seperti Boeing 737 dan Airbus A320. |
| `tail_number` | Mengikuti pola registrasi pesawat Indonesia, misalnya `PK-GAA`. |
| `flight_code` | Dibuat per maskapai sehingga identitas penerbangan adalah `airline_code + flight_code`. |
| Harga tiket | Dibuat berdasarkan estimasi jarak rute dengan variasi harga. |
| Customers | Nama, email, telepon, dan password demo dibuat sintetis. |
| Bookings | Dibuat dengan menghubungkan customer dan flight, lalu memilih kursi dan tanggal transaksi. |

Script data sintetis menggunakan seed tetap:

```python
SEED = 20260521
```

Seed tetap membuat output data dapat diulang untuk laporan dan presentasi.

### 3.3 Urutan Script Data

Pipeline dibuat dalam file Python bernomor agar mudah dijelaskan di laporan.

| Urutan | File | Fungsi | Output |
|--------|------|--------|--------|
| 1 | `01_download.py` | Mengunduh data OpenFlights. | `raw_data/airports.dat`, `raw_data/airlines.dat`, `raw_data/routes.dat` |
| 2 | `02_filter_indonesia.py` | Memfilter bandara, maskapai, dan rute Indonesia. | `filtered/airports.csv`, `filtered/airlines.csv`, `filtered/routes.csv` |
| 3 | `03_generate_synthetic_data.py` | Membuat data sintetis deterministik. | `generated/planes.csv`, `generated/flights.csv`, `generated/customers.csv`, `generated/bookings.csv` |
| 4 | `04_create_database.py` | Membuat skema SQLite dan mengisi data. | `flight-booking.db` |
| 5 | `05_validate_database.py` | Melakukan validasi database dan contoh query analitik. | Output testing di terminal |

Perintah untuk menjalankan ulang pipeline:

```powershell
python 01_download.py
python 02_filter_indonesia.py
python 03_generate_synthetic_data.py
python 04_create_database.py
python 05_validate_database.py
```

---

## 4. Rancangan Database

### 4.1 Entitas dan Relasi

Database terdiri dari 6 entitas utama:

| Entitas | Primary Key | Relasi Utama |
|---------|-------------|--------------|
| `airports` | `airport_code` | Direferensikan oleh `flights.origin_airport_code` dan `flights.dest_airport_code`. |
| `airlines` | `airline_code` | Direferensikan oleh `planes.owner_airline` dan `flights.airline_code`. |
| `planes` | `tail_number` | Direferensikan oleh `flights.tail_number`. |
| `flights` | `airline_code + flight_code` | Direferensikan oleh `bookings.airline_code + bookings.flight_code`. |
| `customers` | `customer_id` | Direferensikan oleh `bookings.customer_id`. |
| `bookings` | `booking_id` | Menghubungkan customer dengan flight yang dipesan. |

Relasi utama:

- satu maskapai memiliki banyak pesawat;
- satu maskapai mengoperasikan banyak flight;
- satu bandara dapat menjadi asal banyak flight;
- satu bandara dapat menjadi tujuan banyak flight;
- satu pesawat dapat ditugaskan ke banyak flight dalam katalog;
- satu customer dapat memiliki banyak booking;
- satu flight dapat memiliki banyak booking selama kursinya berbeda.

### 4.2 Struktur Tabel Relasional

#### `airports`

| Atribut | Tipe | Kunci | Keterangan |
|---------|------|-------|------------|
| `airport_code` | TEXT(3) | PK | Kode IATA bandara. |
| `airport_name` | TEXT | NOT NULL | Nama bandara. |
| `city` | TEXT | | Kota bandara. |
| `latitude` | REAL | | Koordinat untuk peta. |
| `longitude` | REAL | | Koordinat untuk peta. |

#### `airlines`

| Atribut | Tipe | Kunci | Keterangan |
|---------|------|-------|------------|
| `airline_code` | TEXT(2) | PK | Kode IATA maskapai. |
| `airline_name` | TEXT | NOT NULL | Nama maskapai. |

#### `planes`

| Atribut | Tipe | Kunci | Keterangan |
|---------|------|-------|------------|
| `tail_number` | TEXT(6) | PK | Nomor registrasi pesawat. |
| `aircraft_type` | TEXT | NOT NULL | Tipe pesawat. |
| `total_seats` | INTEGER | CHECK | Jumlah kursi, harus lebih dari 0. |
| `owner_airline` | TEXT(2) | FK | Referensi ke `airlines.airline_code`. |

#### `flights`

| Atribut | Tipe | Kunci | Keterangan |
|---------|------|-------|------------|
| `airline_code` | TEXT(2) | PK, FK | Maskapai penerbangan. |
| `flight_code` | TEXT(4) | PK | Kode penerbangan dalam maskapai. |
| `origin_airport_code` | TEXT(3) | FK | Bandara asal. |
| `dest_airport_code` | TEXT(3) | FK | Bandara tujuan. |
| `tail_number` | TEXT(6) | FK | Pesawat yang digunakan. |
| `price` | REAL | CHECK | Harga tiket, minimal 0. |

Primary key `flights` adalah komposit: **(`airline_code`, `flight_code`)**.

#### `customers`

| Atribut | Tipe | Kunci | Keterangan |
|---------|------|-------|------------|
| `customer_id` | INTEGER | PK AUTOINCREMENT | ID pelanggan. |
| `first_name` | TEXT | NOT NULL | Nama depan. |
| `last_name` | TEXT | NOT NULL | Nama belakang. |
| `email` | TEXT | UNIQUE, NOT NULL | Email login simulasi. |
| `phone` | TEXT | | Nomor telepon. |
| `password` | TEXT | | Password demo. |

Catatan: password disimpan plain text hanya untuk demo lokal, bukan praktik produksi.

#### `bookings`

| Atribut | Tipe | Kunci | Keterangan |
|---------|------|-------|------------|
| `booking_id` | INTEGER | PK AUTOINCREMENT | ID booking. |
| `airline_code` | TEXT(2) | FK komposit | Bagian dari referensi ke `flights`. |
| `flight_code` | TEXT(4) | FK komposit | Bagian dari referensi ke `flights`. |
| `seat_number` | TEXT(4) | UNIQUE per flight | Nomor kursi. |
| `customer_id` | INTEGER | FK | Referensi ke customer. |
| `transaction_date` | DATE | NOT NULL | Tanggal transaksi booking. |

### 4.3 Constraint dan Keputusan Desain

Constraint penting:

| Constraint | Tujuan |
|------------|--------|
| `PRIMARY KEY (airline_code, flight_code)` pada `flights` | Flight code hanya unik dalam maskapai, bukan global. |
| `FOREIGN KEY (airline_code, flight_code)` pada `bookings` | Booking harus mengacu ke flight yang valid. |
| `UNIQUE (airline_code, flight_code, seat_number)` | Kursi yang sama tidak boleh dipesan dua kali pada flight yang sama. |
| `CHECK (origin_airport_code <> dest_airport_code)` | Flight tidak boleh memiliki asal dan tujuan yang sama. |
| `CHECK (total_seats > 0)` | Pesawat harus memiliki kursi. |
| `CHECK (price >= 0)` | Harga tiket tidak boleh negatif. |
| `email UNIQUE` | Email customer tidak boleh duplikat. |

Keputusan desain utama:

- menggunakan natural key `airport_code` dan `airline_code` agar join mudah dibaca;
- menyimpan `transaction_date` di `bookings` sebagai tanggal transaksi, bukan tanggal keberangkatan;
- tidak menyimpan jadwal keberangkatan karena `flights` diposisikan sebagai katalog rute;
- mempertahankan `latitude` dan `longitude` untuk visualisasi peta.

---

## 5. Implementasi Menggunakan SQL

### 5.1 Pembuatan Tabel

Implementasi skema berada di `04_create_database.py` pada variabel `SCHEMA_SQL`.

Contoh potongan `CREATE TABLE` untuk `flights`:

```sql
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
```

Contoh potongan `CREATE TABLE` untuk `bookings`:

```sql
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
```

### 5.2 Import Data dengan INSERT

Data dari CSV dimasukkan ke SQLite menggunakan fungsi `insert_rows()` di `04_create_database.py`.

Pola umumnya:

```python
sql = f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})"
conn.executemany(sql, ([row[column] for column in columns] for row in rows))
```

Contoh import `flights`:

```python
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
```

### 5.3 Contoh Kueri Analitik

GUI menyediakan minimal 8 query yang dapat digunakan untuk presentasi.

| No. | Kueri | Konsep SQL |
|-----|-------|------------|
| 1 | Penerbangan dari `CGK` ke `DPS` | `SELECT`, `WHERE`, `JOIN`, `ORDER BY` |
| 2 | Riwayat pemesanan pelanggan | `JOIN` `bookings`, `customers`, `flights` |
| 3 | Jumlah booking per maskapai | `GROUP BY`, `COUNT` |
| 4 | Jumlah booking per rute | `JOIN`, `GROUP BY`, `COUNT` |
| 5 | Harga rata-rata per rute | `AVG`, `MIN`, `MAX`, `GROUP BY` |
| 6 | Penerbangan paling mahal | `ORDER BY price DESC` |
| 7 | Penerbangan paling murah | `ORDER BY price ASC` |
| 8 | Booking berdasarkan tanggal transaksi | `GROUP BY transaction_date`, `COUNT` |

Contoh query jumlah booking per rute:

```sql
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
LIMIT 20;
```

Contoh query harga rata-rata per rute:

```sql
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
LIMIT 20;
```

---

## 6. Implementasi GUI Sederhana

### 6.1 Teknologi GUI

GUI dibuat menggunakan Python dengan library berikut:

| Teknologi | Peran |
|-----------|-------|
| Streamlit | Membuat antarmuka web sederhana dengan widget Python. |
| sqlite3 | Menghubungkan Python ke database SQLite. |
| Pandas | Menampung hasil query dalam bentuk DataFrame agar mudah ditampilkan. |
| PyDeck | Menampilkan peta bandara dan jalur rute penerbangan. |

Prinsip implementasi GUI:

- sederhana seperti logika Jupyter, tetapi ditampilkan sebagai web app;
- tidak menggunakan Flask/Django;
- tidak menggunakan HTML/CSS/JavaScript manual;
- tidak menggunakan ORM;
- query SQL tetap terlihat dan dapat dijelaskan.

### 6.2 Struktur Tab GUI

GUI memiliki tab berikut:

| Tab | Fungsi |
|-----|--------|
| `Tambah Pemesanan` | Mencari tiket, memilih customer, memilih kursi, dan membuat booking. |
| `Database` | Melihat tabel dalam tampilan mentah atau terbaca, memfilter data, dan melihat query SQL. |
| `Manajemen Data` | Menambah data master seperti airlines, airports, planes, dan flights. |
| `Tambah Pelanggan` | Menambahkan customer baru. |
| `Query Database` | Menjalankan query analitik yang disiapkan dan custom `SELECT`. |
| `Overview` | Ringkasan jumlah baris dan alur demo. |

### 6.3 Peta Rute

Peta digunakan pada tab yang berkaitan dengan rute:

- `Tambah Pemesanan`;
- `Query Database` jika hasil query memiliki `origin_airport_code` dan `dest_airport_code`.

Komponen peta:

| Elemen | Implementasi |
|--------|--------------|
| Titik bandara | `ScatterplotLayer` dari PyDeck. |
| Jalur rute | `ArcLayer` dari PyDeck. |
| Tooltip rute | Menampilkan format seperti `CGK → DPS`. |
| Jalur abu-abu | Pasangan bandara kandidat dari pencarian. |
| Jalur biru | Rute dengan tiket tersedia. |
| Jalur oranye | Rute tiket yang sedang dipilih. |

---

## 7. Skenario Demo Website

### 7.1 Tambah Customer

Alur demo:

1. Buka tab `Tambah Pelanggan`.
2. Isi `first_name`, `last_name`, `email`, `phone`, dan `password`.
3. Klik tombol tambah customer.
4. Tunjukkan customer baru pada tabel `Latest Customers`.

Constraint yang ditunjukkan:

- `first_name`, `last_name`, dan `email` wajib diisi;
- `email` harus unik.

### 7.2 Tambah Booking

Alur demo:

1. Buka tab `Tambah Pemesanan`.
2. Cari customer melalui nama, email, atau ID.
3. Cari bandara asal, misalnya `jakarta`.
4. Cari bandara tujuan, misalnya `denpasar` atau `pe`.
5. Pilih hasil pencarian bandara atau gunakan opsi semua bandara yang cocok.
6. Lihat kartu tiket yang tersedia.
7. Pilih satu tiket.
8. Pilih kursi dari dropdown kursi tersedia.
9. Pilih `transaction_date`.
10. Klik tombol buat booking.
11. Tunjukkan booking baru pada `Latest Bookings` atau tab `Database`.

Constraint yang ditunjukkan:

- booking harus mengacu ke customer yang valid;
- booking harus mengacu ke flight yang valid;
- kursi yang sama tidak dapat dipesan dua kali untuk flight yang sama;
- `transaction_date` wajib ada.

### 7.3 Database Browser

Fitur yang dapat didemokan:

- memilih tabel `airports`, `airlines`, `planes`, `flights`, `customers`, atau `bookings`;
- memilih `Tampilan Mentah` untuk melihat data asli;
- memilih `Tampilan Terbaca` untuk melihat data hasil join;
- menggunakan filter spesifik tabel;
- melihat metadata tabel seperti primary key, foreign key, dan constraint;
- melihat query SQL yang digunakan;
- melihat pemeriksaan database.

### 7.4 Manajemen Data

Tab `Manajemen Data` digunakan untuk menambahkan data master secara terkontrol.

Data yang dapat ditambahkan:

- `airlines`;
- `airports`;
- `planes`;
- `flights`.

Setiap form menampilkan constraint yang relevan. Contoh untuk `flights`:

- `airline_code + flight_code` adalah composite primary key;
- `airline_code`, `origin_airport_code`, `dest_airport_code`, dan `tail_number` harus sudah ada;
- origin dan destination tidak boleh sama;
- `price` tidak boleh negatif;
- `tail_number` harus sesuai dengan maskapai yang dipilih.

### 7.5 Query Database dan Custom Query

Tab `Query Database` mendemonstrasikan:

- query analitik yang sudah disiapkan;
- tampilan SQL query melalui expander;
- custom query yang dibatasi hanya untuk satu statement `SELECT`;
- peta rute otomatis jika hasil query memiliki kolom asal dan tujuan bandara.

Contoh custom query aman:

```sql
SELECT *
FROM flights
WHERE origin_airport_code = 'CGK'
ORDER BY price ASC
LIMIT 10;
```

Custom query dibatasi hanya `SELECT` agar demo tidak merusak data dengan `DELETE`, `UPDATE`, atau `DROP TABLE`.

---

## 8. Testing

### 8.1 Testing Pipeline Data

Testing pipeline dilakukan dengan menjalankan semua script secara berurutan:

```powershell
python 01_download.py
python 02_filter_indonesia.py
python 03_generate_synthetic_data.py
python 04_create_database.py
python 05_validate_database.py
```

Output yang diharapkan:

- semua CSV berhasil dibuat;
- `flight-booking.db` berhasil dibuat;
- jumlah baris sesuai;
- validasi foreign key berhasil;
- tidak ada duplikasi kursi pada flight yang sama;
- query analitik contoh berhasil dijalankan.

### 8.2 Testing Constraint Database

Testing constraint dilakukan melalui `05_validate_database.py` dan fitur `Database checks` di GUI.

Pemeriksaan yang dilakukan:

| Pemeriksaan | Rule yang Diuji |
|-------------|-----------------|
| Foreign key check | Semua nilai FK harus memiliki parent key yang valid. |
| Duplicate booked seats | `UNIQUE(airline_code, flight_code, seat_number)`. |
| Same origin/destination | `CHECK(origin_airport_code <> dest_airport_code)`. |
| Invalid airport codes | `airport_code` tidak boleh null, kosong, atau `\N`. |
| Invalid airline codes | `airline_code` tidak boleh null, kosong, atau `\N`. |

### 8.3 Testing GUI

Skenario testing GUI:

| Fitur | Skenario | Hasil yang Diharapkan |
|-------|----------|-----------------------|
| Tambah Pelanggan | Input customer dengan email baru. | Customer masuk ke tabel `customers`. |
| Tambah Pelanggan | Input email yang sudah ada. | Sistem menolak karena email harus unik. |
| Tambah Booking | Pilih customer, ticket, seat, dan tanggal. | Booking masuk ke tabel `bookings`. |
| Tambah Booking | Pilih kursi yang sudah dipesan. | Kursi tidak tersedia di dropdown atau ditolak constraint. |
| Database Browser | Filter `flights` berdasarkan asal/tujuan. | Data yang tampil sesuai filter. |
| Manajemen Data | Tambah flight dengan airport tidak valid. | Sistem menampilkan error foreign key/validasi. |
| Query Database | Jalankan query prepared. | Hasil query tampil. |
| Custom Query | Jalankan `SELECT`. | Hasil query tampil. |
| Custom Query | Jalankan `DELETE` atau `DROP`. | Query ditolak karena bukan `SELECT`. |

### 8.4 Testing Deployment

Deployment menggunakan Render free tier.

File deployment:

| File | Fungsi |
|------|--------|
| `render.yaml` | Konfigurasi Render Blueprint. |
| `runtime.txt` | Versi Python untuk Render. |
| `requirements.txt` | Dependensi Python. |
| `flight-booking.db` | Database SQLite yang dipakai app. |

Start command Render:

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```

Catatan deployment:

- Render free tier dapat sleep saat tidak aktif;
- insert GUI pada SQLite bersifat demo dan dapat reset setelah redeploy;
- seed database tetap reproducible dari script bernomor.

---

## 9. Kesimpulan dan Insight

### Kesimpulan terhadap Tujuan

Proyek ini memenuhi tujuan utama mini project database:

1. Database relasional berhasil dirancang dengan 6 entitas yang saling berelasi.
2. Skema SQLite berhasil dibuat dengan primary key, foreign key, unique constraint, dan check constraint.
3. Data berhasil disusun dari gabungan OpenFlights dan data sintetis yang dapat direproduksi.
4. GUI sederhana berhasil dibuat menggunakan Streamlit untuk menambah record, menampilkan data, memfilter data, dan menjalankan query.
5. Minimal 8 query SQL tersedia dan mencakup filtering, join, grouping, ordering, dan agregasi.
6. Testing dilakukan melalui script validasi, database checks, dan skenario GUI.
7. Data dapat menghasilkan insight sederhana untuk mendukung analisis.

### Contoh Insight yang Dapat Dibahas

Insight yang dapat diambil dari query:

- rute dengan booking terbanyak menunjukkan pasangan kota/bandara yang paling sering dipilih dalam data simulasi;
- jumlah booking per maskapai menunjukkan maskapai yang paling dominan pada data booking;
- harga rata-rata per rute dapat digunakan untuk melihat rute yang relatif mahal atau murah;
- booking berdasarkan tanggal transaksi dapat menunjukkan pola transaksi harian;
- hasil query termurah/termahal membantu membandingkan variasi harga antar rute.

### Batasan Proyek

Batasan yang perlu dijelaskan saat presentasi:

- data booking dan customer bersifat sintetis, bukan data nyata;
- `flights` adalah katalog rute, bukan jadwal penerbangan tanggal tertentu;
- password plain text hanya untuk demo edukasi;
- deployment Render free tier tidak ditujukan untuk penyimpanan data permanen;
- GUI dibuat sederhana untuk memenuhi kebutuhan tugas, bukan sistem produksi.

---

## 10. Lampiran Referensi File

| File | Fungsi dalam Proyek |
|------|---------------------|
| `01_download.py` | Mengunduh data OpenFlights. |
| `02_filter_indonesia.py` | Memfilter data Indonesia dan membersihkan kode IATA. |
| `03_generate_synthetic_data.py` | Membuat data sintetis deterministic. |
| `04_create_database.py` | Membuat skema SQLite dan mengisi semua tabel. |
| `05_validate_database.py` | Melakukan testing database dan query contoh. |
| `app.py` | Implementasi GUI Streamlit. |
| `flight-booking.db` | Database akhir yang digunakan GUI. |
| `requirements.txt` | Library Python untuk menjalankan app. |
| `render.yaml` | Konfigurasi deployment Render. |
| `gui-plan-ID.md` | Penjelasan desain GUI. |
| `project-overview-ID.md` | Dokumen gambaran umum proyek dan referensi presentasi. |
