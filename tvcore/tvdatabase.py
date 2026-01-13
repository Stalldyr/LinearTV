from .helper import calculate_end_time
from .tvconstants import *
from .SQLexecute import SQLexecute
from .metadatafetcher import MetaDataFetcher
from pathlib import Path
from datetime import datetime, timedelta, time as time_class
import sys

class TVDatabase:
    def __init__(self, test_time=None):
        db_path = Path(__file__).parent.parent.absolute()/"data"/"tv.db" #Needs to be improved

        self.db_path = Path(db_path)
        self.test_time = test_time

        self.metadatafetcher = MetaDataFetcher()

        self.sql = SQLexecute(self.db_path)
        self.execute_query = SQLexecute(self.db_path).execute_query
    
        if not self.db_path.exists():
            self.db_path.touch(exist_ok=True)
            self.setup_database()

    #SETUP

    def setup_database(self):
        """
        Sets up database tables if they don't already exists.
        """

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

    def reset_database(self):
        """
        Reset the database to its initial state while preserving series and schedule data.

        This method clears episode-specific metadata by:
        - Removing file information (file_size, filename)
        - Clearing download and air date information (download_date, last_aired)
        - Resetting episode status to 'pending'
        - Resetting view count to 0
        - Clearing third-party identifiers (tmdb_id)
        - Removing keep flags (keep_next_week)
        - Disassociating episodes from the weekly schedule
        """

        self.sql.update_column("episodes", "file_size", None)
        self.sql.update_column("episodes", "filename", None)
        self.sql.update_column("episodes", "download_date", None)
        self.sql.update_column("episodes", "status", "pending")
        self.sql.update_column("episodes", "last_aired", None)
        self.sql.update_column("episodes", "views", 0)
        self.sql.update_column("episodes", "tmdb_id", None)
        self.sql.update_column("episodes", "keep_next_week", False)

        self.sql.update_column("weekly_schedule", "episode_id", None)
        
    #SERIES TABLE OPERATIONS
    
    def add_program(self, program_type:str, **program_data):
        """
        Adds a new program to the database.

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
        """

        self.sql.insert_row(program_type, program_data)
        new_id = self.sql.get_most_recent_id(program_type)
        print(f"Added new program: {program_data.get('name')}")
        return new_id
        
    def update_program(self, program_type:str, program_id:int, **program_data):
        """
        Updates existing program in the database.

        Args:
            program_type: Should be set to either "series" or "movies.
            program_id: Database ID for the program.
            program_data: Fields to update
                        
        Optional (via program_data or kwargs):
            source_url, year, description, duration, genre, tmdb_id,
            season, episode, directory, total_episodes, etc.
        """

        self.sql.update_row(program_type, program_data, id=program_id)

        print(f"Updated program {program_data.get('name')}")


    def delete_program(self, program_id, media_type):
        """
        Deletes a program from the movies/series-table and the weekly schedule (if scheduled).
        
        program_id: id in the table
        media_type: "movies" or "series"
        """

        if media_type == TYPE_SERIES:
            self.sql.delete_row(TABLE_SERIES, program_id)

            for airing in self.get_program_schedule_by_series_id(program_id):
                self.sql.delete_row(TABLE_SCHEDULE, airing["id"])

            return True

        elif media_type == TYPE_MOVIES:
            self.sql.delete_row(TABLE_MOVIES, program_id)

            for airing in self.get_program_schedule_by_movie_id(program_id):
                self.sql.delete_row(TABLE_SCHEDULE, airing["id"])

            return True
        
        else:
            return False

    def get_schedule_by_time(self, day_of_week, start_time, end_time = None):
        """
        Returns rows from the weekly schedule filtered on date and time.
        Note!: Should possibly be merged with get_current_program 
        """

        query = '''
            SELECT * FROM weekly_schedule 
            WHERE day_of_week = ? AND start_time BETWEEN ? and ?
            ORDER BY day_of_week, start_time
        '''

        return self.execute_query(query, (day_of_week, start_time, end_time if end_time else start_time))

    def add_schedule_entry(self, data):
        """Adds new entry to the weekly schedule"""
        self.sql.insert_row(TABLE_SCHEDULE, data)
    
    def delete_schedule_by_id(self, schedule_id):
        """Deletes entry from schedule based on the primary ID"""
        self.sql.delete_row(TABLE_SCHEDULE, schedule_id)

    def edit_schedule(self, conditions, data):
        """Deletes entry from schedule based on custom conditions"""
        self.sql.edit_row_by_conditions(TABLE_SCHEDULE, conditions, **data)
    
    def get_all_series(self):
        """Returns all series from the series-table."""
        return self.execute_query('SELECT * FROM series ORDER BY name')
    
    #02 EPISODE TABLE OPERATIONS

    def update_program_info(self, media_type:str, media_id:int, **file_info): #change name?
        """
        Adds file info for local files to the database.
        """

        if media_type == TYPE_SERIES:
            self.sql.edit_row_by_id(TABLE_EPISODES, media_id, **file_info)
        elif media_type == TYPE_MOVIES:
            self.sql.edit_row_by_id(TABLE_MOVIES, media_id, **file_info)

        return self.sql.get_most_recent_id(TABLE_EPISODES)
    
    def get_pending_episodes(self, strict:bool = False, local:bool = False, schedule:bool = True):
        """
        Return pending episodes from the episodes table.

        strict: Wether status is strictly "pending" or have other nonavailable statuses, i.e. "failed" or "missing".
        local: Wether .... 
        schedule: Wether or not it return pending episodes .... only from programs that are in the weekly schedule
        """
        conditions = []
        join = ""
        
        if strict:
            conditions.append(f'e.status IN ("{STATUS_PENDING}")')
        else:
            conditions.append(f'e.status IN ("{STATUS_PENDING}", "{STATUS_FAILED}", "{STATUS_MISSING}", "{STATUS_DOWNLOADING}", "{STATUS_DELETED}")')

        if local:
            conditions.append(f's.source = {SOURCE_LOCAL}')

        if schedule:
            join = """AND EXISTS (
                SELECT 1 FROM weekly_schedule ws 
                WHERE ws.series_id = s.id
            )"""

        query = f'''
            SELECT e.*, s.name as series_name, s.source_url, s.directory, s.total_episodes, s.source, s.reverse_order, s.episode_count
            FROM episodes e
            JOIN series s ON e.series_id = s.id
            WHERE {" AND ".join(conditions)} AND e.season_number = s.season AND e.episode_number BETWEEN s.episode AND (s.episode + s.episode_count - 1)
            {join}
            ORDER BY series_name, e.season_number, e.episode_number
        '''

        return self.execute_query(query)
            
    def get_scheduled_episodes(self):
        """
        All episodes in the schedule for the current week
        """

        query = f'''
            SELECT DISTINCT e.*, s.*
            FROM episodes e
            JOIN series s ON e.series_id = s.id
            JOIN weekly_schedule ws ON ws.series_id = s.id
            WHERE e.season_number = s.season AND e.episode_number BETWEEN s.episode AND (s.episode + s.episode_count - 1) 
            ORDER BY s.name, e.season_number, e.episode_number
        '''
        return self.execute_query(query)
    
    def get_available_episodes(self):
        """Returns episodes that has "available"-status, i.e. episodes with a file ready for viewing."""

        query = '''
            SELECT e.*, s.name as series_name, s.source_url, s.directory
            FROM episodes e
            JOIN series s ON e.series_id = s.id
            WHERE e.status = 'available'
            ORDER BY e.series_id, e.season_number, e.episode_number
        '''

        return self.execute_query(query)
    
    def get_scheduled_episodes_by_id(self, series_id, offset):
        query = '''
            SELECT e.* FROM episodes e
            JOIN series s ON e.series_id = s.id
            WHERE series_id = ? 
            AND e.episode_number BETWEEN (s.episode - ?) AND (s.episode + s.episode_count - 1)
            ORDER BY e.season_number, e.episode_number
        '''

        return self.execute_query(query, (series_id, offset))
    
    def get_obsolete_episodes(self):
        """Returns available episodes that has already been viewed and is not planned to be viewes again."""
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
    
    def add_pending_episodes(self, **kwargs):
        self.sql.insert_row(TABLE_EPISODES, status = STATUS_PENDING, **kwargs)
    
    def update_episode_keeping_status(self, episode_id:int, keep:bool):
        ''''
            Updates if the episode to be kept or not for the next week

            episode_id (int): The primary id of the episode
            keep (boolean): Marks the episode for keeping (true) or deleting (false)
        '''

        self.sql.edit_cell(TABLE_EPISODES, episode_id, "keep_next_week", keep)

    def get_kept_episodes(self):
        """Returns episodes that are kept from previous week."""

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
            Returns episodes from the "episode" table filtered by series_id, season and episode number
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
            self.sql.edit_row_by_id(TABLE_EPISODES, file_id, **updates)
        elif media_type == TYPE_MOVIES:
            self.sql.edit_row_by_id(TABLE_MOVIES, file_id, **updates)

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
        """Returns movies from the weekly schedule"""
        query = f'''
            SELECT m.* FROM movies m
            JOIN weekly_schedule ws ON m.id = ws.movie_id
        '''
        return self.execute_query(query)
    
    def get_obsolete_movies(self):
        "Returns movies marked for deletion"
        query = '''
            SELECT m.* FROM movies as m
            WHERE status = 'available' AND last_aired IS NOT NULL
        '''
        
        return self.execute_query(query)
    

    #WEEKLY SCHEDULE     
    
    def update_schedule_count(self):
        "Updates the number of episodes of the same series within a week"
        query = '''
            UPDATE series
            SET episode_count = (
                SELECT COUNT(*)
                FROM weekly_schedule ws
                WHERE ws.is_rerun = 0 AND ws.series_id = series.id
            );
        '''

        self.execute_query(query)
    
    def get_weekly_schedule(self) -> list[dict]:
        """Returns all scheduled programs in the weekly schedule"""
        query = '''
            SELECT * FROM weekly_schedule
            ORDER BY day_of_week, start_time
        '''

        return self.execute_query(query)
    
    def get_weekly_schedule_with_episode(self) -> list[dict]:
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
        """Increments the current episode in the series table by 1
        Note!: should be corrected for transission between seasons.
        """
        query = '''
            UPDATE series
            SET episode = episode + 1
            WHERE id = ?
        '''

        self.execute_query(query,(series_id,))

    def update_episode_links(self, schedule_id, episode_id):
        query = '''
            UPDATE weekly_schedule
            SET episode_id = ?
            WHERE id = ?
        '''

        self.execute_query(query,(episode_id,schedule_id))

    def update_movie_link(self, id, movie_id):
        query = '''
            UPDATE weekly_schedule
            SET movie_id = ?
            WHERE id = ?
        '''

        self.execute_query(query,(movie_id,id))
    
    #AIRING OPERATIONS
    
    def get_air_schedule(self) -> list[dict]:
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

    def get_current_program(self, time = datetime.now()) -> dict:
        """
        Returns the program showing at a specified time
        Note!: Should possibly be moved to programmanager/tvstreamer or be rewritten in SQL
        """
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

if __name__ == "__main__":
    tvdb = TVDatabase()

    if len(sys.argv)>1:
        operation = sys.argv[1]
        if operation == "setup":
            tvdb.setup_database()

        if operation == "reset":
            tvdb.reset_database()
