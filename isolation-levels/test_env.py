import mysql.connector


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "isolation_lab"
}


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Creates and returns a new MySQL database connection.

    Each transaction must use its own connection.
    """

    return mysql.connector.connect(**DB_CONFIG)