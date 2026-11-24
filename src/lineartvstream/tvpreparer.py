from lineartvstream.tvcore.tvdownloader import TVDownloader
from lineartvstream.tvcore.metadatafetcher import MetaDataFetcher
from lineartvstream.tvcore.metadataenricher import MetadataEnricher
from lineartvstream.tvcore.tvdatabase import Movie, TVDatabase, Schedule, Channels
from lineartvstream.tvcore.filehandler import TVFileHandler
from lineartvstream.tvcore.mediapathmanager import MediaPathManager
from lineartvstream.tvcore.nrkmanager import NRKManager, check_for_duplicate_titles
from lineartvstream.tvcore.helper import get_iso_week_span
from lineartvstream.tvcore.tvconstants import *
from lineartvstream.tvcore.tvconfig import get_config_dict

from datetime import date, timedelta
import sys
from time import sleep
import logging
from slugify import slugify
from pathlib import Path

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

    def fetch_nrk_data(self, years_back: int, buffer_weeks:int=4):
        today = date.today()
        diff = round(years_back * 365.25 / 7)
        original_date = today - timedelta(weeks=diff)
        
        start_date, end_date = get_iso_week_span(original_date, original_date + timedelta(weeks=buffer_weeks))
        
        nrk_manager = NRKManager(["nrk1", "nrk2"])

        self.database.upsert_on_column(Channels(channel_id="nrk1", display_name="NRK1"), [Channels.channel_id])
        self.database.upsert_on_column(Channels(channel_id="nrk2", display_name="NRK2"), [Channels.channel_id])

        nrk_programs = []
        current_date = start_date
        while current_date <= end_date:
            try:
                nrk_programs += nrk_manager.fetch_programs_by_date(current_date)
            except Exception as e:
                logging.error("Failed to fetch NRK programs for %s: %s", current_date, e)
            sleep(1)

            current_date += timedelta(days=1)

        nrk_manager.insert_programs(nrk_programs)

        duplicates = check_for_duplicate_titles(nrk_programs)
        logging.info("Duplicates between %s and %s:", start_date, end_date)
        for original, rerun in duplicates:
            logging.info("%s: %s %s -> %s %s", original.title, original.channel, original.start, rerun.channel, rerun.start)


    def enrich_metadata(self, missing=False):
        """
        missing: Only replaces data that is missing from the database
        """
        episodes = self.database.get_episodes(missing=missing)
        
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

    def resolve_overlapping_broadcasts(self, buffer_days=3, buffer_time=3, delete_overlaps=False):
        now = date.today()
        channels = self.database.get_channels()

        for channel in channels:
            schedule = [
                entry
                for day in range(buffer_days)
                for entry in self.database.get_schedule(channel=channel.channel_id, date = now + timedelta(days=day))
            ]

            schedule.sort(key=lambda e: e.start)

            overlaps = []
            i = 0
            while i < len(schedule):
                s1 = schedule[i]
                j = i + 1
                while j < len(schedule):
                    s2 = schedule[j]

                    if s1.end <= s2.start + timedelta(minutes=buffer_time):
                        break

                    overlaps.append((s1,s2))

                    schedule.pop(j)

                i += 1

            if not overlaps:
                logging.info("No overlaps found on channel %s", channel.display_name)

            else:
                for s1,s2 in overlaps:
                    if delete_overlaps:
                        self.database.delete(Schedule(id=s2.schedule_id))

                    logging.info(
                        "Overlapping broadcast: schedule %s %s (channel %s, start %s) overlaps with schedule %s %s",
                        s2.schedule_id, s2.title, channel.display_name, s2.start, s1.schedule_id, s1.title
                    )


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
                    self.downloader.download_single(entry.schedule_id, source_url, download_path)

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

def preparer_logging(log_dir):
    log_dir = Path(log_dir)

    log_path = log_dir / "preparer.log"
    log_path.parent.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )

def main():
    prep = TVPreparer()

    config = get_config_dict()

    refresh_config = config["refresh"]
    refresh_buffer = refresh_config["buffer_weeks"]
    missing = refresh_config["missing"]
    #target_week = config["schedule"]["target_week"]
    years_back = config["schedule"]["years_back"]

    sync_config = config["sync"]
    download_buffer = sync_config["download_buffer"]
    verify_buffer = sync_config["verify_buffer"]
    overlap = sync_config["overlap_minutes"]
    delete_overlaps = sync_config["delete_overlaps"]

    log_bool = config["logging"]

    if log_bool:
        log_dir = config["paths"]["logs"]
        preparer_logging(log_dir)

    if len(sys.argv)>1:
        operation = sys.argv[1]

        if operation == "delete":
            prep.cleanup_obsolete_episodes()

        elif operation == "download":
            prep.download_weekly_schedule(buffer_days=download_buffer)

        elif operation == "verify":
            prep.verify_scheduled_programs(buffer_days=verify_buffer)

        elif operation == "overlaps":
            prep.resolve_overlapping_broadcasts(buffer_days=verify_buffer, buffer_time=overlap, delete_overlaps=delete_overlaps)

        elif operation == "fetch":
            prep.fetch_nrk_data(years_back, buffer_weeks=refresh_buffer)
        
        elif operation == "metadata":
            prep.enrich_metadata(missing=missing)

        elif operation == "sync":
            prep.cleanup_obsolete_episodes()
            prep.download_weekly_schedule(buffer_days=download_buffer)
            prep.verify_scheduled_programs(buffer_days=verify_buffer)
            prep.resolve_overlapping_broadcasts(buffer_days=verify_buffer, buffer_time=overlap, delete_overlaps=delete_overlaps)

        elif operation == "refresh":
            prep.fetch_nrk_data(years_back, buffer_weeks=refresh_buffer)
            prep.enrich_metadata(missing=missing)

        else:
            print("Not a valid operation")


if __name__ == "__main__":
    main()