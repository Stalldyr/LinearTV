from nrkscraper.nrk_db import NRKSession, NRKdb, NRK1, NRK2, T
from tvstreamer.tvcore.metadatafetcher import MetaDataFetcher
from tvstreamer.tvcore.programmanager import ProgramManager
from tvstreamer.tvcore.tvdatabase import TVDatabase, Series, Movie, Episode, Schedule
from tvstreamer.tvcore.tvconstants import *
from tvstreamer.tvcore.calendar import *
import isodate
from datetime import datetime, date
from time import sleep
from slugify import slugify

from typing import TypeVar, Type, Generic

class NRKManager(Generic[T]):
    def __init__(self, db_path: str, channel: Type[T],  debug: bool = False):
        self.Session = NRKSession(db_path, debug)
        self.metadata = MetaDataFetcher()
        self.programmanager = ProgramManager()
        self.db = TVDatabase()
        self.channel = channel

    @classmethod
    def nrk1(cls, db_path: str, debug: bool = False) -> "NRKManager[NRK1]":
        return cls(db_path, NRK1, debug)
    
    @classmethod
    def nrk2(cls, db_path: str, debug: bool = False) -> "NRKManager[NRK2]":
        return cls(db_path, NRK2, debug)

    def insert_database(self, start, end):
        with self.Session() as session:
            db = NRKdb(session, self.channel)
            programs = db.get_nrk_web_programs_by_dates(start, end)

        for program in programs:
            series_id = None
            episode_id = None
            movie_id = None

            duration_dt = isodate.parse_duration(program.duration)
            duration = duration_dt.total_seconds()

            schedule_start = self.same_iso_week_this_year(program.planned_start)
            schedule_end = self.same_iso_week_this_year(program.planned_start + duration_dt)

            if program.series_id:
                series_id = self.db.add(
                    Series(
                        slug= program.series_id,
                        title= program.series_title,
                        genre= program.category_display_value
                    ),
                    ["slug"]
                )

                episode_id = self.db.add(
                    Episode(
                        series_id = series_id,
                        title = program.title,
                        description = program.description,
                        duration = duration,
                        program_id = program.program_id,
                        release = program.planned_start,
                        source_url = program.program_href
                    ),
                    ["program_id"]
                )

            else:
                movie_id = self.db.add(
                    Movie(
                        title = program.title,
                        program_id = program.program_id,
                        genre = program.category_display_value,
                        duration = duration,
                        release = program.planned_start,
                        description = program.description,
                        source_url = program.program_href,
                        slug = slugify(program.title)
                    )
                    ,
                    ["program_id"]
                )

            self.db.add(
                    Schedule(
                        title = program.title,
                        episode_id = episode_id,
                        movie_id = movie_id,
                        start = schedule_start,
                        end = schedule_end,
                        rerun = program.rerun,
                        channel = self.channel.__tablename__
                    )
                    ,
                    ["start", "channel"]
                )
    
    def calculate_air_time(self, original, new):
        # Calculate the time difference between the original and new air times
        time_diff = new - original

        # Adjust the start and end times of the program by the time difference
        adjusted_start = original + time_diff
        adjusted_end = original + time_diff

        return adjusted_start, adjusted_end
    
    def get_initalization_values(self, date:datetime, weeks):
        iso_date = date.isocalendar()

        current_week = iso_date.week

        return current_week, current_week + weeks
    
    def same_iso_week_this_year(self, dt: date, target_year: int = None) -> date:
        if target_year is None:
            target_year = date.today().isocalendar().year
        
        _, week, weekday = dt.isocalendar()
        new_date = date.fromisocalendar(target_year, week, weekday)
        return dt.replace(year=new_date.year, month=new_date.month, day=new_date.day)
        
    def fetch_metadata(self, url):
        metadata = self.metadata._fetch_ytdlp_info(url)
        return self.metadata.extract_episode_info_from_ytdlp(metadata)



