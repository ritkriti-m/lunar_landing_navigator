import sqlite3
import pandas as pd
import os

def build_database():
    print("Starting data ingestion...")
    
    # 1. Load the real CSV files provided by the data team
    sun_df = pd.read_csv(os.path.join("data", "HW10_solar_positions.csv"))
    earth_df = pd.read_csv(os.path.join("data", "HW10_earth_visibility.csv"))
    
    # 2. Merge them on the timestamp (UTC)
    sun_df = sun_df.rename(columns={'UTC': 'timestamp', 'Solar elevation (degrees)': 'sun_elevation'})
    earth_df = earth_df.rename(columns={'UTC': 'timestamp', 'Earth elevation (degrees)': 'earth_elevation'})
    
    merged_ephem = pd.merge(
        sun_df[['timestamp', 'sun_elevation']], 
        earth_df[['timestamp', 'earth_elevation']], 
        on='timestamp'
    )
    
    # 3. Transcribe the real target sites with sunlight illumination percentages
    topo_data = [
        {"site": "HW01", "latitude": -86.768, "longitude": -20.514, "elevation": -4100, "illumination": 42.10},
        {"site": "HW02", "latitude": -86.808, "longitude": -21.719, "elevation": -4100, "illumination": 38.50},
        {"site": "HW03", "latitude": -86.860, "longitude": -19.893, "elevation": -4100, "illumination": 41.20},
        {"site": "HW04", "latitude": -86.568, "longitude": -21.473, "elevation": -4100, "illumination": 39.00},
        {"site": "HW05", "latitude": -86.662, "longitude": -30.548, "elevation": -4100, "illumination": 45.30},
        {"site": "HW06", "latitude": -87.050, "longitude": -24.240, "elevation": -4100, "illumination": 37.80},
        {"site": "HW07", "latitude": -86.932, "longitude": -23.020, "elevation": -4100, "illumination": 40.40},
        {"site": "HW08", "latitude": -86.924, "longitude": -25.809, "elevation": -4100, "illumination": 36.90},
        {"site": "HW09", "latitude": -86.623, "longitude": -26.075, "elevation": -4100, "illumination": 43.70},
        {"site": "HW10", "latitude": -86.527, "longitude": -14.876, "elevation": -4100, "illumination": 34.86}, # True HW10 sunlight fraction
        {"site": "HW_K2023", "latitude": -86.990, "longitude": -24.254, "elevation": -4100, "illumination": 44.20}
    ]
    topo_df = pd.DataFrame(topo_data)

    # 4. Create and populate the SQLite database
    os.makedirs('data', exist_ok=True)
    db_path = os.path.join('data', 'haworth.db')
    conn = sqlite3.connect(db_path)
    
    merged_ephem.to_sql('ephemeris', conn, if_exists='replace', index=False)
    topo_df.to_sql('topography', conn, if_exists='replace', index=False)
    
    conn.close()
    print(f"✅ Successfully ingested {len(merged_ephem)} timeline records and {len(topo_df)} surface coordinates into {db_path}!")

if __name__ == "__main__":
    build_database()