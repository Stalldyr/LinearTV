try: 
    from .tvcore.tvdownloader import TVDownloader
    from .tvcore.metadatafetcher import MetaDataFetcher
    from .tvcore.tvdatabase import TVDatabase, Episode, Schedule
    from .tvcore.filehandler import TVFileHandler
    from .tvcore.mediapathmanager import MediaPathManager
    from .tvcore.nrkmanager import NRKManager, check_for_duplicate_titles
    from .tvcore.calendar import get_iso_week_span_target_year, get_iso_week_number
    from .tvcore.tvconstants import *
except ImportError:
    from tvcore.tvdownloader import TVDownloader
    from tvcore.metadatafetcher import MetaDataFetcher
    from tvcore.tvdatabase import TVDatabase, Episode, Schedule
    from tvcore.filehandler import TVFileHandler
    from tvcore.mediapathmanager import MediaPathManager
    from tvcore.nrkmanager import NRKManager, check_for_duplicate_titles
    from tvcore.calendar import get_iso_week_span_target_year, get_iso_week_number
    from tvcore.tvconstants import *

from datetime import datetime, date, timedelta
import sys
from colorama import Fore, Style
from time import sleep
import logging
from slugify import slugify
from pathlib import Path

log_path = Path(__file__).parent / "logs" / "preparer.log"
log_path.parent.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)

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
            logging.info("No programs to delete")
            return
        
        for entry in obsolete_programs:
            #TODO: Implement deletion of metadata
            try:
                media_path = self.paths.get_full_path(entry.filepath)
                self.handler.delete_media(entry.id, media_path)
                logging.info("Deletion successful: %s", entry.filepath)
            
            except Exception as e:
                logging.error("Error deleting %s: %s", entry.filepath, e)

    def fetch_nrk_data(self, buffer_weeks=4):
        week_number = get_iso_week_number(date.today())
        start_date, end_date = get_iso_week_span_target_year(week_number, week_number + buffer_weeks, 2001)
        
        nrk1 = NRKManager("nrk1")
        nrk2 = NRKManager("nrk2")

        nrk1_programs = []
        nrk2_programs = []
        current_date = start_date
        while current_date <= end_date:
            try:
                nrk1_programs += nrk1.fetch_programs_by_date(current_date)
            except Exception as e:
                logging.error("Failed to fetch NRK1 programs for %s: %s", current_date, e)
            sleep(1)

            try:
                nrk2_programs += nrk2.fetch_programs_by_date(current_date)
            except Exception as e:
                logging.error("Failed to fetch NRK2 programs for %s: %s", current_date, e)
            sleep(1)
            
            current_date += timedelta(days=1)

        nrk1.insert_programs(nrk1_programs)
        nrk2.insert_programs(nrk2_programs)

        duplicates = check_for_duplicate_titles(nrk1_programs + nrk2_programs)
        logging.info("Duplicates between %s and %s:", start_date, end_date)
        for original, rerun in duplicates:
            logging.info("%s: %s %s -> %s %s", original.title, original.channel, original.start, rerun.channel, rerun.start)

    def enrich_metadata(self):
        self.enrich_episode_metadata()
        self.database.update_end_time()
    
    def enrich_episode_metadata(self, overwrite=[]):
        episodes = self.database.get_episodes(missing=True)
        
        for episode in episodes:
            if episode.source_url:
                json_path = self.paths.get_metadata_path(
                    TYPE_SERIES, 
                    episode.series.slug, 
                    self.paths.create_ytdlp_episode_json_name(episode.series.id, episode.id)
                )

                episode_data = self.metadata.get_ytdlp_data(episode.source_url, json_path = json_path)
                relevant_data = self.metadata.extract_episode_info_from_ytdlp(episode_data)

                self.database.upsert(Episode(id=episode.id,**relevant_data.model_dump()))
                
            if episode.tmdb_id:
                json_path = self.paths.get_metadata_path(
                    TYPE_SERIES, 
                    episode.series.slug, 
                    self.paths.create_tmbd_episode_json_name(episode.series.id, episode.id)
                )

                episode_data = self.metadata.get_tmdb_data(tmdb_id=episode.tmdb_id, json_path = json_path)
                relevant_data = self.metadata.extract_episode_info_from_ytdlp(episode_data)

                self.database.upsert(Episode(id=episode.id,**relevant_data.model_dump()))



    def download_weekly_schedule(self, buffer_days=3):
        now = date.today()

        pending_programs = [
            entry
            for day in range(buffer_days)
            for entry in self.database.get_pending_programs(date=now + timedelta(days=day))
        ]

        if not pending_programs:
            logging.info("No new episodes to download")

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

                filename = self.paths.create_episode_file_name(
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
                    
                filename = self.paths.create_movie_file_name(entry.movie_id)
                file_path = self.paths.get_filepath(TYPE_MOVIES, slug, filename)
                
            else:
                logging.warning("Missing media ID or source URL for entry, skipping download: %s", entry.id)
                continue
                            
            if file_path.exists():
                logging.info("Local file found for %s, skipping download.", file_path)
                status = STATUS_AVAILABLE
                self.database.upsert(Schedule(id=entry.id, status = status))
            else:
                try:
                    status = self.downloader.download_single(entry.id, source_url, file_path)
                except Exception as e:
                    logging.error("Error while downloading: %s", e)

            
            if status == STATUS_AVAILABLE:
                self.handler.update_file_info(entry.id, file_path)
            
            sleep(10)

    def verify_scheduled_programs(self, buffer_days=3):
        now = date.today()

        scheduled_programs = [
            entry
            for day in range(buffer_days)
            for entry in self.database.get_scheduled_programs(date=now + timedelta(days=day))
        ]

        if not scheduled_programs:
            logging.info("No programs to verify")

        for entry in scheduled_programs:
            file_path = None
            if entry.filepath:
                file_path = self.paths.get_full_path(entry.filepath)

            elif entry.episode_id: 
                filename = self.paths.create_episode_file_name(
                    entry.episode.series.id,
                    entry.episode.id
                )
                file_path = self.paths.get_filepath(TYPE_SERIES, entry.episode.series.slug, filename)
                        
            elif entry.movie_id: 
                filename = self.paths.create_movie_file_name(entry.movie.slug)
                file_path = self.paths.get_filepath(TYPE_MOVIES, entry.movie.slug, filename)

            try:
                file_status = self.handler.verify_local_file(entry.id, file_path)
            except Exception as e:
                logging.error("Error veryifing file %s: %s", file_path, e)


            #TODO Check file integrity series_dl._check_file_integrity()

            if file_status == STATUS_AVAILABLE:
                logging.info("File found: %s", file_path)
            else:
                logging.warning("File missing: %s", file_path)


            self.handler.update_file_info(entry.id, file_path)

def _status_helper(status, level, succes, failure, file_path):
    if status == STATUS_AVAILABLE:
        print(Fore.GREEN + "File found: " + Style.RESET_ALL, file_path)
    else:
        print(Fore.RED + "File missing: "+ Style.RESET_ALL, file_path)



if __name__ == "__main__":

    prep = TVPreparer()

    if len(sys.argv)>1:
        operation = sys.argv[1]

        if operation == "delete":
            prep.cleanup_obsolete_episodes()

        elif operation == "fetch":
            prep.fetch_nrk_data()
        
        elif operation == "metadata":
            prep.enrich_metadata()

        elif operation == "download":
            prep.download_weekly_schedule()

        elif operation == "verify":
            prep.verify_scheduled_programs()

        elif operation == "daily":
            prep.cleanup_obsolete_episodes()
            prep.download_weekly_schedule()
            prep.verify_scheduled_programs()

        elif operation == "weekly":
            prep.fetch_nrk_data()
            prep.enrich_metadata()

        else:
            print("Not a valid operation")

