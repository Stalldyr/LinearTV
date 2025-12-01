import sqlite3
import os
from flask import jsonify
from contextlib import contextmanager
from datetime import datetime
from datetime import datetime, timedelta, time as time_class
import sys
from helper import calculate_time_blocks, create_path_friendly_name, calculate_end_time
from TVconstants import *

class TVDatabase:
    def __init__(self, db_path = 'data/tv.db', test_time=None):
        db_path = os.path.join(BASE_DIR, db_path)

        self.db_path = db_path
        self.test_time = test_time

        if not os.path.exists(self.db_path):
            self.setup_database()

    #EXECUTE QUERY

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


    def _execute_query(self, query, params=None, fetch_one=False, fetch_all=True, output = "dict"):
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


    #SETUP

    def setup_database(self):
        os.makedirs('data', exist_ok=True)
                
        self._execute_query('''
            CREATE TABLE IF NOT EXISTS series (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                tmdb_id INT,          
                season INTEGER DEFAULT 1,       
                episode INTEGER DEFAULT 1,          
                source TEXT,                         
                source_url TEXT,                     -- "https://play.tv2.no/programmer/serier/hotel-caesar/sesong-{season}"
                directory TEXT,                      -- "hotel_caesar_s{season}E{episode}"
                total_episodes INTEGER,              
                description TEXT,
                duration INT,
                reverse_order BOOLEAN,                    
                genre TEXT,
                year INT,
                episode_count INT DEFAULT 0
            )
        ''')
        
        self._execute_query('''
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY,
                series_id INTEGER REFERENCES series(id),
                yt_dlp_id TEXT,                    -- ID fra youtube-dl/yt-dlp
                tmdb_id INT,
                season_number INTEGER,
                episode_number INTEGER,
                title TEXT,
                description TEXT,
                duration INTEGER,
                filename TEXT,
                download_date DATE,
                file_size INTEGER,
                status TEXT DEFAULT 'pending',    -- 'pending', 'available', 'deleted', 'failed', 'downloading', 'missing'
                last_aired DATE,
                views INT, 
                keep_next_week BOOLEAN DEFAULT 0
            )
        ''')

        self._execute_query('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                tmdb_id INT,
                yt_dlp_id TEXT,
                description TEXT,
                duration INTEGER,
                year INT,
                genre TEXT,
                directory TEXT,
                filename TEXT,
                download_date DATE,
                file_size INTEGER,
                status TEXT DEFAULT 'pending',
                last_aired DATE,
                views INT,
                source TEXT,
                source_url TEXT
            )                                    
        ''')

        self._execute_query('''
            CREATE TABLE IF NOT EXISTS weekly_schedule (
                id INTEGER PRIMARY KEY,
                content_type TEXT NOT NULL,
                series_id INTEGER REFERENCES series(id),
                episode_id INTEGER REFERENCES episodes(id),
                movie_id INTEGER REFERENCES movies(id),
                name TEXT NOT NULL,       -- "Hotel Cæsar"
                day_of_week INTEGER NOT NULL,  -- 1=mandag, 7=søndag
                start_time TIME NOT NULL,      -- "19:30"
                end_time TIME,
                blocks INT,
                is_rerun BOOLEAN DEFAULT 0
            )
        ''')
        
        print("Databasetabeller opprettet!")

    def reset_database(self):
        '''
            Cleans the database while keeping the series and schedule intact
        '''

        self.update_column("episodes", "file_size", None)
        self.update_column("episodes", "filename", None)
        self.update_column("episodes", "download_date", None)
        self.update_column("episodes", "status", "pending")
        self.update_column("episodes", "last_aired", None)
        self.update_column("episodes", "views", 0)
        self.update_column("episodes", "tmdb_id", None)
        self.update_column("episodes", "keep_next_week", False)

        self.update_column("weekly_schedule", "episode_id", None)
        
    #SERIES TABLE OPERATIONS
    
    def add_program(self, data):
        data_type = data.pop("type")

        directory = create_path_friendly_name(data['name'])
        data.update(
            {
                "directory": directory
            }
        )

        import TVdownloader
        tv_dl = TVdownloader.TVDownloader(directory, data_type)
        
        if data['source_url']:
            if data_type == TYPE_SERIES:
                try:
                    tv_dl.get_ytdlp_season_metadata(data["season"], video_url=data['source_url'])
                    
                except Exception as e:
                    print(f"Error recieving ytdlp metadata: {e}")            

        if data["tmdb_id"]:
            if data_type == TYPE_SERIES:
                try:
                    tv_dl.get_tmdb_season_metadata(data["tmdb_id"], data["season"])
                    
                except Exception as e:
                    print(f"Error recieving tmdb metadata: {e}")

            if data_type == TYPE_MOVIES:
                try:
                    tv_dl.get_tmdb_movie_metadata(data["tmdb_id"])
                    
                except Exception as e:
                    print(f"Error recieving tmdb metadata: {e}")                
        
        if data_type == TYPE_SERIES:
            total_episodes = tv_dl.get_season_metadata(data)
            data.update(
                {
                    "total_episodes": total_episodes
                }
            )

        try:
            if data["id"] and self.check_if_id_exists(data_type, data["id"]):
                new_id = data.pop("id")
                self.update_row(data_type, data, id = new_id)
                print(f"Updated program: {data['name']}")

            else:
                data.pop("id", None)
                self.insert_row(data_type, data)
                print(f"Added new program: {data['name']}")
            
            return jsonify({"status": "success"})
            
        except Exception as e:
            print(f"Feil ved lagring: {e}")
            return jsonify({"status": "error", "message": str(e)})
            
    def get_all_series(self):
        query = 'SELECT * FROM series ORDER BY name'
        return self._execute_query(query)
    
    #02 EPISODE TABLE OPERATIONS

    def add_new_episode(self, episode_data):
        '''
        If files downloaded sucessfully, place info in the database.
        '''

        self.insert_row("episodes", episode_data)
        
        print(f"Logget nedlastet fil: {episode_data["filepath"]}")

        return self.get_most_recent_id("episodes")

    def get_status(self, series_id, season, episode):
        query = '''
            SELECT status FROM episodes
            WHERE series_id = ? AND season_number = ? AND episode_number = ?
        ''' 
        result = self._execute_query(query, (series_id, season, episode))
        
        return result[0]['status'] if result else None
    
    def create_pending_episode(self, series_id, season, episode):
        episode_data = {
            "series_id": series_id,
            "season_number": season,
            "episode_number": episode,
            "status": STATUS_PENDING,
            "download_date": None 
        }
        
        self.insert_row("episodes", episode_data)
        return self.get_most_recent_id("episodes")
    
    def get_pending_episodes(self, strict = False, local = False):
        conditions = []
        
        if strict:
            conditions.append(f'e.status IN ("{STATUS_PENDING}")')
        else:
            conditions.append(f'e.status IN ("{STATUS_PENDING}", "{STATUS_FAILED}", "{STATUS_MISSING}", "{STATUS_DOWNLOADING}", "{STATUS_DELETED}")')

        if local:
            conditions.append(f's.source = {SOURCE_LOCAL}')

        query = f'''
            SELECT e.*, s.name as series_name, s.source_url, s.directory, s.total_episodes, s.source, s.reverse_order, s.episode_count
            FROM episodes e
            JOIN series s ON e.series_id = s.id
            WHERE {" AND ".join(conditions)} AND e.season_number = s.season AND e.episode_number BETWEEN s.episode AND (s.episode + s.episode_count - 1)
            ORDER BY series_name, e.season_number, e.episode_number
        '''

        return self._execute_query(query)
    
    def get_pending_episodes_by_id(self, series_id, episode, count, strict = False):
        if strict:
            conditions = f"{STATUS_PENDING}"
        else:
            conditions = f"{STATUS_PENDING}, {STATUS_FAILED}, {STATUS_MISSING}, {STATUS_DOWNLOADING}, {STATUS_DELETED}"

        query = f'''
            SELECT e.*, s.name as series_name, s.source_url, s.directory
            FROM episodes e
            JOIN series s ON e.series_id = s.id
            WHERE e.status IN ({conditions}) AND e.series_id = ? AND e.episode_number BETWEEN ? AND ?
            ORDER BY e.season_number, e.episode_number
        '''

        return self._execute_query(query, (series_id, episode, int(episode) + int(count) - 1))
    
    def get_scheduled_episodes(self):
        query = f'''
            SELECT e.*, s.name as series_name, s.source_url, s.directory
            FROM episodes e
            JOIN series s ON e.series_id = s.id
            WHERE e.season_number = s.season AND e.episode_number BETWEEN s.episode AND (s.episode + s.episode_count - 1) 
            ORDER BY series_name, e.season_number, e.episode_number
        '''
        return self._execute_query(query)
    
    def get_available_episodes(self):
        query = '''
            SELECT e.*, s.name as series_name, s.source_url, s.directory
            FROM episodes e
            JOIN series s ON e.series_id = s.id
            WHERE e.status = 'available'
            ORDER BY e.series_id, e.season_number, e.episode_number
        '''

        return self._execute_query(query)
    
    def get_nonavailable_episodes(self):
        query = '''
            SELECT e.*, s.name as series_name, s.source_url, s.directory
            FROM episodes e
            JOIN series s ON e.series_id = s.id
            WHERE e.status != 'available'
            ORDER BY e.series_id, e.season_number, e.episode_number
        '''

        return self._execute_query(query)

    def get_available_episodes_by_id(self, series_id):
        query = '''
            SELECT * FROM episodes
            JOIN series as s ON e.series_id = s.id
            WHERE status = 'available' AND series_id = ? AND e.episode_number BETWEEN s.episode AND (s.episode + s.episode_count - 1) 
            ORDER BY series_id, season_number, episode_number
        '''

        return self._execute_query(query, (series_id,))
    
    def get_obsolete_episodes(self):
        query = '''
            SELECT e.*, s.directory FROM episodes as e
            JOIN series as s ON e.series_id = s.id
            WHERE keep_next_week = 0 AND status = 'available' AND last_aired IS NOT NULL AND e.episode_number BETWEEN s.episode - s.count AND s.episode - 1
        '''

        #  AND last_aired <= DATE('now', '-7 days')
        
        return self._execute_query(query)
    
    def update_episode_keeping_status(self, episode_id, keep:bool):
        self.edit_cell("episodes", episode_id, "keep_next_week", keep)

    def get_kept_episodes(self):
        query = '''
            SELECT * FROM episodes
            WHERE keep_next_week = 1 AND status = 'available'
        '''

        return self._execute_query(query)
    
    def get_episode_by_details(self, series_id, season, episode):
        """
        Hent episode basert på series_id, season og episode number
        """
        query = '''
            SELECT * FROM episodes
            WHERE series_id = ? AND season_number = ? AND episode_number = ?
        '''
        result = self._execute_query(query, (series_id, season, episode))
        return result[0] if result else None
    
    def update_media_status(self, file_id, media_type, status, **kwargs):
        updates = {"status": status}
        updates.update(kwargs)

        if media_type == TYPE_SERIES:
            self.edit_row_by_id(TABLE_EPISODES, file_id, **updates)
            print(f"Episode ID {file_id}: Status oppdatert til '{status}'")
        elif media_type == TYPE_MOVIES:
            self.edit_row_by_id(TABLE_MOVIES, file_id, **updates)
            print(f"Movies ID {file_id}: Status oppdatert til '{status}'")

    #MOVIES TABLE OPERATIONS

    def get_all_movies(self):
        query = 'SELECT * FROM movies ORDER BY name'
        return self._execute_query(query)
    
    def get_available_movies(self):
        query = f'''
            SELECT m.* FROM movies m
            WHERE status = "available"
        '''
        return self._execute_query(query)
    
    def get_scheduled_movies(self):
        query = f'''
            SELECT m.* FROM movies m
            JOIN weekly_schedule ws ON m.id = ws.movie_id
        '''
        return self._execute_query(query)
    
    def get_obsolete_movies(self):
        query = '''
            SELECT m.* FROM movies as m
            WHERE status = 'available' AND last_aired IS NOT NULL
        '''

        #  AND last_aired <= DATE('now', '-7 days')
        
        return self._execute_query(query)
    

    #WEEKLY SCHEDULE

    def save_schedule_entry(self, data):
        """Save new entry in the weekly schedule"""

        try:
            existing = self._execute_query('''
                SELECT id FROM weekly_schedule 
                WHERE day_of_week = ? AND start_time = ?
            ''', (data['day_of_week'], data['start_time']))

            if existing:
                if data["name"] == "[Ledig]":
                    self._execute_query('''
                        DELETE FROM weekly_schedule
                        WHERE day_of_week = ? AND start_time = ?
                    ''', (data['day_of_week'], data['start_time']))

                    print(f"Slettet program: {data['name']} på {data['day_of_week']} {data['start_time']}")

                else:
                    conditions = {
                        "day_of_week": data["day_of_week"], 
                        "start_time": data["start_time"]
                    }

                    data["end_time"] = calculate_end_time(data["start_time"], data["duration"])
                    data["blocks"] = calculate_time_blocks(data["duration"])
                    data.pop("duration", None)

                    self.edit_row_by_conditions("weekly_schedule", conditions, **data)

                    print(f"Endret program: {data['name']} på {data['day_of_week']} {data['start_time']}")
            else:
                data["end_time"] = calculate_end_time(data["start_time"], data["duration"])
                data["blocks"] = calculate_time_blocks(data["duration"])
                data.pop("duration", None)
                self.insert_row("weekly_schedule", data)

                print(f"Lagret program: {data['name']} på {data['day_of_week']} {data['start_time']}")

            self.update_episode_count()
            
            return jsonify({"status": "success"})
            
        except Exception as e:
            print(f"Feil ved lagring: {e}")
            return jsonify({"status": "error", "message": str(e)})
        

    def get_episode_count(self):
        query = '''
            SELECT series_id, COUNT(*) as count
            FROM weekly_schedule
            WHERE is_rerun = 0
            GROUP BY series_id
        '''

        return self._execute_query(query)
    
    def update_episode_count(self):
        query = '''
            UPDATE series
            SET episode_count = (
                SELECT COUNT(*)
                FROM weekly_schedule ws
                WHERE ws.is_rerun = 0 AND ws.series_id = series.id
            );
        '''

        self._execute_query(query)

    def get_daily_schedule(self):
        now = datetime.now()

        #put this in helper function
        current_day = int(now.strftime('%w'))

        if current_day == 0:
            current_day = 7

        query = '''
            SELECT * FROM weekly_schedule
            WHERE day_of_week = ?
            ORDER BY start_time
        '''

        return self._execute_query(query,(current_day,))
    
    def get_weekly_schedule(self):
        #Get all scheduled shows
        query = '''
            SELECT * FROM weekly_schedule
            ORDER BY day_of_week, start_time
        '''

        return self._execute_query(query)
    
    def get_weekly_schedule_with_episode(self):
        query = '''
            SELECT ws.name, ws.day_of_week, ws.start_time, ws.is_rerun, e.episode_number, e.filename, e.keep_next_week FROM weekly_schedule AS ws
            JOIN episodes e ON e.id = ws.episode_id  
            ORDER BY ws.day_of_week, ws.start_time
        '''
        
        return self._execute_query(query)
        

    def get_program_schedule(self, series_id):
        query = '''
            SELECT * FROM weekly_schedule
            WHERE series_id = ?
            ORDER BY day_of_week, start_time
        '''

        return self._execute_query(query,(series_id,))
    
    def get_scheduled_series(self):
        query = '''
            SELECT DISTINCT s.* FROM series as s
            INNER JOIN weekly_schedule ws ON s.id = ws.series_id
            ORDER BY s.name
        '''

        return self._execute_query(query)

    def check_if_rerun_before_new(self, series_id):
        query = '''
            SELECT day_of_week, start_time, is_rerun
            FROM weekly_schedule 
            WHERE series_id = ?
            ORDER BY day_of_week, start_time
        '''
        
        airings = self._execute_query(query, (series_id,))
        
        if len(airings) < 2:
            return False  
        
        first_airing = airings[0]
        return first_airing["is_rerun"] == 1
    
    #DOWNLOADS

    def get_weekly_download_schedule(self):
        count = '''
            SELECT series_id, COUNT() as count
            FROM weekly_schedule
            WHERE is_rerun = 0
            GROUP BY series_id
        '''

        query = f'''
            SELECT s.id as series_id, s.name, s.season, s.episode, s.source, s.source_url, s.tmdb_id, s.directory, s.total_episodes, s.reverse_order as reverse, c.count
            FROM series s
            LEFT JOIN ({count}) c ON c.series_id = s.id
            WHERE c.count > 0
        '''

        return self._execute_query(query)
    
    def increment_episode(self, series_id):
        query = '''
            UPDATE series
            SET episode = episode + 1
            WHERE id = ?
        '''

        self._execute_query(query,(series_id,))
        
        print(f"Serie ID {series_id}: Episode nummer inkrementert.")

    def decrement_episode(self, series_id):
        query = '''
            UPDATE series
            SET episode = episode - 1
            WHERE id = ?
        '''

        self._execute_query(query,(series_id,))
        
        print(f"Serie ID {series_id}: Episode nummer dekrementert.")

    def update_episode_links(self, id, episode_id):
        query = '''
            UPDATE weekly_schedule
            SET episode_id = ?
            WHERE id = ?
        '''

        self._execute_query(query,(episode_id,id))

    def update_movie_link(self, id, movie_id):
        query = '''
            UPDATE weekly_schedule
            SET movie_id = ?
            WHERE id = ?
        '''

        self._execute_query(query,(movie_id,id))
    





    #AIRING OPERATIONS
    
    def get_air_schedule(self):
        query = '''
            SELECT 
                ws.id,
                ws.name,
                ws.day_of_week,
                ws.start_time,
                ws.end_time,
                ws.is_rerun,
                COALESCE(e.filename, m.filename) as filename,
                COALESCE(e.description, m.description) as description,
                COALESCE(e.status, m.status) as status,
                COALESCE(m.duration, s.duration) as duration,
                COALESCE(m.last_aired, e.last_aired) as last_aired,
                e.episode_number,
                COALESCE(m.directory, s.directory) as directory,
                COALESCE(s.description, m.description) as program_description,
                COALESCE(e.id, m.id) as media_id,
                CASE 
                    WHEN m.id IS NOT NULL THEN 'movies'
                    WHEN e.id IS NOT NULL THEN 'series'
                END as content_type
            FROM weekly_schedule ws
            LEFT JOIN movies m ON ws.movie_id = m.id
            LEFT JOIN episodes e ON ws.episode_id = e.id
            LEFT JOIN series s ON e.series_id = s.id
        '''

        return self._execute_query(query)



    def get_current_program(self, time = datetime.now(), daily=False):
        schedule = self.get_air_schedule()

        current_time = time.time()
        current_day = int(time.strftime('%w'))

        if current_day == 0:
            current_day = 7
        
        for program in schedule:
            if program['day_of_week'] == current_day:
                # Parse start time
                start_hour, start_min = map(int, program['start_time'].split(':'))
                start_time = time_class(start_hour, start_min)
                
                end_time = datetime.strptime(program['end_time'], "%H:%M").time() if program['end_time'] else None
                if not end_time:
                    duration_minutes = program['duration'] if program['duration'] else 30
                    end_time = calculate_end_time(program['start_time'], duration_minutes)

                # Normal program within same day
                if start_time <= current_time < end_time:
                    return program
        
        return None


    #TABLE OPERATIONS

    #Cell operations
    def get_most_recent_id(self, table):
        table_id = self._execute_query(f'''
            SELECT id 
            FROM {table} 
            ORDER BY id DESC 
            LIMIT 1;
        ''', output="tuples")

        return table_id[0][0]
    
    def get_cell(self, table, record_id, column):
        result = self._execute_query(f"SELECT {column} FROM {table} WHERE id = ?", (record_id,))
        return result[0] if result else None

    def edit_cell(self, table, id, column, new_value):
        self._execute_query( f"UPDATE {table} SET {column} = ? WHERE id = ?", (new_value, id))
    
    def check_if_id_exists(self,table, key):
        query = f'''
            SELECT COUNT(*)
            FROM {table}
            WHERE id = ?;
        '''

        return self._execute_query(query,(key,),output=tuple)[0][0]
    

    #Column operations
    def add_column(self, table, col, type=None):
        self._execute_query(f"""ALTER TABLE {table} ADD COLUMN {col} {type};""")

    def rename_column(self,table,col1,col2):
        self._execute_query(f"""ALTER TABLE {table} RENAME COLUMN {col1} TO {col2};""")

    def drop_column(self,table,col):
        self._execute_query(f"""ALTER TABLE {table} DROP COLUMN {col};""")

    def update_column(self, table, col, value):
        self._execute_query(f"""UPDATE {table} SET {col} = ?;""", (value,))

    #Row operations
    def get_row_by_id(self, table, row_id):
        result = self._execute_query(f'SELECT * FROM {table} WHERE id = ?', (row_id,))
        return result[0] if result else None

    def delete_row(self, table, id):
        if id == -1:
            id = "(SELECT MAX(id))"

        self._execute_query(f"DELETE FROM {table} WHERE id = ?", (id,))        
        print(f"Slettet oppføring {id} i {table}")

    def edit_row_by_id(self, table, series_id, **kwargs):        
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        values.append(series_id)
        
        query = f"UPDATE {table} SET {', '.join(fields)} WHERE id = ?"
        self._execute_query(query,values)

    def edit_row_by_conditions(self, table, conditions:dict, **kwargs):        
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
        self._execute_query(query,values)

    def insert_row(self, table, data:dict={}, **kwargs):
        fields = ', '.join(list(data.keys()) + list(kwargs.keys()))
        placeholders = ', '.join(['?'] * (len(data) + len(kwargs)))
        params = list(data.values()) + list(kwargs.values())
        
        query = f'''
            INSERT INTO {table}
            ({fields}) 
            VALUES ({placeholders})    
        '''
        self._execute_query(query, params)

    def update_row(self, table, data, **kwargs):
        fields = ', '.join([f"{key} = ?" for key in data])
        conditions = ', AND '.join([f"{key} = ?" for key in kwargs])
        params = list(data.values()) + list(kwargs.values())

        query = f'''
            UPDATE {table}
            SET {fields}
            WHERE {conditions}
        '''
        self._execute_query(query, params)

if __name__ == "__main__":
    tvdb = TVDatabase()
    
    if len(sys.argv)>1:
        operation = sys.argv[1]
        if operation == "setup":
            tvdb.setup_database()

        if operation == "reset":
            tvdb.reset_database()
