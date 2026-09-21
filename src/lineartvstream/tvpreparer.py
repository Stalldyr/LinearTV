from lineartvstream.tvcore.tvdownloader import TVDownloader
from lineartvstream.tvcore.metadatafetcher import MetaDataFetcher
from lineartvstream.tvcore.metadataenricher import MetadataEnricher
from lineartvstream.tvcore.tvdatabase import Movie, TVDatabase, Episode, Schedule, Channels
from lineartvstream.tvcore.filehandler import TVFileHandler
from lineartvstream.tvcore.mediapathmanager import MediaPathManager
from lineartvstream.tvcore.nrkmanager import NRKManager, check_for_duplicate_titles
from lineartvstream.tvcore.helper import get_iso_week_span_target_year, get_iso_week_number
from lineartvstream.tvcore.tvconstants import *
from lineartvstream.tvcore.appdirs import get_config_dir

from datetime import date, timedelta
import sys
from time import sleep
import logging
from slugify import slugify
from pathlib import Path

log_path = Path(get_config_dir()) / "logs" / "preparer.log"
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
        self.enricher = MetadataEnricher()

    def cleanup_obsolete_episodes(self):
        obsolete_programs = self.database.get_obsolete_programs()

        if not obsolete_programs:
            logging.info("No programs to delete")
            return
        
        for entry in obsolete_programs:
            try:
                if entry.episode_id:
                    self.handler.delete_episode_files(entry.episode)
                elif entry.movie_id:
                    self.handler.delete_movie_files(entry.movie)

                self.database.upsert(Schedule(id=entry.schedule_id, status=STATUS_DELETED, file_size=None, download_date=None, filepath=None))
                logging.info("Deletion successful: %s", entry.filepath)
            
            except Exception as e:
                logging.error("Error deleting %s: %s", entry.filepath, e)

    def fetch_nrk_data(self, buffer_weeks:int=4):
        week_number = get_iso_week_number(date.today())
        start_date, end_date = get_iso_week_span_target_year(week_number, week_number + buffer_weeks, 2001)
        
        nrk1 = NRKManager("nrk1")
        nrk2 = NRKManager("nrk2")

        self.database.upsert_on_column(Channels(channel_id="nrk1", display_name="NRK1"), [Channels.channel_id])
        self.database.upsert_on_column(Channels(channel_id="nrk2", display_name="NRK2"), [Channels.channel_id])

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
        episodes = self.database.get_episodes(missing=False)
        
        for episode in episodes:
            if episode.source_url:
                try: 
                    self.enricher.enrich_ytdlp_episode_metadata(
                        episode.source_url,
                        episode.series.slug,
                        episode.series.series_id,
                        episode.episode_id
                    )
                except Exception as e:
                    logging.error("Failed to fetch YTDLP metadata for episode %s: %s", episode.episode_id, e)
                
            if episode.tmdb_id:
                try:
                    self.enricher.enrich_tmdb_episode_metadata(
                        episode.series.slug,
                        episode.tmdb_id,
                        episode.series.series_id,
                        episode.episode_id
                    )

                except Exception as e:
                    logging.error("Failed to fetch TMDB metadata for episode %s: %s", episode.episode_id, e)

        movies = self.database.get_movies(missing=False)

        for movie in movies:
            if movie.source_url:
                try: 
                    self.enricher.enrich_ytdlp_movie_metadata(
                        movie.source_url,
                        movie.slug,
                        movie.movie_id
                    )
    
                except Exception as e:
                    logging.error("Failed to fetch YTDLP metadata for movie %s: %s", movie.movie_id, e)
                
            if movie.tmdb_id:
                json_path = self.paths.get_metadata_path(
                    TYPE_MOVIES, 
                    movie.slug, 
                    self.paths.create_tmbd_movie_json_name(movie.tmdb_id)
                )

                try:
                    movie_data = self.metadata.get_tmdb_movie_data(tmdb_id=movie.tmdb_id, json_path = json_path)
                    relevant_data = self.metadata.extract_movie_info_from_tmdb(movie_data)

                    self.database.upsert(Movie(id=movie.movie_id,**relevant_data.model_dump()))

                except Exception as e:
                    logging.error("Failed to fetch TMDB metadata for movie %s: %s", movie.movie_id, e)

    def resolve_duplicate_broadcasts(self, buffer_days=3, buffer_time=3, delete_duplicates=False):
        now = date.today()
        channels = self.database.get_channels()

        for channel in channels:
            schedule = [
                entry
                for day in range(buffer_days)
                for entry in self.database.get_schedule(channel=channel.channel_id, date = now + timedelta(days=day))
            ]

            schedule.sort(key=lambda e: e.start)

            i = 0
            while i < len(schedule):
                s1 = schedule[i]
                j = i + 1
                while j < len(schedule):
                    s2 = schedule[j]

                    if s1.end <= s2.start + timedelta(minutes=buffer_time):
                        break

                    if delete_duplicates:
                        self.database.delete(Schedule(id=s2.schedule_id))

                    logging.info(
                        "Overlapping broadcast: schedule %s %s (channel %s, start %s) overlaps with schedule %s %s",
                        s2.schedule_id, s2.title, channel, s2.start, s1.schedule_id, s1.title
                    )
                    schedule.pop(j)

                i += 1

    def download_weekly_schedule(self, buffer_days=3):
        now = date.today()

        pending_programs = [
            entry
            for day in range(buffer_days)
            for entry in self.database.get_pending_programs(date = now + timedelta(days=day))
        ]

        if not pending_programs:
            logging.info("No new episodes to download")

        for entry in pending_programs:
            slug = None
            file_path = None
            status = None
            source_url = None

            if entry.episode_id and entry.episode.series.series_id and entry.episode.source_url:
                if entry.episode.series.slug:
                    slug = entry.episode.series.slug
                else:
                    slug = slugify(entry.episode.series.title)

                source_url = entry.episode.source_url

                filename = self.paths.create_episode_file_name(
                    entry.episode.series.series_id,
                    entry.episode.episode_id
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
                logging.warning("Missing media ID or source URL for entry, skipping download: %s", entry.schedule_id)
                continue
                            
            if file_path.exists():
                logging.info("Local file found for %s, skipping download.", file_path)
                self.database.upsert(Schedule(id=entry.schedule_id, status=STATUS_AVAILABLE))
            else:
                try:
                    download_path = self.paths.get_download_path(filename)
                    status = self.downloader.download_single(entry.schedule_id, source_url, download_path)

                    download_path.rename(file_path)

                    self.database.upsert(Schedule(id=entry.schedule_id, status=STATUS_AVAILABLE))

                except Exception as e:
                    logging.error("Error while downloading: %s", e)
                    continue

            
            self.handler.update_file_info(entry.schedule_id, file_path)
            
            sleep(10)

    def verify_scheduled_programs(self, buffer_days=3):
        now = date.today()

        scheduled_programs = [
            entry
            for day in range(buffer_days)
            for entry in self.database.get_schedule(date=now + timedelta(days=day))
        ]

        if not scheduled_programs:
            logging.info("No programs to verify")

        for entry in scheduled_programs:
            file_path = None
            if entry.filepath:
                file_path = self.paths.get_full_media_path(entry.filepath)

            elif entry.episode_id: 
                filename = self.paths.create_episode_file_name(
                    entry.episode.series.series_id,
                    entry.episode.episode_id
                )
                file_path = self.paths.get_filepath(TYPE_SERIES, entry.episode.series.slug, filename)
                        
            elif entry.movie_id: 
                filename = self.paths.create_movie_file_name(entry.movie_id)
                file_path = self.paths.get_filepath(TYPE_MOVIES, entry.movie.slug, filename)

            try:
                file_status = self.handler.verify_local_file(entry.schedule_id, file_path)
            except Exception as e:
                logging.error("Error veryifing file %s: %s", file_path, e)

            if file_status == STATUS_AVAILABLE:
                logging.info("File found: %s", file_path)
            else:
                logging.warning("File missing: %s", file_path)


            self.handler.update_file_info(entry.schedule_id, file_path)

def main():
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

        elif operation == "sync":
            prep.cleanup_obsolete_episodes()
            prep.download_weekly_schedule()
            prep.verify_scheduled_programs()

        elif operation == "refresh":
            prep.fetch_nrk_data()
            prep.enrich_metadata()
            prep.resolve_duplicate_broadcasts()

        else:
            print("Not a valid operation")


if __name__ == "__main__":
    main()