import sqlite3

DATABASE_NAME = "database.db"

def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # USERS TABLE
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

    # DONORS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS donors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        blood TEXT NOT NULL,
        phone TEXT NOT NULL,
        location TEXT NOT NULL,
        last_date TEXT NOT NULL,
        status TEXT NOT NULL
    )
    """)

    # PATIENTS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        blood TEXT NOT NULL,
        phone TEXT NOT NULL,
        location TEXT NOT NULL,
        units_required INTEGER NOT NULL,
        urgency TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()





