from .tvdatabase import Movie, TVDatabase, Series
from .metadatafetcher import MetaDataFetcher
from .tvconstants import *
from .helper import calculate_time_blocks, calculate_end_time
from .tvconfig import TVConfig
from slugify import slugify
from hypermedia import *
from .schemas import MovieInput, MovieInput, SeriesInput
import logging
from pydantic_core import ValidationError

class ProgramManager:
    """
    Works as a manager between flask/front-end and the database
    """
    def __init__(self):
        self.db = TVDatabase()
        self.config = TVConfig()
        self.metadatafetcher = MetaDataFetcher()

    # ============ CRUD OPERATIONS ============

    def save_series(self, data:dict):
        """
        Handle the complete workflow of adding or updating a program.
        
        Args:
            program_data: Dict with all program information from web form
            
        Returns:
            tuple: (success: bool, message: str)
        """

        try:
            series = SeriesInput(**data)
        except ValidationError as e:
            logging.error("Validation failed:\n%s", e)
            return False, e.errors(), 400
        
        if not series.title:
            print("Missing program name")
            return False, "Missing program name"
        
        if not series.start_episode or not series.start_episode:
            print("Missing season and/or episode for series")
            return False, "Series requires season and episode"
        

        """
        if series.source_url:
            try:
                self.metadatafetcher.get_ytdlp_season_metadata(program_type, directory, season, video_url=source_url)
                
            except Exception as e:
                print(f"Error recieving ytdlp metadata: {e}")            

        if series.tmdb_id:
            try:
                self.metadatafetcher.get_tmdb_metadata(program_type, directory, tmdb_id, season)
                
            except Exception as e:
                print(f"Error recieving tmdb metadata: {e}")
        """

        try:
            self.db.upsert(
                Series(
                    **series.model_dump(),
                    slug = slugify(series.title)
                )
            )
            
            return True, "Program saved successfully"
        
        except Exception as e:
            print(f"Error while saving: {e}")
            return False, f"Database error: {str(e)}", 500


    def save_movie(self, data:dict):
        """
        Handle the complete workflow of adding or updating a program.
        
        Args:
            program_data: Dict with all program information from web form
            
        Returns:
            tuple: (success: bool, message: str)
        """

        try:
            movie = MovieInput(**data)
        except ValidationError as e:
            logging.error("Validation failed:\n%s", e)
            return False, e.errors(), 400
        
        if not movie.title:
            print("Missing program name")
            return False, "Missing program name"
        
        """
        if series.source_url:
            try:
                self.metadatafetcher.get_ytdlp_season_metadata(program_type, directory, season, video_url=source_url)
                
            except Exception as e:
                print(f"Error recieving ytdlp metadata: {e}")            

        if series.tmdb_id:
            try:
                self.metadatafetcher.get_tmdb_metadata(program_type, directory, tmdb_id, season)
                
            except Exception as e:
                print(f"Error recieving tmdb metadata: {e}")
        """

        try:
            self.db.upsert(
                Movie(
                    **movie.model_dump(),
                    slug = slugify(movie.title)
                )
            )
            
            return True, "Program saved successfully"
        
        except Exception as e:
            print(f"Error while saving: {e}")
            return False, f"Database error: {str(e)}", 500
        
    def delete_program(self, program_id):
        try:
            success = self.db.delete(
                #Obj(program_id) 
            )
            
            if success:
                return True, "Program deleted successfully"
            
            else:
                return False, "Invalid program type"
        
        except Exception as e:
            return False, f"Database error: {str(e)}", 500
        

    def save_schedule(self, data:dict):
        """
            Save new entry in the weekly schedule

            Args:
                data: input data schedule    
        """
        #TODO: FIX

        return

        try:
            existing = self.db.get_schedule_by_time(data["day_of_week"], data["start_time"])

            if len(existing) == 1:
                conditions = {
                    "day_of_week": data["day_of_week"], 
                    "start_time": data["start_time"]
                }

                data["end_time"] = calculate_end_time(data["start_time"], data["duration"])
                data["blocks"] = calculate_time_blocks(data["duration"])
                data.pop("duration", None)

                self.db.edit_schedule(conditions, data)
                self.db.update_schedule_count()

                return True, f"Edited program {data['name']} in schedule at {data['day_of_week']} {data['start_time']}"
        
            elif len(existing) == 0:
                data["end_time"] = calculate_end_time(data["start_time"], data["duration"])
                data["blocks"] = calculate_time_blocks(data["duration"])
                data.pop("duration", None)
                
                self.db.add_schedule_entry(data)
                self.db.update_schedule_count()

                return True, f"Saved new program {data['name']} to schedule at {data['day_of_week']} {data['start_time']}"
            
            else:
                return False, "Multiple programs are saved to the same time slot"
            
        except Exception as e:
            return False, f"Database error: {str(e)}", 500
        
        
    # ============ PAGE INITIALIZATION DATA ============
        
    def initialize_admin_page(self):
        schedule_data = self.db.get_current_week_schedule()
        series_data = self.db.get_all_series()
        movie_data = self.db.get_all_movies()

        #for series in series_data:
        #    series['blocks'] = calculate_time_blocks(series)

        timeslots = self.config.get_time_slots()
        genres = sorted(self.config.get_genres())


        data = {
            "schedule_data": [obj.model_dump() for obj in schedule_data],
            "series_data": [obj.model_dump() for obj in series_data],
            "movie_data": [obj.model_dump() for obj in movie_data],
            "timeslots": timeslots,
            "genres": genres
        }
        return data
    
    def initialize_tv_guide(self):
        timeslots = self.config.get_time_slots()
        schedule = self.db.get_air_schedule()
        DAYS = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag", "Søndag"]

        def create_schedule_list(schedule) -> Element:
            return Div(
                *[Div(H1(day), create_entry(program), class_="schedule-entry") for day in DAYS for program in schedule],
                class_="schedule-list"
            )
        
        def create_entry(program) -> Element:
            return Div(
                H3(program.title),
                P(f"Start: {program.start.time()}"),
                P(f"End: {program.end.time()}"),
                P(f"Description: {program.episode.description}"),
                class_="schedule-entry"
            )

        return create_schedule_list(schedule).dump()