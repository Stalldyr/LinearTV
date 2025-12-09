from contextlib import contextmanager
import sqlite3


class SQLexecute:
    def __init__(self, db_path):
        self.db_path = db_path

    @contextmanager
    def get_connection(self, row_factory):
        """
        Context manager for database connections.
        Ensures proper connection handling and cleanup.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            if row_factory:
                conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            print(f"Database error: {e}")
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Unexpected error: {e}")
            raise
        finally:
            if conn:
                conn.close()


    def execute_query(self, query, params=None, fetch_one=False, fetch_all=True, output = "dict"):
        """
        Universal query executor with error handling.
        
        Args:
            query: SQL query string
            params: Parameters for the query (optional)
            fetch_one: Return single row instead of all rows
            fetch_all: Whether to fetch results (False for INSERT/UPDATE/DELETE)
        
        Returns:
            Query results or None for non-SELECT queries
        """

        row_factory = False
        if output == "dict" or output == "rows":
            row_factory = True


        with self.get_connection(row_factory=row_factory) as conn:

            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_all and not fetch_one:
                result = cursor.fetchall()
            elif fetch_one:
                result = cursor.fetchone()
            else:
                result = cursor.rowcount  # For INSERT/UPDATE/DELETE operations
            
            conn.commit()

            if output == "dict":
                return [dict(zip(row.keys(), row)) for row in result] 

            else:
                return result