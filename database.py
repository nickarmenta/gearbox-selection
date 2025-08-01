"""
This module handles all database interactions for the gearbox selection application.
It is responsible for creating the database and table, as well as populating it
with initial data.
"""
import sqlite3
from logging_config import logger
from models import Gearbox

def get_db_connection():
    """
    Establishes and returns a connection to the SQLite database.

    Returns:
        sqlite3.Connection: A connection object to the database.
    """
    conn = sqlite3.connect('gearboxes.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_gearbox_table():
    """
    Creates the 'gearboxes' table in the database if it does not already exist.
    The schema is designed to store parameters relevant for gearbox selection.
    """
    conn = get_db_connection()
    try:
        logger.info("Attempting to create 'gearboxes' table...")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS gearboxes (
                part_number TEXT PRIMARY KEY,
                supplier TEXT NOT NULL,
                output_interface TEXT NOT NULL,
                T_max_motor REAL NOT NULL,
                n_1N REAL NOT NULL,
                T2max_rated REAL NOT NULL,
                n2N_rated REAL NOT NULL,
                efficiency REAL NOT NULL,
                J_m REAL NOT NULL,
                F2rB REAL NOT NULL,
                F2aB REAL NOT NULL
            )
        ''')
        conn.commit()
        logger.info("'gearboxes' table created successfully or already exists.")
    except sqlite3.Error as e:
        logger.error(f"Database error while creating table: {e}")
    finally:
        conn.close()

def get_gearboxes_by_interface(output_interface: str) -> list[Gearbox]:
    """
    Fetches all gearboxes from the database that match the given output interface.

    Args:
        output_interface (str): The desired output interface ('Flange' or 'Shaft').

    Returns:
        list[Gearbox]: A list of Pydantic Gearbox models.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        logger.info(f"Fetching gearboxes with interface: {output_interface}")
        cursor.execute("SELECT * FROM gearboxes WHERE output_interface = ?", (output_interface,))
        rows = cursor.fetchall()
        # Pydantic can validate directly from dict-like objects (like sqlite.Row)
        gearboxes = [Gearbox.model_validate(dict(row)) for row in rows]
        logger.info(f"Found {len(gearboxes)} matching gearboxes.")
        return gearboxes
    except Exception as e:
        logger.error(f"Failed to fetch gearboxes: {e}")
        return []
    finally:
        conn.close()

def populate_initial_data():
    """
    Populates the 'gearboxes' table with a set of sample gearbox data.
    This function will not insert data if the part number already exists,
    preventing duplicate entries on subsequent runs.
    """
    sample_gearboxes = [
        ('APEX-AB042-010', 'APEX', 'Flange', 10, 6000, 20, 400, 0.97, 0.015, 800, 1600),
        ('APEX-AB060-010', 'APEX', 'Flange', 25, 6000, 50, 400, 0.97, 0.035, 1200, 2400),
        ('APEX-AB090-010', 'APEX', 'Flange', 70, 5000, 140, 350, 0.97, 0.120, 2500, 5000),
        ('APEX-AD140-010', 'APEX', 'Shaft', 180, 4000, 360, 250, 0.94, 0.450, 5000, 10000),
        ('APEX-AE205-010', 'APEX', 'Shaft', 450, 3000, 900, 150, 0.94, 1.5, 10000, 20000),
        ('WITTENSTEIN-NPL-025', 'WITTENSTEIN', 'Flange', 8, 8000, 15, 500, 0.96, 0.010, 700, 1400),
        ('WITTENSTEIN-NPL-035', 'WITTENSTEIN', 'Shaft', 20, 8000, 40, 500, 0.96, 0.025, 1000, 2000),
    ]

    conn = get_db_connection()
    try:
        logger.info("Populating database with initial sample gearboxes...")
        cursor = conn.cursor()
        for gearbox in sample_gearboxes:
            cursor.execute("SELECT 1 FROM gearboxes WHERE part_number = ?", (gearbox[0],))
            if cursor.fetchone() is None:
                cursor.execute('''
                    INSERT INTO gearboxes (part_number, supplier, output_interface, T_max_motor, n_1N, T2max_rated, n2N_rated, efficiency, J_m, F2rB, F2aB)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', gearbox)
        conn.commit()
        logger.info("Initial data population complete.")
    except sqlite3.Error as e:
        logger.error(f"Database error during data population: {e}")
    finally:
        conn.close()

def init_database():
    """
    Initializes the database by creating the table and populating it with data.
    This is the main entry point for database setup.
    """
    logger.info("Database initialization sequence started.")
    create_gearbox_table()
    populate_initial_data()
    logger.info("Database initialization sequence finished.") 