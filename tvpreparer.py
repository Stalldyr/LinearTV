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
    from tvcore.tvdatabase import TVDatabase, Episode
    from tvcore.filehandler import TVFileHandler
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
    
    def enrich_series_metadata(self, overturn = False):
        series = self.database.get_all_series(overturn)

        for entry in series:
            if entry.source_url:
                series_data = self.metadata.get_ytdlp_series_metadata(entry)

            if entry.tmdb_id:
                tmdb_data = self.metadata.fetch_tmdb_series_data(entry.tmdb_id)

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

    def download_weekly_schedule(self):
        pending_episodes = self.database.get_pending_programs()

        for entry in pending_episodes:

            if entry.episode_id and entry.episode.source_url:  
                filename = self.paths.create_episode_file_name2(
                    entry.episode.series.id,
                    entry.episode.id
                )
                file_path = self.paths.get_filepath(TYPE_SERIES, entry.episode.series.slug, filename)
                status = self.downloader.download_single(entry.id, entry.episode.source_url, file_path)

            elif entry.movie_id and entry.episode.source_url:
                filename = self.paths.create_movie_file_name(entry.movie.slug)
                file_path = self.paths.get_filepath(TYPE_MOVIES, entry.movie.slug, filename)
                status = self.downloader.download_single(entry.id, entry.movie.source_url, file_path)
            else:
                print("No source available")
                continue
                
            """
            if file_path.exists():
                print(f"Local file found for {filename}, skipping download.")
                status = STATUS_AVAILABLE
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
                status = self.downloader.download_single(entry["id"], TYPE_MOVIES, entry["source_url"], file_path)
            """
            
            if status == STATUS_AVAILABLE:
                self.handler.update_file_info(entry.id, file_path)
            
            time.sleep(1)

    def verify_files_for_scheduled_media(self):
        programs = self.database.get_scheduled_programs()

        for entry in programs:
            file_path = None
            if entry.filepath:
                file_path = entry.filepath

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
            prep.verify_files_for_scheduled_media()

        elif operation == "all":
            prep.cleanup_obsolete_episodes()
            prep.download_weekly_schedule()
            prep.verify_files_for_scheduled_media()

        else:
            print("Not a valid operation")