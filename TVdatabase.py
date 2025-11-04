import sqlite3
import os
from flask import jsonify
from contextlib import contextmanager
import slugify
from datetime import datetime
from datetime import datetime, timedelta, time as time_class
import helper

class TVDatabase:
    def __init__(self, db_path = 'data/tv.db', test_time=None):

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
                
        # Lag series tabell (episode-tracking)
        self._execute_query('''
            CREATE TABLE IF NOT EXISTS series (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,          
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
                tmdb_id INT
            )
        ''')
        
        # Lag episodes tabell (denne ukas nedlastede filer) series_id INTEGER REFERENCES series(id)
        self._execute_query('''
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY,
                series_id INTEGER REFERENCES series(id),
                yt_dlp_id TEXT,               -- ID fra youtube-dl/yt-dlp
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
            CREATE TABLE IF NOT EXISTS weekly_schedule (
                id INTEGER PRIMARY KEY,
                series_id INTEGER REFERENCES series(id),
                episode_id INTEGER REFERENCES episodes(id),
                show_name TEXT NOT NULL,       -- "Hotel Cæsar"
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
    
    def save_schedule_entry(self, data):
        """Save new entry in the weekly schedule"""

        try: 
            existing = self._execute_query('''
                SELECT id FROM weekly_schedule 
                WHERE day_of_week = ? AND start_time = ?
            ''', (data['day_of_week'], data['start_time']))

            if existing:
                if data["show_name"] == "[Ledig]":
                    #Sletter oppføring
                    self._execute_query('''
                        DELETE FROM weekly_schedule
                        WHERE day_of_week = ? AND start_time = ?
                    ''', (data['day_of_week'], data['start_time']))

                    print(f"Slettet program: {data['show_name']} på {data['day_of_week']} {data['start_time']}")

                else:
                    #Oppdater eksisterende oppføring
                    conditions = {
                        "day_of_week": data["day_of_week"], 
                        "start_time": data["start_time"]
                    }

                    data["end_time"] = helper._calculate_end_time(data["start_time"], data["duration"])
                    data["blocks"] = helper._calculate_blocks(data["duration"])
                    data.pop("duration", None)

                    self.edit_row_by_conditions("weekly_schedule", conditions, **data)

                    print(f"Endret program: {data['show_name']} på {data['day_of_week']} {data['start_time']}")
            else:
                # Legg til nytt program
                data["end_time"] = helper._calculate_end_time(data["start_time"], data["duration"])
                data["blocks"] = helper._calculate_blocks(data["duration"])
                data.pop("duration", None)
                self.insert_row("weekly_schedule", data)

                print(f"Lagret program: {data['show_name']} på {data['day_of_week']} {data['start_time']}")
            
            return jsonify({"status": "success"})
            
        except Exception as e:
            print(f"Feil ved lagring: {e}")
            return jsonify({"status": "error", "message": str(e)})
        
    def save_series(self,data):
        import TVdownloader

        tv_dl = TVdownloader.TVDownloader()

        directory = helper._create_valid_filename(data['name'])
        if not os.path.exists(f'downloads/{directory}'):
            os.makedirs(f'downloads/{directory}')
        
        data.update(
            {
                "directory": directory
            }
        )

        url = None
        total_episodes = None
        if data['source_url']:
            url = data['source_url'].format(season=data['season'])
            try:
                tv_dl.get_ytdlp_season_metadata(directory, video_url=url)
                
            except Exception as e:
                print(f"Feil ved henting av ytdlp metadata: {e}")

        if data["tmdb_id"]:
            try:
                tv_dl.get_tmdb_season_metadata(data["tmdb_id"], directory, data["season"])
                
            except Exception as e:
                print(f"Feil ved henting av tmdb metadata: {e}")

        total_episodes = tv_dl.get_season_metadata(data)

        data.update(
            {
                "source_url": url,
                "directory": directory,
                "total_episodes": total_episodes
            }
        )

        try:
            if data["id"] and self.check_if_id_exists("series", data["id"]):
                new_id = data.pop("id")
                self.update_row("series", data, id = new_id)
                print(f"Oppdatert program: {data['name']}")

            else:
                data.pop("id", None)
                self.insert_row("series", data)
                print(f"Lagt til nytt program: {data['name']}")
            
            return jsonify({"status": "success"})
            
        except Exception as e:
            print(f"Feil ved lagring: {e}")
            return jsonify({"status": "error", "message": str(e)})
        
    def update_series(self,data):
        
        directory = helper._create_valid_filename(data['name'])
        if not os.path.exists(f'downloads/{directory}'):
            os.makedirs(f'downloads/{directory}')

        

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
    
    def get_all_series(self):
        query = 'SELECT * FROM series ORDER BY name'
        return self._execute_query(query)

    #WEEKLY SCHEDULE

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
            SELECT ws.show_name, ws.day_of_week, ws.start_time, ws.is_rerun, e.episode_number, e.filename, e.keep_next_week FROM weekly_schedule AS ws
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

    def update_download_links(self, id, episode_id):
        query = '''
            UPDATE weekly_schedule
            SET episode_id = ?
            WHERE id = ?
        '''

        self._execute_query(query,(episode_id,id))
    


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
            "status": "pending",
            "download_date": None 
        }
        
        self.insert_row("episodes", episode_data)
        return self.get_most_recent_id("episodes")
    
    def get_pending_episodes(self, series_id, episode, count, strict = False):
        if strict:
            conditions = "'pending'"
        else:
            conditions = "'pending', 'failed', 'missing', 'downloading', 'deleted'"

        query = f'''
            SELECT e.*, s.name as series_name, s.source_url, s.directory
            FROM episodes e
            JOIN series s ON e.series_id = s.id
            WHERE e.status IN ({conditions}) AND e.series_id = ? AND e.episode_number BETWEEN ? AND ?
            ORDER BY e.season_number, e.episode_number
        '''

        return self._execute_query(query, (series_id, episode, int(episode) + int(count) - 1))
    
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
            WHERE status = 'available' AND series_id = ?
            ORDER BY series_id, season_number, episode_number
        '''

        return self._execute_query(query, (series_id,))
    
    def get_obsolete_episodes(self):
        query = '''
            SELECT e.*, s.directory FROM episodes as e
            Join series as s ON e.series_id = s.id
            WHERE keep_next_week = 0 AND status = 'available'
        '''

        #  AND last_aired <= DATE('now', '-7 days')
        
        return self._execute_query(query)
    
    def update_episode_keeping_status(self, episode_id, keep:bool):
        self.edit_cell("episodes", episode_id, "keep_next_week", keep)

        if keep:
            print(f"Episode ID {episode_id} markert for bevaring.")
        else:
            print(f"Episode ID {episode_id} markert for sletting.")

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
    
    def update_episode_status(self, episode_id, status, **kwargs):
        """
        Oppdater status for en episode
        
        Args:
            episode_id: ID for episoden
            status: Ny status ('pending', 'downloading', 'available', 'failed')
            **kwargs: Andre felter som skal oppdateres (f.eks. file_size, download_date)
        """
        updates = {"status": status}
        
        # Legg til download_date hvis status er 'available'
        if status == "available" and "download_date" not in kwargs:
            updates["download_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        updates.update(kwargs)
        
        self.edit_row_by_id("episodes", episode_id, **updates)
        print(f"Episode ID {episode_id}: Status oppdatert til '{status}'")


    #AIRING OPERATIONS

    def get_air_schedule(self):
        query = '''
            SELECT t1.*, s.duration, s.directory, s.description as series_description FROM series s
            LEFT JOIN (SELECT ws.*, e.filename, e.episode_number, e.description as episode_description, e.last_aired, e.status FROM weekly_schedule as ws RIGHT JOIN episodes e ON ws.episode_id = e.id) as t1 ON t1.series_id = s.id
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
                    end_time = helper._calculate_end_time(program['start_time'], duration_minutes)

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
        print(f"Oppdatert {table} ID {id}: satt {column} til {new_value}")
    
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
        
        print(f"Ny oppføring lagt til i {table}.")

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

    tvdb._execute_query("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'weekly_schedule';")
