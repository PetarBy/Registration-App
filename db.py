import os
import mysql.connector
from mysql.connector import Error

DB_HOST     = os.getenv('DB_HOST', 'localhost')
DB_PORT     = int(os.getenv('DB_PORT', 3306))
DB_USER     = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME     = os.getenv('DB_NAME')

if not all((DB_USER, DB_PASSWORD, DB_NAME)):
    raise RuntimeError("Set DB_USER, DB_PASSWORD, and DB_NAME")

def get_connection():
    try:
        return mysql.connector.connect(
            host       = DB_HOST,
            port       = DB_PORT,
            user       = DB_USER,
            password   = DB_PASSWORD,
            database   = DB_NAME,
            charset    = 'utf8mb4',
            autocommit = False
        )
    except Error as err:
        print(f"DB connection error: {err}")
        raise
