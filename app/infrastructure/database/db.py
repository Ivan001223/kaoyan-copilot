import logging
import time
from typing import Any, Optional

import mysql.connector
from mysql.connector import pooling

from app.infrastructure.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    _instance: Optional["DatabaseManager"] = None
    _pool: Optional[pooling.MySQLConnectionPool] = None

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_pool()
        return cls._instance

    def _init_pool(self) -> None:
        db_config = settings.database
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._pool = pooling.MySQLConnectionPool(
                    pool_name="kaoyan_pool",
                    pool_size=5,
                    host=db_config.host,
                    port=db_config.port,
                    user=db_config.user,
                    password=db_config.password,
                    database=db_config.db_name,
                    autocommit=True,
                )
                logger.info("MySQL Connection Pool initialized successfully.")
                break
            except mysql.connector.Error as err:
                logger.warning(f"Error initializing DB pool (Attempt {attempt+1}/{max_retries}): {err}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    logger.error("Failed to connect to MySQL database.")
                    self._pool = None

    def get_connection(self) -> mysql.connector.MySQLConnection:
        if not self._pool:
            self._init_pool()
            if not self._pool:
                raise Exception("Database connection pool is not initialized.")
        return self._pool.get_connection()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> list[dict[str, Any]]:
        conn: Optional[mysql.connector.MySQLConnection] = None
        cursor: Optional[mysql.connector.cursor.CursorBase] = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            return result
        except mysql.connector.Error as err:
            logger.error(f"Query Error: {err}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        conn: Optional[mysql.connector.MySQLConnection] = None
        cursor: Optional[mysql.connector.cursor.CursorBase] = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid
        except mysql.connector.Error as err:
            logger.error(f"Update Error: {err}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


db_manager = DatabaseManager()
