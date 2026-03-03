from nrkscraper.nrk_db import NRKSession, NRKdb, NRK1, NRK2, T
from tvstreamer.tvcore.metadatafetcher import MetaDataFetcher
from tvstreamer.tvcore.programmanager import ProgramManager
#from tvstreamer.tvcore.tvdatabase import TVDatabase
from tvstreamer.tvcore.tvdatabasealchemy import TVDatabaseAlch, Series, Movie, Episode, Schedule
from tvstreamer.tvcore.tvconstants import *
import isodate
from datetime import datetime
from time import sleep

from typing import TypeVar, Type, Generic

class NRKManager(Generic[T]):
    def __init__(self, db_path: str, channel: Type[T],  debug: bool = False):
        self.Session = NRKSession(db_path, debug)
        self.metadata = MetaDataFetcher()
        self.programmanager = ProgramManager()
        self.db = TVDatabaseAlch()
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

            print(programs)

        for program in programs:
            series_id = None
            episode_id = None
            movie_id = None

            duration_dt = isodate.parse_duration(program.duration)
            duration = duration_dt.total_seconds()
            end = program.planned_start + duration_dt

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
                        release = program.planned_start
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
                        description = program.description
                    )
                    ,
                    ["program_id"]
                )

            self.db.add(
                    Schedule(
                        title = program.title,
                        series_id = series_id,
                        episode_id = episode_id,
                        movie_id = movie_id,
                        start = program.planned_start,
                        end = end,
                        rerun = program.rerun,
                        channel = self.channel.__tablename__
                    )
                    ,
                    ["start", "channel"]
                )
            

    def insert_series(self, start, end):
        with self.Session() as session:
            db = NRKdb(session, NRK1)
            programs = db.get_nrk_web_by_dates(start, end)

        for program in programs:
            print(program.series_title)


    def fetch_metadata(self, url):
        metadata = self.metadata._fetch_ytdlp_info(url)
        return self.metadata.extract_episode_info_from_ytdlp(metadata)

