from .tvdatabase import TVDatabase, Series, Episode, Movie, Schedule
from .metadatafetcher import MetaDataFetcher
from .tvconstants import *
from .helper import calculate_time_blocks, calculate_end_time
from .tvconfig import TVConfig
from slugify import slugify
from hypermedia import *
from .schemas import MovieInput, SeriesInput, EpisodeInput, ScheduleInput, ScheduleUpdate
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
            return False, "Invalid data", 400
                
        try:
            self.db.upsert(
                Series(
                    **series.model_dump(),
                    slug = slugify(series.title)
                )
            )
            
            return True, "Program saved successfully", 200
        
        except Exception as e:
            logging.error(f"Error while saving: {e}")
            return False, "Database error", 500

    def delete_series(self, series_id):
        try:
            self.db.delete(
                Series(id=series_id) 
            )

            episodes = self.db.get_episodes(series_id=series_id)

            self.db.delete_bulk(
                episodes
            )

            #TODO: Should also delete relevant files

            return True, "Program deleted successfully", 200
                    
        except Exception as e:
            logging.error(f"Error while saving: {e}")
            return False, "Database error", 500
        

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
            return False, "Invalid data", 400
        
        try:
            self.db.upsert(
                Movie(
                    **movie.model_dump(),
                    slug = slugify(movie.title)
                )
            )
            
            return True, "Program saved successfully", 200
        
        except Exception as e:
            logging.error(f"Error while saving: {e}")
            return False, "Database error", 500

        
    def delete_movie(self, movie_id):
        try:
            success = self.db.delete(
                Movie(id=movie_id) 
            )

            #TODO: Should also delete relevant files

            return True, "Program deleted successfully", 200
                    
        except Exception as e:
            logging.error(f"Error while saving: {e}")
            return False, "Database error", 500

    def save_episode(self, data:dict):
        """
        Args:
            program_data: Dict with all program information from web form
            
        Returns:
            tuple: (success: bool, message: str)
        """

        try:
            episode = EpisodeInput(**data)
        except ValidationError as e:
            logging.error("Validation failed:\n%s", e)
            return False, "Invalid data", 400
        
        try:
            self.db.upsert(
                Episode(
                    **episode.model_dump()
                )
            )
            
            return True, "Episode saved successfully", 200
        
        except Exception as e:
            logging.error(f"Error while saving: {e}")
            return False, "Database error", 500
        
    def delete_episode(self, episode_id):
        try:
            self.db.delete(
                Episode(id=episode_id) 
            )

            #TODO: Should also delete relevant files

            return True, "Program deleted successfully", 200
                    
        except Exception as e:
            logging.error(f"Error while saving: {e}")
            return False, "Database error", 500
    

    #Schedule
    def save_schedule(self, data:dict):
        """
        Save new entry in the weekly schedule
        """
        #TODO: FIX

        try:
            schedule = ScheduleInput(**data)
        except ValidationError as e:
            logging.error("Validation failed:\n%s", e)
            return False, e.errors(), 400
        
    def update_schedule(self, data:dict):
        """
        Save new entry in the weekly schedule
        """
        try:
            schedule = ScheduleUpdate(**data)
        except ValidationError as e:
            logging.error("Validation failed:\n%s", e)
            return False, e.errors(), 400
        
        try:
            self.db.upsert(
                Schedule(
                    **schedule.model_dump(exclude={"date","time"})
                )
            )
            
            return True, "Schedule saved successfully", 200
        
        except Exception as e:
            logging.error(f"Error while saving: {e}")
            return False, "Database error", 500

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
        