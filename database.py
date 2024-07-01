from importlib.resources import as_file
import sqlite3
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_db_connection(db_file):
    """Create and return a database connection."""
    try:
        conn = sqlite3.connect(db_file)
        logging.info(f"Connected to the database {db_file} successfully.")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database: {e}")
        return None

# Function to establish a connection to the SQLite database
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connected to SQLite database: {sqlite3.version}")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite database: {e}")

    return conn

# Function to create necessary tables if they don't exist
def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            price REAL NOT NULL,
            quantity REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cursor.close()

# Function to insert a trade into the 'trades' table
def insert_trade(conn, symbol, action, price, quantity):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO trades (symbol, action, price, quantity)
        VALUES (?, ?, ?, ?)
    ''', (symbol, action, price, quantity))
    conn.commit()
    cursor.close()

# Function to retrieve all trades from the 'trades' table
def get_all_trades(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trades')
    trades = cursor.fetchall()
    cursor.close()
    return trades

# Function to close the database connection
def close_connection(conn):
    if conn:
        conn.close()
        print("SQLite connection is closed")

# Example usage in your main script or wherever needed
'''if __name__ == '__main__':
    database_file = 'trading_bot.db'
    conn = create_connection(database_file)'''
    
# Now `conn` can be used to execute SQL queries or interact with the database
def create_table(conn, create_table_sql):
    """Create a table from the create_table_sql statement."""
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        logging.info("Table created successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error creating table: {e}")

def store_data_to_db(conn, df, table_name):
    """Store a DataFrame into a database table."""
    try:
        if conn:
            with conn:
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                logging.info(f"Data stored in table {table_name} successfully.")
        else:
            logging.error("Cannot store data: Database connection is closed or not established.")
    except Exception as e:
        logging.error(f"Error storing data to table {table_name}: {e}")

def fetch_historical_data(conn, table_name):
    """Fetch historical data from a database table into a DataFrame."""
    df = pd.DataFrame()  # Initialize an empty DataFrame for error handling
    try:
        if conn:
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql(query, conn)
            logging.info(f"Data fetched from table {table_name} successfully.")
        else:
            logging.error("Cannot fetch data: Database connection is closed or not established.")
    except Exception as e:
        logging.error(f"Error fetching data from table {table_name}: {e}")
    return df

def close_db_connection(conn):
    """Close the database connection."""
    try:
        if conn:
            conn.close()
            logging.info("Database connection closed.")
        else:
            logging.warning("Database connection already closed.")
    except Exception as e:
        logging.error(f"Error closing database connection: {e}")
        
def close_connection(conn):
    if conn:
        conn.close()
        print("SQLite connection is closed")
        
def init_db(db_file):
    """Initialize the database with the necessary tables."""
    conn = create_db_connection(db_file)
    if conn:
        historical_data_table = """
        CREATE TABLE IF NOT EXISTS historical_data (
            Date TEXT,
            Open REAL,
            High REAL,
            Low REAL,
            Close REAL,
            Volume INTEGER
        );
        """
        create_table(conn, historical_data_table)
        close_db_connection(conn)

# Example usage
if __name__ == "__main__":
    DB_FILE = 'trading_bot.db'
    TABLE_NAME = 'historical_data'
    
    # Create a database connection
    conn = create_db_connection(DB_FILE)
    
    if conn:
        # Example DataFrame
        data = {
            'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'Open': [100, 105, 102],
            'Close': [105, 102, 108]
        }
        df = pd.DataFrame(data)
        
    # Print the DataFrame
    print("Example DataFrame:")
    print(df)
    print()

    # Basic DataFrame operations
    # Indexing and selecting data
    print("Selected Date and Close price:")
    print(df[['Date', 'Close']])
    print()

    # Slicing rows
    print("First two rows:")
    print(df.head(2))
    print()

    # Filtering data
    print("Filtered rows where Close > 103:")
    filtered_df = df[df['Close'] > 103]
    print(filtered_df)
    print()

    # Aggregation
    print("Mean Open price:")
    mean_open = df['Open'].mean()
    print(mean_open)
    print()

# Handling missing data (not shown in example data)

# Time series analysis (not shown in example data)
        
# Example of integrating with your trading bot (hypothetical usage)
def analyze_market_data(df):
    # Example: Calculate moving average
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    return df

# Example usage in your trading bot
if __name__ == "__main__":
    # Assume df contains real market data fetched or stored elsewhere
    df = fetch_historical_data(conn, TABLE_NAME)  # Replace with actual data retrieval logic
    
    # Ensure df is not empty before analysis
    if not df.empty:
        df_analyzed = analyze_market_data(df)
        
        # Further analysis or strategy development
        # ...

        # Example: Plotting using matplotlib (not included here)

        # Save the DataFrame or results to a database or file
        # df_analyzed.to_sql('market_data', conn, if_exists='replace', index=False)

    else:
        logging.warning("DataFrame is empty or not properly fetched.")

    # Close database connections or clean up resources
    close_db_connection(conn)

    
    # Further analysis or strategy development
    # ...

    # Example: Plotting using matplotlib (not included here)

    # Save the DataFrame or results to a database or file
    # df_analyzed.to_sql('market_data', conn, if_exists='replace', index=False)

    # Close database connections or clean up resources

# Further exploration:
# - Pandas documentation: https://pandas.pydata.org/docs/
# - Tutorials on Pandas operations, time series analysis, and more.        
        
        # Store data to the database
    store_data_to_db(conn, df, TABLE_NAME)
        
    # Fetch data from the database
    historical_data = fetch_historical_data(conn, TABLE_NAME)
    print(historical_data)
        
    # Close the database connection
    close_db_connection(conn)
        
    # Initialize the database
    init_db(DB_FILE)
        
    def init_db(db_file):
    #"""Initialize the database with the necessary tables."""
            conn = create_db_connection(as_file)
            if conn:
                historical_data_table = """
                CREATE TABLE IF NOT EXISTS historical_data (
                    Date TEXT,
                    Open REAL,
                    High REAL,
                    Low REAL,
                    Close REAL,
                    Volume INTEGER
                );
                """
                create_table(conn, historical_data_table)
        
                # Close the database connection
                create_table(conn, historical_data_table)
                close_db_connection(conn)


