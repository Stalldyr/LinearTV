from .tvconstants import *
from pathlib import Path

class MediaPathManager:
    def __init__(self, download_path="downloads", series_subdir=TYPE_SERIES, movies_subdir=TYPE_MOVIES, **kwargs):
        self.base_dir = Path(__file__).parent.parent.resolve()
        
        self.download_path = self.base_dir / download_path
        self.series_path = self.download_path / series_subdir
        self.movies_path = self.download_path / movies_subdir

        self.paths = []
        for path in kwargs:
            self.paths.append(Path(download_path)/path)

        self._ensure_base_paths()

    def _ensure_base_paths(self):
        """Create base directory structure if it doesn't exist"""

        for path in [self.download_path, self.series_path, self.movies_path]:
            Path(path).mkdir(exist_ok=True)

    def get_program_dir(self, media_type, directory) -> Path:
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
    
    def get_filepath(self, media_type, directory, filename) -> Path:
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
