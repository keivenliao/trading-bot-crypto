import sqlite3
import pandas as pd

def create_db_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn

def store_data_to_db(conn, df, table_name):
    df.to_sql(table_name, conn, if_exists='replace', index=False)

def fetch_historical_data(conn, table_name):
    query = f"SELECT * FROM {table_name}"
    return pd.read_sql(query, conn)
