from tvstreamer.tvcore.metadatafetcher import MetaDataFetcher
from tvstreamer.tvcore.programmanager import ProgramManager
from tvstreamer.tvcore.tvdatabase import TVDatabase, Series, Movie, Episode, Schedule
from tvstreamer.tvcore.tvconstants import *
from tvstreamer.tvcore.schemas import NRKInput

from slugify import slugify
import requests
from pydantic_core import ValidationError
from datetime import timedelta

class NRKManager():
    def __init__(self, channel:str, debug:bool = False):
        self.metadata = MetaDataFetcher()
        self.programmanager = ProgramManager()
        self.db = TVDatabase()
        self.channel = channel
    
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
                        channel = self.channel
                    )
                    ,
                    ["start", "channel"]
                )
            
    def insert_programs(self, programs: list[NRKInput]):
        for program in programs:
            self.insert_database(program)
        
    def api_request(self, channel, date):
        return requests.get(f"https://psapi.nrk.no/epg/{channel}?date={date}")
    
    def fetch_programs_by_date(self, date):
        data = self.api_request(self.channel, date).json()

        entries = data[0]["entries"]
        programs = []

        for entry in entries:
            epgentries = entry.get("epgEntries")

            if epgentries:
                for epgentry in epgentries:
                    data = self._validate_input(epgentry)
                    data.channel = self.channel
                    programs.append(data)

            else:
                data = self._validate_input(entry)
                data.channel = self.channel
                programs.append(data)

        return programs

    def _validate_input(self, data:dict):
        try:
            return NRKInput.model_validate(data)
        except ValidationError as e:
            raise

def check_for_duplicate_titles(programs:list[NRKInput]) -> list[tuple[NRKInput, NRKInput]]:
    duplicates = []
    programs.sort(key=lambda p: p.start)
    
    for i, program in enumerate(programs):
        if program.availability.status == "available":
            for other in programs[i+1:]:
                if other.start - program.start > timedelta(days=7):
                    break

                if other.availability.status != "available" and program.title == other.title:
                    duplicates.append((program, other))
    
    return duplicates
