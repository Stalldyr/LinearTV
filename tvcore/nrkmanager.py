from nrkscraper.nrk_db import NRKSession, NRKdb, NRK1, NRK2, T
from tvstreamer.tvcore.metadatafetcher import MetaDataFetcher
from tvstreamer.tvcore.programmanager import ProgramManager
from tvstreamer.tvcore.tvdatabase import TVDatabase, Series, Movie, Episode, Schedule
from tvstreamer.tvcore.tvconstants import *

from tvstreamer.tvcore.schemas import NRKInput
import isodate
from datetime import datetime, date, timedelta
from time import sleep
from slugify import slugify
import requests
import logging
from pydantic_core import ValidationError

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

    def get_nrk_from_db(self, start, end):
        with self.Session() as session:
            db = NRKdb(session, self.channel)
            return db.get_available_nrk_web_programs_by_dates(start, end)
    
    def insert_database(self, program: NRKInput):
        if program.availability.status == "available":
            episode_id = None
            movie_id = None
            if program.series_id:
                series_id = self.db.add(
                    Series(
                        slug = program.series_id,
                        title = program.series_title,
                        genre = program.category.display_value
                    ),
                    ["slug"]
                )

                episode_id = self.db.add(
                    Episode(
                        series_id = series_id,
                        title = program.title,
                        description = program.description,
                        duration = program.duration,
                        program_id = program.program_id,
                        source_url = program.source_url
                    ),
                    ["program_id"]
                )

            else:
                movie_id = self.db.add(
                    Movie(
                        title = program.title,
                        program_id = program.program_id,
                        genre = program.category.display_value,
                        duration = program.duration,
                        description = program.description,
                        source_url = program.source_url,
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
                        original_start = program.original_start,
                        start = program.start,
                        end = program.end,
                        rerun = program.rerun,
                        channel = self.channel.__tablename__
                    )
                    ,
                    ["start", "channel"]
                )
    
    def fetch_metadata(self, url):
        metadata = self.metadata._fetch_ytdlp_info(url)
        return self.metadata.extract_episode_info_from_ytdlp(metadata)
    
    def api_request(self, channels, date, source="https://psapi.nrk.no/epg/{channels}?date={date}"):
        return requests.get(f"https://psapi.nrk.no/epg/{channels}?date={date}")
    
    def fetch_programs_by_date(self, date):
        data = self.api_request(self.channel.__tablename__, date).json()

        entries = data[0]["entries"]
        
        for entry in entries:
            epgentries = entry.get("epgEntries")

            if epgentries:
                for epgentry in epgentries:
                    data = self.validate_input(epgentry)
                    self.insert_database(data)

            else:
                data = self.validate_input(entry)
                self.insert_database(data)

    def validate_input(self, data:dict):
        try:
            return NRKInput.model_validate(data)
        except ValidationError as e:
            print(e)


    def insert_database_from_api(self, current_date, end_date):
        while current_date <= end_date:
            self.fetch_programs_by_date(current_date)
            current_date += timedelta(days=1)

            sleep(1)




