from tvconstants import *
from datetime import datetime
from pathlib import Path
import subprocess

class MediaPathManager:
    def __init__(self, download_path="downloads", series_subdir=TYPE_SERIES, movies_subdir=TYPE_MOVIES, **kwargs):
        self.base_dir = Path()
        
        self.download_path = Path(download_path)
        self.series_path = self.download_path/series_subdir
        self.movies_path = self.download_path/movies_subdir

        self.paths = []
        for path in kwargs:
            self.paths.append(Path(download_path)/path)

        self._ensure_base_paths()

    def _ensure_base_paths(self):
        """Create base directory structure if it doesn't exist"""

        for path in [self.download_path, self.series_path, self.movies_path]:
            Path(path).mkdir(exist_ok=True)

    
    def get_program_dir(self, media_type, directory):
        """Get the full path to a program's directory"""

        if media_type == TYPE_SERIES:
            base = self.series_path
        elif media_type == TYPE_MOVIES:
            base = self.movies_path
        else:
            raise ValueError(f"Invalid media type: {media_type}")
        
        program_dir = Path(base)/directory
        
        # Create if doesn't exist
        program_dir.mkdir(exist_ok = True)
        
        return program_dir
    
    def get_filepath(self, media_type, directory, filename):
        """Get full path to a specific file"""
        program_dir = self.get_program_dir(media_type, directory)
        return Path(program_dir)/filename
    
    def get_metadata_path(self, media_type, directory, metadata_file):
        """Get path for metadata JSON files"""
        program_dir = self.get_program_dir(media_type, directory)
        return Path(program_dir)/metadata_file
    
    #Filename generation

    def create_episode_file_name(self, directory, season, episode):
        return f"{directory}_s{season:02d}e{episode:02d}.mp4"

    def create_movie_file_name(self, directory):
        return f"{directory}.mp4"

    def create_ytdlp_season_json_name(self, season):
        return f'ytdlp_data_season_{season}.json'
    
    def create_tmbd_season_json_name(self, season):
        return f'tmdb_data_season_{season}.json'
    
    def create_tmbd_movie_json_name(self, film_name):
        return f'{film_name}_tmdb_data.json'

class TVFileHandler:
    def __init__(self):
        from tvdatabase import TVDatabase

        self.paths = MediaPathManager()
        self.tv_db = TVDatabase()

    def delete_media(self, media_id, file_path, media_type):
        path = Path(file_path)
        try:
            if path.exists():
                path.unlink()
                print(f"Deleted file: {file_path}")
                self.tv_db.update_media_status(media_id, media_type, STATUS_DELETED)
            else:
                print(f"File does not exist: {file_path}")
                self.tv_db.update_media_status(media_id, media_type, STATUS_MISSING)

        except Exception as e:
            print(f"Error while deleting {file_path}: {e}")


    def update_file_info(self, media_id, media_type, file_path):
        
        file_info = self.get_file_info(file_path)

        self.tv_db.update_episode_info(self, media_type, media_id, file_info)

        return file_info

    def verify_local_file(self, file_id, filepath, media_type):
        if Path(filepath).exists():
            self.tv_db.update_media_status(file_id, media_type, STATUS_AVAILABLE)
            return STATUS_AVAILABLE
        else:
            self.tv_db.update_media_status(file_id, media_type, STATUS_MISSING)
            return STATUS_MISSING

    def _check_file_integrity(self, path):
        print(f"Checking file integrity.")
        test = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", path, "-f", "null", "-"],
            stderr=subprocess.PIPE,
            text=True
        )
        print(test.stdout)


    def _verify_file_and_update_status(self, id, media_type, filepath, success):
        if success:
            if Path(filepath).exists():
                self.tv_db.update_media_status(id, media_type, STATUS_AVAILABLE)
                return STATUS_AVAILABLE
            else:
                self.tv_db.update_media_status(id, media_type, STATUS_MISSING)
                return STATUS_MISSING
        else:
            self.tv_db.update_media_status(id, media_type, STATUS_FAILED)
            return STATUS_FAILED

    def get_file_info(self, input_path):
        path = Path(input_path) 
        
        if path.is_file():
            stats = path.stat()
            timestamp = stats.st_ctime
            download_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
            return {
                "filename": path.name,
                "download_date": download_date, 
                "file_size": stats.st_size, 
            }
        
        else:
            return {
                "filename": None,
                "download_date": None, 
                "file_size": None, 
            }
