from flask import jsonify
from datetime import datetime
from datetime import datetime, timedelta, time as time_class
import sys
from helper import calculate_time_blocks, create_path_friendly_name, calculate_end_time
from tvconstants import *
from SQLexecute import SQLexecute
from pathlib import Path
from metadatafetcher import MetaDataFetcher
from typing import TypedDict, Optional
from dataclasses import dataclass

@dataclass
class ProgramData:
    name: str
    source: str
    season: int
    type: str
    id: Optional[int] = None
    source_url: Optional[str] = None
    tmdb_id: Optional[str] = None

class TVDatabase:
    def __init__(self, db_path="data/tv.db", test_time=None):
        self.db_path = Path(db_path)
        self.test_time = test_time

        self.metadatafetcher = MetaDataFetcher()
    
        if not self.db_path.exists():
            self.db_path.mkdir(exist_ok=True)
            self.setup_database()
        
        self.execute_query = SQLexecute(self.db_path).execute_query

    #SETUP

    def setup_database(self):
        self.execute_query('''
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
        
        self.execute_query('''
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

        self.execute_query('''
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

        self.execute_query('''
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
    
    def add_program(self, program_type:str, **program_data):
        '''
            Adds or a program to the database.

            Required:
                program_type: Should be set to either "series" or "movies.
                program_id: Id for the program. Should be set to None for a new program
                
            Required fields in program_data:
                name: Program name
                source: Source platform (NRK, TV2, YouTube, etc)
                season (for series)
                episode (for series)
            
            Optional (via program_data or kwargs):
                source_url, year, description, duration, genre, tmdb_id,
                season, episode, directory, total_episodes, etc.
        '''

        self.insert_row(program_type, program_data)
        new_id = self.get_most_recent_id(program_type)
        print(f"Added new program: {program_data.get('name')}")
        return new_id
        
    def update_program(self, program_type:str, program_id:int, **program_data):
        '''
            Updates existing program in the database.

            Args:
                program_type: Should be set to either "series" or "movies.
                program_id: Database ID for the program.
                **program_data: Fields to update
                            
            Optional (via program_data or kwargs):
                source_url, year, description, duration, genre, tmdb_id,
                season, episode, directory, total_episodes, etc.
        '''

        self.update_row(program_type, program_data, id=program_id)

        print(f"Updated program {program_data.get('name')}")


    def delete_program(self, program_id, media_type):
        if media_type == TYPE_SERIES:
            self.delete_row(TABLE_SERIES, program_id)

            for airing in self.get_program_schedule_by_series_id(program_id):
                self.delete_row(TABLE_SCHEDULE, airing["id"])

            return True

        elif media_type == TYPE_MOVIES:
            self.delete_row(TABLE_MOVIES, program_id)

            for airing in self.get_program_schedule_by_movie_id(program_id):
                self.delete_row(TABLE_SCHEDULE, airing["id"])

            return True
        
        else:
            return False

            
    def save_schedule_entry(self, data):
        """Save new entry in the weekly schedule"""

        try:
            existing = self.execute_query('''
                SELECT id FROM weekly_schedule 
                WHERE day_of_week = ? AND start_time = ?
            ''', (data['day_of_week'], data['start_time']))

            if existing:
                if data["name"] == "[Ledig]":
                    self.execute_query('''
                        DELETE FROM weekly_schedule
                        WHERE day_of_week = ? AND start_time = ?
                    ''', (data['day_of_week'], data['start_time']))

                    print(f"Removed program: {data['name']} på {data['day_of_week']} {data['start_time']}")

                else:
                    conditions = {
                        "day_of_week": data["day_of_week"], 
                        "start_time": data["start_time"]
                    }

                    data["end_time"] = calculate_end_time(data["start_time"], data["duration"])
                    data["blocks"] = calculate_time_blocks(data["duration"])
                    data.pop("duration", None)

                    self.edit_row_by_conditions("weekly_schedule", conditions, **data)

                    print(f"Edited program: {data['name']} at {data['day_of_week']} {data['start_time']}")
            else:
                data["end_time"] = calculate_end_time(data["start_time"], data["duration"])
                data["blocks"] = calculate_time_blocks(data["duration"])
                data.pop("duration", None)
                self.insert_row("weekly_schedule", data)

                print(f"Saved program: {data['name']} at {data['day_of_week']} {data['start_time']}")

            self.update_episode_count()
            
            return jsonify({"status": "success"})
            
        except Exception as e:
            print(f"Error while saving: {e}")
            return jsonify({"status": "error", "message": str(e)})
        
    def get_schedule_by_time(self, day_of_week, start_time):
        query = '''
                SELECT * FROM weekly_schedule 
                WHERE day_of_week = ? AND start_time = ?
        '''

        return self.execute_query(query, (day_of_week, start_time))

    def add_schedule_entry(self, data):
        self.insert_row(TABLE_SCHEDULE, data)
    
    def delete_schedule_by_id(self, schedule_id):
        print(schedule_id)
        self.delete_row(TABLE_SCHEDULE, schedule_id)

    def edit_schedule(self, conditions, data):
        self.edit_row_by_conditions(TABLE_SCHEDULE, conditions, **data)
    
    def get_all_series(self):
        query = 'SELECT * FROM series ORDER BY name'
        return self.execute_query(query)
    
    #02 EPISODE TABLE OPERATIONS

    def update_episode_info(self, media_type:str, media_id:int, file_info:dict):
        '''
            If files downloaded sucessfully, place file info in the database.
        '''

        if media_type == TYPE_SERIES:
            self.edit_row_by_id(TABLE_EPISODES, media_id, **file_info)
        elif media_type == TYPE_MOVIES:
            self.edit_row_by_id(TABLE_MOVIES, media_id, **file_info)

        self.insert_row("episodes", file_info)

        return self.get_most_recent_id("episodes")

    def get_episode_status(self, series_id:int, season:int, episode:int):
        '''
            Gets status of episode. UNUSED!
        '''

        query = '''
            SELECT status FROM episodes
            WHERE series_id = ? AND season_number = ? AND episode_number = ?
        ''' 
        result = self.execute_query(query, (series_id, season, episode))
        
        return result[0]['status'] if result else None
    
    def create_pending_episode(self, series_id:int, season:int, episode:int):
        episode_data = {
            "series_id": series_id,
            "season_number": season,
            "episode_number": episode,
            "status": STATUS_PENDING,
            "download_date": None 
        }
        
        self.insert_row("episodes", episode_data)
        return self.get_most_recent_id("episodes")
    
    def get_pending_episodes(self, strict:bool = False, local:bool = False):
        '''
            strict: wether status is strictly "pending" or have other nonavailable statuses
        '''
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

        return self.execute_query(query)
        
    def get_scheduled_episodes(self):
        '''
        
        '''
        query = f'''
            SELECT e.*, s.name as series_name, s.source_url, s.directory
            FROM episodes e
            JOIN series s ON e.series_id = s.id
            WHERE e.season_number = s.season AND e.episode_number BETWEEN s.episode AND (s.episode + s.episode_count - 1) 
            ORDER BY series_name, e.season_number, e.episode_number
        '''
        return self.execute_query(query)
    
    def get_available_episodes(self):
        query = '''
            SELECT e.*, s.name as series_name, s.source_url, s.directory
            FROM episodes e
            JOIN series s ON e.series_id = s.id
            WHERE e.status = 'available'
            ORDER BY e.series_id, e.season_number, e.episode_number
        '''

        return self.execute_query(query)
    
    def get_nonavailable_episodes(self):
        query = '''
            SELECT e.*, s.name as series_name, s.source_url, s.directory
            FROM episodes e
            JOIN series s ON e.series_id = s.id
            WHERE e.status != 'available'
            ORDER BY e.series_id, e.season_number, e.episode_number
        '''

        return self.execute_query(query)

    def get_scheduled_episodes_by_id(self, series_id):
        query = '''
            SELECT e.* FROM episodes e
            JOIN series s ON e.series_id = s.id
            WHERE series_id = ? AND e.episode_number BETWEEN s.episode AND (s.episode + s.episode_count - 1)
            ORDER BY e.season_number, e.episode_number
        '''

        return self.execute_query(query, (series_id,))
    
    def get_obsolete_episodes(self):
        query = '''
            SELECT e.*, s.directory FROM episodes as e
            JOIN series as s ON e.series_id = s.id
            WHERE keep_next_week = 0 
                AND status = 'available' 
                AND last_aired IS NOT NULL 
                AND (
                    e.season_number < s.season
                    OR (e.season_number = s.season AND e.episode_number < s.episode)
                )
        '''
        
        return self.execute_query(query)
    
    def update_episode_keeping_status(self, episode_id:int, keep:bool):
        ''''
            Sets if the episode to be kept or not

            episode_id: The id of the episode
            keep (boolean): Marks the episode for keeping (true) or deleting (false)
        '''

        self.edit_cell("episodes", episode_id, "keep_next_week", keep)

    def get_kept_episodes(self):
        query = '''
            SELECT e.* FROM episodes as e
            JOIN series s ON s.id = e.series_id
            WHERE keep_next_week = 1 
                AND status = 'available' 
                AND (
                    e.season_number < s.season
                    OR (e.season_number = s.season AND e.episode_number < s.episode)
                )

        '''

        return self.execute_query(query)
    
    def get_episode_by_details(self, series_id: int, season:int , episode: int):
        """
            Gets episodes based on series_id, season and episode number
        """

        query = '''
            SELECT * FROM episodes
            WHERE series_id = ? AND season_number = ? AND episode_number = ?
        '''
        result = self.execute_query(query, (series_id, season, episode))
        return result[0] if result else None
    
    def update_media_status(self, file_id:int, media_type:str, status:str, **kwargs):
        updates = {"status": status}
        updates.update(kwargs)

        if media_type == TYPE_SERIES:
            self.edit_row_by_id(TABLE_EPISODES, file_id, **updates)
        elif media_type == TYPE_MOVIES:
            self.edit_row_by_id(TABLE_MOVIES, file_id, **updates)

    #MOVIES TABLE OPERATIONS

    def get_all_movies(self):
        query = 'SELECT * FROM movies ORDER BY name'
        return self.execute_query(query)
    
    def get_available_movies(self):
        query = f'''
            SELECT m.* FROM movies m
            WHERE status = "available"
        '''
        return self.execute_query(query)
    
    def get_scheduled_movies(self):
        query = f'''
            SELECT m.* FROM movies m
            JOIN weekly_schedule ws ON m.id = ws.movie_id
        '''
        return self.execute_query(query)
    
    def get_obsolete_movies(self):
        query = '''
            SELECT m.* FROM movies as m
            WHERE status = 'available' AND last_aired IS NOT NULL
        '''
        
        return self.execute_query(query)
    

    #WEEKLY SCHEDULE     
    
    def update_episode_count(self):
        query = '''
            UPDATE series
            SET episode_count = (
                SELECT COUNT(*)
                FROM weekly_schedule ws
                WHERE ws.is_rerun = 0 AND ws.series_id = series.id
            );
        '''

        self.execute_query(query)

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

        return self.execute_query(query,(current_day,))
    
    def get_weekly_schedule(self):
        #Get all scheduled shows
        query = '''
            SELECT * FROM weekly_schedule
            ORDER BY day_of_week, start_time
        '''

        return self.execute_query(query)
    
    def get_weekly_schedule_with_episode(self):
        query = '''
            SELECT ws.name, ws.day_of_week, ws.start_time, ws.is_rerun, e.episode_number, e.filename, e.keep_next_week FROM weekly_schedule AS ws
            JOIN episodes e ON e.id = ws.episode_id  
            ORDER BY ws.day_of_week, ws.start_time
        '''
        
        return self.execute_query(query)
        

    def get_program_schedule_by_series_id(self, series_id):
        query = '''
            SELECT * FROM weekly_schedule
            WHERE series_id = ?
            ORDER BY day_of_week, start_time
        '''

        return self.execute_query(query,(series_id,))
    
    def get_program_schedule_by_movie_id(self, movie_id):
        query = '''
            SELECT * FROM weekly_schedule
            WHERE movie_id = ?
            ORDER BY day_of_week, start_time
        '''

        return self.execute_query(query,(movie_id,))
    
    def get_scheduled_series(self):
        query = '''
            SELECT DISTINCT s.* FROM series as s
            INNER JOIN weekly_schedule ws ON s.id = ws.series_id
            ORDER BY s.name
        '''

        return self.execute_query(query)

    def check_if_rerun_before_new(self, series_id):
        query = '''
            SELECT day_of_week, start_time, is_rerun
            FROM weekly_schedule 
            WHERE series_id = ?
            ORDER BY day_of_week, start_time
        '''
        
        airings = self.execute_query(query, (series_id,))
        
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

        return self.execute_query(query)
    
    def increment_episode(self, series_id):
        query = '''
            UPDATE series
            SET episode = episode + 1
            WHERE id = ?
        '''

        self.execute_query(query,(series_id,))

    def decrement_episode(self, series_id):
        query = '''
            UPDATE series
            SET episode = episode - 1
            WHERE id = ?
        '''

        self.execute_query(query,(series_id,))
        
    def update_episode_links(self, id, episode_id):
        query = '''
            UPDATE weekly_schedule
            SET episode_id = ?
            WHERE id = ?
        '''

        self.execute_query(query,(episode_id,id))

    def update_movie_link(self, id, movie_id):
        query = '''
            UPDATE weekly_schedule
            SET movie_id = ?
            WHERE id = ?
        '''

        self.execute_query(query,(movie_id,id))
    
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

        return self.execute_query(query)

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

        self.execute_query(f"DELETE FROM {table} WHERE id = ?", (id,))        
        print(f"Slettet oppføring {id} i {table}")

    def edit_row_by_id(self, table:str, series_id:int, **kwargs):        
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        values.append(series_id)
        
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

if __name__ == "__main__":
    tvdb = TVDatabase()

    if len(sys.argv)>1:
        operation = sys.argv[1]
        if operation == "setup":
            tvdb.setup_database()

        if operation == "reset":
            tvdb.reset_database()
