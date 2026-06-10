import sqlite3

DATABASE_NAME = "database.db"


# ==========================
# DATABASE CONNECTION
# ==========================
def get_connection():

    conn = sqlite3.connect(DATABASE_NAME)

    conn.row_factory = sqlite3.Row

    return conn


# ==========================
# CREATE TABLES
# ==========================
def create_tables():

    conn = get_connection()

    cursor = conn.cursor()

    # ==========================
    # USERS TABLE
    # ==========================
    cursor.execute("""

    CREATE TABLE IF NOT EXISTS users (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        blood TEXT NOT NULL,

        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )

    """)

    # ==========================
    # DONORS TABLE
    # GPS ADDED
    # ==========================
    cursor.execute("""

    CREATE TABLE IF NOT EXISTS donors (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        blood TEXT NOT NULL,

        phone TEXT NOT NULL,
        location TEXT NOT NULL,

        latitude REAL,
        longitude REAL,

        last_date TEXT NOT NULL,
        status TEXT NOT NULL
    )

    """)

    # ==========================
    # PATIENTS TABLE
    # GPS ADDED
    # ==========================
    cursor.execute("""

    CREATE TABLE IF NOT EXISTS patients (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        blood TEXT NOT NULL,

        phone TEXT NOT NULL,
        location TEXT NOT NULL,

        latitude REAL,
        longitude REAL,

        units_required INTEGER NOT NULL,
        urgency TEXT NOT NULL
    )

    """)

    # ==========================
    # BLOOD REQUESTS TABLE
    # ==========================
    cursor.execute("""

    CREATE TABLE IF NOT EXISTS blood_requests (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        patient_name TEXT NOT NULL,
        patient_contact TEXT NOT NULL,

        donor_name TEXT NOT NULL,
        donor_contact TEXT NOT NULL,

        blood_group TEXT NOT NULL,

        status TEXT NOT NULL,
        request_date TEXT NOT NULL
    )

    """)

    conn.commit()

    conn.close()