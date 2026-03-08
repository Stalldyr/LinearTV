try: 
    from .tvcore.tvdownloader import TVDownloader
    from .tvcore.metadatafetcher import MetaDataFetcher
    from .tvcore.tvdatabase import TVDatabase
    from .tvcore.filehandler import TVFileHandler
    from .tvcore.mediapathmanager import MediaPathManager
    from .tvcore.tvconstants import *
except ImportError:
    from tvcore.tvdownloader import TVDownloader
    from tvcore.metadatafetcher import MetaDataFetcher
    from tvcore.tvdatabase import TVDatabase, Episode, Schedule
    from tvcore.filehandler import TVFileHandler
    from tvcore.mediapathmanager import MediaPathManager
    from tvcore.tvconstants import *

from datetime import datetime, date, timedelta
import sys
from colorama import Fore, Style
import time
import logging

from slugify import slugify

logging.basicConfig(level=logging.DEBUG)

class TVPreparer():
    """
    Preparation for new week in the schedule.
    """

    def __init__(self):
        self.paths = MediaPathManager()
        self.database = TVDatabase()
        self.downloader = TVDownloader()
        self.handler = TVFileHandler()
        self.metadata = MetaDataFetcher()

    def cleanup_obsolete_episodes(self):
        obsolete_programs = self.database.get_obsolete_programs()

        if not obsolete_programs:
            print(f"No programs to delete")
        
        for entry in obsolete_programs:
            try:
                path = self.paths.get_full_path(entry.filepath)
                self.handler.delete_media(entry.id, path)
                print(Fore.GREEN + "Deletion successful: " + Style.RESET_ALL, entry.filepath)
            
            except Exception as e:
                logging.error(f"Error deleting {entry.filepath}:", e)
                print(Fore.RED + "Deletion failed: "+ Style.RESET_ALL, entry.filepath)

    def enrich_metadata(self):
        self.enrich_series_metadata()

        self.enrich_episode_metadata()

        self.database.update_end_time()
    
    def enrich_series_metadata(self, overturn = False):
        series = self.database.get_all_series(overturn)

        for entry in series:
            if entry.source_url:
                series_data = self.metadata.get_ytdlp_series_metadata(entry)

            if entry.tmdb_id:
                pass
                #tmdb_data = self.metadata.fetch_tmdb_series_data(entry.tmdb_id)

    def enrich_episode_metadata(self, overwrite=[]):
        episodes = self.database.get_all_episodes(True)
        
        for episode in episodes:
            if episode.source_url:   
                json_name = self.paths.create_ytdlp_episode_json_name2(episode.series.id, episode.id)
                json_path = self.paths.get_metadata_path(TYPE_SERIES, episode.series.slug, json_name)

                episode_data = self.metadata.get_ytdlp_episode_metadata(json_path=json_path, video_url=episode.source_url)

                relevant_data = self.metadata.extract_episode_info_from_ytdlp(episode_data)

                self.database.upsert(Episode(id=episode.id,**relevant_data))
                
            if episode.tmdb_id:
                pass

    def download_weekly_schedule(self, buffer_days=3):
        now = date.today()

        pending_programs = [
            entry
            for day in range(buffer_days)
            for entry in self.database.get_pending_programs(date=now + timedelta(days=day))
        ]

        if not pending_programs:
            print("No new episodes to download")

        for entry in pending_programs:
            slug = None
            file_path = None
            status = None
            source_url = None

            if entry.episode_id and entry.episode.series.id and entry.episode.source_url:
                if entry.episode.series.slug:
                    slug = entry.episode.series.slug
                else:
                    slug = slugify(entry.episode.series.title)

                source_url = entry.episode.source_url

                filename = self.paths.create_episode_file_name2(
                    entry.episode.series.id,
                    entry.episode.id
                )
                file_path = self.paths.get_filepath(TYPE_SERIES, slug, filename)

            elif entry.movie_id and entry.movie.source_url:
                if entry.movie.slug:
                    slug = entry.movie.slug
                else:
                    slug = slugify(entry.movie.title)

                source_url = entry.movie.source_url
                    
                filename = self.paths.create_movie_file_name2(entry.movie_id)
                file_path = self.paths.get_filepath(TYPE_MOVIES, slug, filename)
                
            else:
                print("Missing media ID or source URL for entry, skipping download:", entry.id)
                continue
                
            
            if file_path.exists():
                print(f"Local file found for {file_path}, skipping download.")
                status = STATUS_AVAILABLE
                self.database.upsert(Schedule(id=entry.id, status = STATUS_AVAILABLE))
            else:
                status = self.downloader.download_single(entry.id, source_url, file_path)

            
            if status == STATUS_AVAILABLE:
                self.handler.update_file_info(entry.id, file_path)
            
            time.sleep(1)

    def verify_scheduled_programs(self, buffer_days=3):
        now = date.today()

        scheduled_programs = [
            entry
            for day in range(buffer_days)
            for entry in self.database.get_scheduled_programs(date=now + timedelta(days=day))
        ]

        if not scheduled_programs:
            print("No programs to verify")

        for entry in scheduled_programs:
            file_path = None
            if entry.filepath:
                file_path = self.paths.get_full_path(entry.filepath)

            elif entry.episode_id: 
                filename = self.paths.create_episode_file_name2(
                    entry.episode.series.id,
                    entry.episode.id
                )
                file_path = self.paths.get_filepath(TYPE_SERIES, entry.episode.series.slug, filename)
                        
            elif entry.movie_id: 
                filename = self.paths.create_movie_file_name(entry.movie.slug)
                file_path = self.paths.get_filepath(TYPE_MOVIES, entry.movie.slug, filename)

            file_status = self.handler.verify_local_file(entry.id, file_path)
            
            #TODO Check file integrity series_dl._check_file_integrity()

            if file_status == STATUS_AVAILABLE:
                print(Fore.GREEN + "File found: " + Style.RESET_ALL, file_path)
            else:
                print(Fore.RED + "File missing: "+ Style.RESET_ALL, file_path)

            self.handler.update_file_info(entry.id, file_path)

if __name__ == "__main__":
    prep = TVPreparer()

    if len(sys.argv)>1:
        operation = sys.argv[1]

        if operation == "delete":
            prep.cleanup_obsolete_episodes()
        
        elif operation == "metadata":
            prep.enrich_metadata()

        elif operation == "download":
            prep.download_weekly_schedule()

        elif operation == "verify":
            prep.verify_scheduled_programs()

        elif operation == "all":
            prep.cleanup_obsolete_episodes()
            prep.download_weekly_schedule()
            prep.verify_scheduled_programs()

        else:
            print("Not a valid operation")