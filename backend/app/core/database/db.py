import mysql.connector
from mysql.connector import pooling
import time
from app.core.config.config_manager import config_manager

class DatabaseManager:
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_pool()
        return cls._instance

    def _init_pool(self):
        """Initialize the connection pool."""
        db_config = config_manager.get_config().get("database", {})
        
        # Retry logic for DB connection
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name="kaoyan_pool",
                    pool_size=5,
                    host=db_config.get("host", "localhost"),
                    port=db_config.get("port", 3306),
                    user=db_config.get("user", "root"),
                    password=db_config.get("password", "password"),
                    database=db_config.get("db_name", "kaoyan_copilot"),
                    autocommit=True
                )
                print("MySQL Connection Pool initialized successfully.")
                break
            except mysql.connector.Error as err:
                print(f"Error initializing DB pool (Attempt {attempt+1}/{max_retries}): {err}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    print("Failed to connect to MySQL database.")
                    # We don't raise error here to allow app to start even if DB is down initially
                    self._pool = None

    def get_connection(self):
        """Get a connection from the pool."""
        if not self._pool:
            # Try to re-initialize if it failed previously
            self._init_pool()
            if not self._pool:
                raise Exception("Database connection pool is not initialized.")
        
        return self._pool.get_connection()

    def execute_query(self, query, params=None):
        """Execute a query and return results (for SELECT)."""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            return result
        except mysql.connector.Error as err:
            print(f"Query Error: {err}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def execute_update(self, query, params=None):
        """Execute an update query (INSERT, UPDATE, DELETE) and return last row id."""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid
        except mysql.connector.Error as err:
            print(f"Update Error: {err}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

# Global instance
db_manager = DatabaseManager()
