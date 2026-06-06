import sqlite3

def init_database():
    # This creates the database file if it doesn't exist and opens a connection
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # 1. Create the Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        body_profile TEXT DEFAULT NULL
    );
    """)

    # 2. Create the Clothes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clothes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        image_url TEXT,
        category TEXT NOT NULL,
        color TEXT,
        formality INTEGER,
        weather_tags TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)

    # 3. Create the Outfit Logs Table (The Tracker)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS outfit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        wear_date TEXT NOT NULL,
        clothing_ids TEXT NOT NULL,
        context TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)

    # Save changes and close the connection
    connection.commit()
    connection.close()
    print("🚀 Database initialized successfully! 'database.db' created.")

if __name__ == "__main__":
    init_database()