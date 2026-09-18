import shutil

from .tvdatabase import TVDatabase, Schedule
from .tvconstants import *
from .mediapathmanager import MediaPathManager
from datetime import datetime
from pathlib import Path
import subprocess

class TVFileHandler:
    """
    Class that deals with all sorts of file handling, such as deleting, recieve file metadata, etc. 
    """
    def __init__(self):
        self.paths = MediaPathManager()
        self.tv_db = TVDatabase()

    def _delete_file_if_exists(self, path) -> bool:
        path = Path(path)
        if path.exists():
            path.unlink()
            return True
        return False

    def delete_media(self, schedule_id, file_path):
        success = self._delete_file_if_exists(file_path)
        if success:
            self._clear_schedule_file_info(schedule_id, status=STATUS_DELETED)
        else:
            self._clear_schedule_file_info(schedule_id, status=STATUS_MISSING)

    def delete_series_directory(self, slug) -> bool:
        program_dir = self.paths.get_program_dir(TYPE_SERIES, slug)
        if program_dir.exists():
            shutil.rmtree(program_dir)
            return True
        return False

    def delete_episode_files(self, episode) -> None:
        slug = episode.series.slug
        series_id = episode.series.series_id

        filename = self.paths.create_episode_file_name(series_id, episode.episode_id)
        video_path = self.paths.get_filepath(TYPE_SERIES, slug, filename)
        self._delete_file_if_exists(video_path)

        ytdlp_json = self.paths.get_metadata_path(
            TYPE_SERIES, slug,
            self.paths.create_ytdlp_episode_json_name(series_id, episode.episode_id)
        )
        self._delete_file_if_exists(ytdlp_json)

        if episode.tmdb_id:
            tmdb_json = self.paths.get_metadata_path(
                TYPE_SERIES, slug,
                self.paths.create_tmbd_episode_json_name(
                    episode.tmdb_id, episode.season_number, episode.episode_number
                )
            )
            self._delete_file_if_exists(tmdb_json)

    def delete_movie_files(self, movie) -> None:
        slug = movie.slug

        filename = self.paths.create_movie_file_name(movie.movie_id)
        video_path = self.paths.get_filepath(TYPE_MOVIES, slug, filename)
        self._delete_file_if_exists(video_path)

        ytdlp_json = self.paths.get_metadata_path(
            TYPE_MOVIES, slug,
            self.paths.create_ytdlp_movie_json_name(movie.movie_id)
        )
        self._delete_file_if_exists(ytdlp_json)

        if movie.tmdb_id:
            tmdb_json = self.paths.get_metadata_path(
                TYPE_MOVIES, slug,
                self.paths.create_tmbd_movie_json_name(movie.tmdb_id)
            )
            self._delete_file_if_exists(tmdb_json)

    def update_file_info(self, schedule_id, file_path):
        file_info = self.get_file_info(file_path)
        self.tv_db.upsert(Schedule(id=schedule_id, **file_info))
        return file_info

    def verify_local_file(self, schedule_id, filepath):
        if Path(filepath).exists():
            self.tv_db.upsert(Schedule(id=schedule_id, status=STATUS_AVAILABLE))
            return STATUS_AVAILABLE
        else:
            self.tv_db.upsert(Schedule(id=schedule_id, status=STATUS_MISSING))
            return STATUS_MISSING

    def get_file_info(self, input_path):
        path = Path(input_path)
        
        if path.is_file():
            stats = path.stat()
            timestamp = stats.st_ctime
            download_date = datetime.fromtimestamp(timestamp)
            return {
                "filepath": str(path.relative_to(self.paths.media_path)),
                "download_date": download_date, 
                "file_size": stats.st_size, 
            }
        
        else:
            return {
                "filepath": None,
                "download_date": None, 
                "file_size": None, 
            }
