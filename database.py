import sqlite3
import os
import pandas as pd


class RailwayDatabase:

    def __init__(self, db_path="database/railway.db"):

        self.db_path = db_path

        os.makedirs(
            os.path.dirname(db_path),
            exist_ok=True
        )

        self.create_tables()

    # --------------------------------------------------
    # Connect to database
    # --------------------------------------------------

    def connect(self):
        return sqlite3.connect(self.db_path)

    # --------------------------------------------------
    # Create tables
    # --------------------------------------------------

    def create_tables(self):

        connection = self.connect()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_name TEXT UNIQUE NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                train_name TEXT,
                train_number TEXT,
                distance REAL,
                travel_time REAL,
                departure TEXT,
                arrival TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                optimization_type TEXT NOT NULL,
                route TEXT NOT NULL,
                total_distance REAL,
                total_time REAL
            )
        """)

        connection.commit()
        connection.close()

        print("Database tables created successfully.")

    # --------------------------------------------------
    # Import cleaned CSV into database
    # --------------------------------------------------

    def import_routes(self, csv_file="data/cleaned_routes.csv"):

        if not os.path.exists(csv_file):
            raise FileNotFoundError(
                f"CSV file not found: {csv_file}"
            )

        df = pd.read_csv(csv_file)

        connection = self.connect()
        cursor = connection.cursor()

        # Clear existing data before importing
        cursor.execute("DELETE FROM routes")
        cursor.execute("DELETE FROM stations")

        # Import stations
        stations = set()

        for _, row in df.iterrows():

            stations.add(row["source"])
            stations.add(row["destination"])

        for station in stations:

            cursor.execute("""
                INSERT OR IGNORE INTO stations (station_name)
                VALUES (?)
            """, (station,))

        # Import routes
        for _, row in df.iterrows():

            cursor.execute("""
                INSERT INTO routes (
                    source,
                    destination,
                    train_name,
                    train_number,
                    distance,
                    travel_time,
                    departure,
                    arrival
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["source"],
                row["destination"],
                row["train_name"],
                str(row["train_number"]),
                row["distance"],
                row["travel_time_min"],
                row["departure"],
                row["arrival"]
            ))

        connection.commit()
        connection.close()

        print("Routes imported successfully.")
        print("Records imported:", len(df))
        print("Stations imported:", len(stations))

    # --------------------------------------------------
    # Get all stations
    # --------------------------------------------------

    def get_stations(self):

        connection = self.connect()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT station_name
            FROM stations
            ORDER BY station_name
        """)

        stations = [
            row[0]
            for row in cursor.fetchall()
        ]

        connection.close()

        return stations

    # --------------------------------------------------
    # Get route count
    # --------------------------------------------------

    def get_route_count(self):

        connection = self.connect()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM routes
        """)

        count = cursor.fetchone()[0]

        connection.close()

        return count

    # --------------------------------------------------
    # Save optimization result
    # --------------------------------------------------

    def save_result(
        self,
        source,
        destination,
        optimization_type,
        route,
        total_distance,
        total_time
    ):

        connection = self.connect()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO optimization_results (
                source,
                destination,
                optimization_type,
                route,
                total_distance,
                total_time
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            source,
            destination,
            optimization_type,
            route,
            total_distance,
            total_time
        ))

        connection.commit()
        connection.close()


# ------------------------------------------------------
# Test database and import data
# ------------------------------------------------------

if __name__ == "__main__":

    database = RailwayDatabase()

    print("\n========================================")
    print("IMPORTING RAILWAY DATA")
    print("========================================")

    database.import_routes()

    print("\n========================================")
    print("DATABASE INFORMATION")
    print("========================================")

    print(
        "Number of stations:",
        len(database.get_stations())
    )

    print(
        "Number of routes:",
        database.get_route_count()
    )