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
            
    #Cell operations
    def get_most_recent_id(self, table):
        table_id = self.execute_query(f'''
            SELECT id 
            FROM {table} 
            ORDER BY id DESC 
            LIMIT 1;
        ''', output="tuples")

        return table_id[0][0]
    
    def get_cell(self, table, record_id, column):
        result = self.execute_query(f"SELECT {column} FROM {table} WHERE id = ?", (record_id,))
        return result[0] if result else None

    def edit_cell(self, table, id, column, new_value):
        self.execute_query( f"UPDATE {table} SET {column} = ? WHERE id = ?", (new_value, id))
    
    def check_if_id_exists(self,table, key):
        query = f'''
            SELECT COUNT(*)
            FROM {table}
            WHERE id = ?;
        '''

        return self.execute_query(query,(key,),output=tuple)[0][0]
    

    #Column operations
    def add_column(self, table, col, type=None):
        self.execute_query(f"""ALTER TABLE {table} ADD COLUMN {col} {type};""")

    def rename_column(self,table,col1,col2):
        self.execute_query(f"""ALTER TABLE {table} RENAME COLUMN {col1} TO {col2};""")

    def drop_column(self,table,col):
        self.execute_query(f"""ALTER TABLE {table} DROP COLUMN {col};""")

    def update_column(self, table, col, value):
        self.execute_query(f"""UPDATE {table} SET {col} = ?;""", (value,))

    #Row operations
    def get_row_by_id(self, table:str, row_id:int):
        result = self.execute_query(f'SELECT * FROM {table} WHERE id = ?', (row_id,))
        return result[0] if result else None

    def delete_row(self, table, id):
        if id == -1:
            id = "(SELECT MAX(id))"

        try:
            self.execute_query(f"DELETE FROM {table} WHERE id = ?", (id,))        
            print(f"Slettet oppføring {id} i {table}")
            return True
        except:
            return False

    def edit_row_by_id(self, table:str, row_id:int, **kwargs):        
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        values.append(row_id)
        
        query = f"UPDATE {table} SET {', '.join(fields)} WHERE id = ?"
        self.execute_query(query,values)

    def edit_row_by_conditions(self, table:str, conditions:dict, **kwargs):        
        fields = []
        values = []
        conditions_list = []

        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)

        for key, value in conditions.items():
            conditions_list.append(f"{key} = ?")
            values.append(value)
        
        query = f"UPDATE {table} SET {', '.join(fields)} WHERE {' AND '.join(conditions_list)}"
        self.execute_query(query,values)

    def insert_row(self, table:str, data:dict={}, **kwargs):
        fields = ', '.join(list(data.keys()) + list(kwargs.keys()))
        placeholders = ', '.join(['?'] * (len(data) + len(kwargs)))
        params = list(data.values()) + list(kwargs.values())
        
        query = f'''
            INSERT INTO {table}
            ({fields}) 
            VALUES ({placeholders})    
        '''
        self.execute_query(query, params)

    def update_row(self, table:str, data:dict, **kwargs):
        fields = ', '.join([f"{key} = ?" for key in data])
        conditions = ', AND '.join([f"{key} = ?" for key in kwargs])
        params = list(data.values()) + list(kwargs.values())

        query = f'''
            UPDATE {table}
            SET {fields}
            WHERE {conditions}
        '''
        self.execute_query(query, params)