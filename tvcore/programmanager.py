from .tvdatabase import TVDatabase
from .metadatafetcher import MetaDataFetcher
from .tvconstants import *
from .helper import create_path_friendly_name, calculate_time_blocks, calculate_end_time

class ProgramManager:
    """
        Works as a manager between flask and the database
    """
    def __init__(self):
        self.db = TVDatabase()
        self.metadatafetcher = MetaDataFetcher()

    def create_or_update_program(self, data:dict):
        """
            Handle the complete workflow of adding or updating a program.
            
            Args:
                program_data: Dict with all program information from web form
                
            Returns:
                tuple: (success: bool, message: str)
        """
        
        program_type = data.pop("program_type")
        program_id = data.pop("id")
        program_name = data.get("name", None)

        print(data)
        print(program_name)

        if not program_name:
            print("Missing program name")
            return False, "Missing program name"

        if program_type == TYPE_SERIES:
            season = data.get("season")
            episode = data.get("episode")
            if not season or not episode:
                print("Missing season and/or episode for series")
                return False, "Series requires season and episode"

        directory = create_path_friendly_name(program_name)
        data["directory"] = directory

        source_url = data.get("source_url", None)
        tmdb_id = data.get("tmdb_id", None)

        if source_url and program_type == TYPE_SERIES:
            try:
                self.metadatafetcher.get_ytdlp_season_metadata(program_type, directory, season, video_url=source_url)
                
            except Exception as e:
                print(f"Error recieving ytdlp metadata: {e}")            

        if tmdb_id:
            try:
                self.metadatafetcher.get_tmdb_metadata(program_type, directory, tmdb_id, season)
                
            except Exception as e:
                print(f"Error recieving tmdb metadata: {e}")

        if program_type == TYPE_SERIES:
            total_episodes = self.metadatafetcher.get_season_episode_count(directory, season, source_url, tmdb_id)
            data["total_episodes"] = total_episodes

        try:
            if program_id:
                self.db.update_program(program_type, program_id, **data)
            else:
                self.db.add_program(program_type, **data)
            
            return True, "Program saved successfully"
        
        except Exception as e:
            print(f"Error while saving: {e}")
            return False, f"Database error: {str(e)}", 500
        
    def delete_program(self, program_id, program_type):
        try:
            success = self.db.delete_program(program_id, program_type)
            
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

        try:
            existing = self.db.get_schedule_by_time(data["day_of_week"], data["start_time"])

            if len(existing) == 1:
                if data["name"] == "[Ledig]":
                    self.db.delete_schedule_by_id(existing[0]["id"])

                    return True, f"Removed program {data['name']} from schedule at {data['day_of_week']} {data['start_time']}"

                else:
                    conditions = {
                        "day_of_week": data["day_of_week"], 
                        "start_time": data["start_time"]
                    }

                    data["end_time"] = calculate_end_time(data["start_time"], data["duration"])
                    data["blocks"] = calculate_time_blocks(data["duration"])
                    data.pop("duration", None)

                    self.db.edit_schedule(conditions, data)

                    return True, f"Edited program {data['name']} in schedule at {data['day_of_week']} {data['start_time']}"
            
            elif len(existing) == 0:
                data["end_time"] = calculate_end_time(data["start_time"], data["duration"])
                data["blocks"] = calculate_time_blocks(data["duration"])
                data.pop("duration", None)
                
                self.db.add_schedule_entry(data)

                return True, f"Saved new program {data['name']} to schedule at {data['day_of_week']} {data['start_time']}"
            
            else:
                return False, "Error: Multiple programs are saved to the same time"
            
        except Exception as e:
            return False, f"Database error: {str(e)}", 500
        
    def initialize_admin_page(self):
        schedule_data = self.db.get_weekly_schedule()
        series_data = self.db.get_all_series()
        movie_data = self.db.get_all_movies()

        for series in series_data:
            series['blocks'] = calculate_time_blocks(series['duration'])

        return schedule_data, series_data, movie_data

    
    def get_video_file(self):
        pass

