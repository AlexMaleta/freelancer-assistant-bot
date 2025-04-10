import sqlite3

from config.config import db_path

DB_PATH = db_path

def get_connection():
    return sqlite3.connect(DB_PATH)