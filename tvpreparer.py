try: 
    from .tvcore.tvdownloader import TVDownloader
    from .tvcore.metadatafetcher import MetaDataFetcher
    from .tvcore.tvdatabase import TVDatabase
    from .tvcore.tvhandler import TVFileHandler
    from .tvcore.mediapathmanager import MediaPathManager
    from .tvcore.tvconstants import *
except ImportError:
    from tvcore.tvdownloader import TVDownloader
    from tvcore.metadatafetcher import MetaDataFetcher
    from tvcore.tvdatabase import TVDatabase
    from tvcore.tvhandler import TVFileHandler
    from tvcore.mediapathmanager import MediaPathManager
    from tvcore.tvconstants import *

import sys
from colorama import Fore, Style
import time
import logging

logging.basicConfig(level=logging.DEBUG)

class TVPreparer():
    """
    Preperation for new week in the schedule.
    """

    def __init__(self):
        self.paths = MediaPathManager()
        self.database = TVDatabase()
        self.downloader = TVDownloader()
        self.handler = TVFileHandler()

    def increment_episodes(self):
        """
            Increment the current episode.
            Run only once at the start of the week.
        """
        scheduled_episodes = self.database.get_scheduled_episodes()

        for e in scheduled_episodes:
            self.database.increment_episode(e['series_id'])
            print(f"Series {e["series_name"]}: Episode number incremented.")

    def update_keeping_status(self):
        """
            Sets episodes that is kept from previous week to be deleted at the end of the week.
        """

        kept_files = self.database.get_kept_episodes()

        for episode in kept_files:
            self.database.update_episode_keeping_status(episode['id'], False)
            print(f"{episode["filename"]} marked for deletion")

    def cleanup_obsolete_media(self):
        obsolete_episodes = self.database.get_obsolete_episodes()
        self._cleanup(obsolete_episodes, TYPE_SERIES)

        obsolete_movies = self.database.get_obsolete_movies()
        self._cleanup(obsolete_movies, TYPE_MOVIES)

    def _cleanup(self, data, media_type):
        data = self.database.get_obsolete_movies()

        if not data:
            print(f"No {media_type} to delete")
        
        for entry in data:
            if not entry['last_aired']:
                continue

            path = self.paths.get_filepath(media_type, entry["directory"], entry["filename"])
            self.handler.delete_media(entry["id"], path, media_type)


    def create_pending_episodes(self):
        series_list = self.database.get_scheduled_series()
        metadata_fetcher = MetaDataFetcher()

        for series in series_list:

            if series["source_url"]:
                try:
                    yt_dlp_data = metadata_fetcher.get_ytdlp_season_metadata(TYPE_SERIES, series["directory"], series["season"], video_url=series["source_url"])
                    self._create_pending(yt_dlp_data["entries"], series["season"], series["id"], series["name"])

                except Exception as e:
                    print(f"Error fetching metadata for {series["name"]}")

            elif series["tmdb_id"]:
                try:
                    tmdb_data = metadata_fetcher.get_tmdb_metadata(TYPE_SERIES, series["directory"], series["tmdb_id"], series["season"])

                    self._create_pending(tmdb_data["episodes"], series["season"], series["id"], series["name"])
                    
                except Exception as e:
                    print(f"Error fetching metadata for {series["name"]}")

            else:
                print(f"No metadata available for {series["name"]}")


    def _create_pending(self, episodes, season, series_id, series_name, ytdlp=True):
        metadata_fetcher = MetaDataFetcher()
        for entry in episodes:
            if ytdlp:
                episode_data = metadata_fetcher.extract_episode_info_from_ytdlp(entry)
            else:
                episode_data = metadata_fetcher.extract_episode_info_from_tmdb(entry)

            if not episode_data["season_number"]:
                episode_data["season_number"] = season

            existing = self.database.get_episode_by_details(series_id, episode_data["season_number"], episode_data["episode_number"])

            if existing:
                continue
            
            self.database.add_pending_episodes(**episode_data, series_id =series_id, download_date = None)

            print(f"Pending episode added for {series_name}")

    def download_weekly_schedule(self):
        pending_episodes = self.database.get_scheduled_episodes()
        print(pending_episodes)
        self._download(pending_episodes, TABLE_SERIES)

        pending_movies = self.database.get_scheduled_movies()
        self._download(pending_movies, TABLE_MOVIES)

    def _download(self, pending, media_type):
        for entry in pending:
            if entry["source"] == SOURCE_LOCAL:
                continue
            
            if media_type == TYPE_SERIES:                
                filename = self.paths.create_episode_file_name(
                    entry["directory"],
                    entry["season_number"],
                    entry["episode_number"]
                )
            elif media_type == TYPE_MOVIES:
                filename = self.paths.create_movie_file_name(entry["directory"])
            else:
                break
                
            file_path = self.paths.get_filepath(media_type, entry["directory"], filename)
            file_path_check = self.paths.get_filepath(media_type, entry["directory"], filename).exists()

            if file_path_check:
                print(f"Local file found for {filename}, skipping download.")
            elif media_type == TYPE_SERIES:
                status = self.downloader.download_from_playlist(
                    entry["id"],
                    TYPE_SERIES,
                    file_path,
                    entry["source_url"],
                    entry["episode_number"],
                    total_episodes=entry["total_episodes"],
                    reverse_order= entry["reverse_order"]
                )
            elif media_type == TYPE_MOVIES:
                status = self.downloader.download_movie(entry["id"], entry["source_url"])

            if status == STATUS_AVAILABLE:
                self.handler.update_file_info(entry["id"], media_type, file_path)
            
            time.sleep(1)

    def verify_files_for_scheduled_media(self):
        episodes = self.database.get_scheduled_episodes()
        self._verify(episodes, TYPE_SERIES)
        
        movies = self.database.get_scheduled_movies()
        self._verify(movies, TYPE_MOVIES)

    def _verify(self, data, media_type):
        for entry in data:
            if entry["filename"]:
                filename = entry["filename"]
            else:
                if media_type == TYPE_MOVIES: 
                    filename = self.paths.create_movie_file_name(entry["directory"])

                elif media_type == TYPE_SERIES: 
                    filename = self.paths.create_episode_file_name(entry["directory"], entry["season_number"], entry["episode_number"])
            
            #series_dl._check_file_integrity()

            file_path = self.paths.get_filepath(media_type, entry["directory"], filename)
            file_status = self.handler.verify_local_file(entry["id"], file_path, media_type)

            if file_status == STATUS_AVAILABLE:
                print(Fore.GREEN + "File found: " + Style.RESET_ALL, filename)
            else:
                print(Fore.RED + "File missing: "+ Style.RESET_ALL, filename)

            self.handler.update_file_info(entry["id"], media_type, file_path)

    def link_programs_to_schedule(self):
        scheduled_series = self.database.get_scheduled_series()

        for series in scheduled_series:
            airings = self.database.get_program_schedule_by_series_id(series["id"])

            if not airings:
                continue

            first_is_rerun = airings[0]["is_rerun"] == 1
            offset = 1 if first_is_rerun else 0
            episodes = self.database.get_scheduled_episodes_by_id(series["id"], offset)

            if not episodes:
                continue

            current_episode = None

            for idx, entry in enumerate(airings):
                if first_is_rerun and idx == 0:
                    current_episode = episodes.pop(0)
                    self.database.update_episode_keeping_status(current_episode["id"], True)
                elif entry["is_rerun"] == 0 and episodes:
                    current_episode = episodes.pop(0)
                elif not current_episode:
                    continue
                
                self.update_episode_link(
                    entry["name"], 
                    entry["id"], 
                    current_episode["id"], 
                    current_episode["status"], 
                    current_episode["season_number"], 
                    current_episode["episode_number"], 
                    current_episode["filename"], 
                    entry["day_of_week"], 
                    entry["start_time"], 
                    rerun=(entry["is_rerun"] == 1)
                )

    def update_episode_link(self, series_name, schedule_id, episode_id, episode_status, season_number, episode_number, filename, day_of_week, start_time, rerun = False):
        text = "re-run" if rerun else "original run"

        if episode_status == STATUS_AVAILABLE:
            self.database.update_episode_links(schedule_id, episode_id)
            print(Fore.GREEN + "Success:" + Style.RESET_ALL, f"Linked {text} of {series_name} (S{season_number}E{episode_number}). {filename} set to show at (day {day_of_week}, {start_time})")
        else:
            print(Fore.RED + "Failure:" + Style.RESET_ALL, f"Failed to link  {text} of {series_name} (S{season_number}E{episode_number}). {filename} scheduled to show at (day {day_of_week}, {start_time}). File is not available")

if __name__ == "__main__":
    prep = TVPreparer()

    if len(sys.argv)>1:
        operation = sys.argv[1]
        if operation == "increment":
            prep.increment_episodes()

        elif operation == "delete":
            prep.cleanup_obsolete_media()

        elif operation == "keep":
            prep.update_keeping_status()

        elif operation == "pending":
            prep.create_pending_episodes()

        elif operation == "download":
            prep.download_weekly_schedule()

        elif operation == "verify":
            prep.verify_files_for_scheduled_media()

        elif operation == "link":
            prep.link_programs_to_schedule()

        elif operation == "all":
            prep.cleanup_obsolete_media()
            prep.update_keeping_status()
            prep.create_pending_episodes()
            prep.download_weekly_schedule()
            prep.verify_files_for_scheduled_media()
            prep.link_programs_to_schedule()

        else:
            print("Not a valid operation")