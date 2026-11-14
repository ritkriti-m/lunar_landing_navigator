import sqlite3
import os

def create_database():
    # Make sure the data folder exists before we put a database in it
    os.makedirs('data', exist_ok=True)
    
    # Connect to (and create) the SQLite database file
    db_path = os.path.join('data', 'haworth.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Table 1: Topography (To store the LOLA terrain elevation data)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS topography (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        elevation REAL NOT NULL
    )
    ''')

    # Table 2: Ephemeris (To store the JPL Horizons time, Sun, and Earth data)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ephemeris (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        sun_azimuth REAL,
        sun_elevation REAL,
        earth_azimuth REAL,
        earth_elevation REAL
    )
    ''')

    # Save changes and close the connection
    conn.commit()
    conn.close()
    
    print(f"Success! Database created at {db_path} with Topography and Ephemeris tables.")

if __name__ == '__main__':
    create_database()