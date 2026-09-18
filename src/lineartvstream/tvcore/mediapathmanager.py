from .tvconstants import *
from .appdirs import get_config_dir

from pathlib import Path
import shutil
from importlib.resources import files as resource_files


class MediaPathManager:
    def __init__(self, download_path=None, media_path=None, ad_path=None, series_subdir=TYPE_SERIES, movies_subdir=TYPE_MOVIES, **kwargs):
        self.base_dir = Path(get_config_dir())/"tvfiles"

        if download_path:
            self.download_path = Path(download_path)
        else:
            self.download_path = self.base_dir / "downloads"

        if media_path:
            self.media_path = Path(media_path)
        else:
            self.media_path = self.base_dir / "media"

        if ad_path:
            self.ad_path = Path(ad_path)
        else:
            self.ad_path = self.media_path / "ads"
            
        self.series_path = self.media_path / series_subdir
        self.movies_path = self.media_path / movies_subdir

        self.paths = []
        for path in kwargs:
            self.paths.append(Path(download_path)/path)

        self._ensure_base_paths()

    def _ensure_default_ad(self):
        """Copy the bundled placeholder ad into ad_path if it's empty."""
        if any(self.ad_path.iterdir()):
            return  
        
        try:
            source = resource_files("lineartvstream.assets").joinpath("PM5544.mp4")
            with source.open("rb") as src:
                with open(self.ad_path / "PM5544.mp4", "wb") as dst:
                    shutil.copyfileobj(src, dst)
        except (FileNotFoundError, ModuleNotFoundError) as e:
            print("Could not install default ad file: %s", e)

    def _ensure_base_paths(self):
        """Create base slug structure if it doesn't exist"""

        for path in [self.base_dir, self.download_path, self.media_path, self.series_path, self.movies_path, self.ad_path]:
            Path(path).mkdir(exist_ok=True)

        self._ensure_default_ad()

    def get_program_dir(self, media_type:Path, slug:str) -> Path:
        """Get the full path to a program's slug"""

        if media_type == TYPE_SERIES:
            media_dir = self.series_path
        elif media_type == TYPE_MOVIES:
            media_dir = self.movies_path
        else:
            raise ValueError(f"Invalid media type: {media_type}")
        
        program_dir = media_dir / slug
        
        program_dir.mkdir(exist_ok = True)
        
        return program_dir
    
    def get_filepath(self, media_type, slug, filename) -> Path:
        """Get full path to a specific file"""
        program_dir = self.get_program_dir(media_type, slug)
        return Path(program_dir)/filename

    def get_download_path(self, filename) -> Path:
        """Get download path for ytdlp files"""
        return self.download_path/filename
    
    def get_metadata_path(self, media_type, slug, metadata_file) -> Path:
        """Get path for metadata JSON files"""
        program_dir = self.get_program_dir(media_type, slug)
        return Path(program_dir)/metadata_file
    
    def get_full_media_path(self, relative_path) -> Path:
        """Convert a relative path to a full path"""
        return self.media_path / relative_path
    

    #========= FILE NAME GENEREATION =========

    #MEDIA

    def create_episode_file_name(self, series_id, episode_id) -> str:
        return f"seriesid{series_id}_episodeid{episode_id}.mp4"

    def create_movie_file_name(self, movie_id) -> str:
        return f"movieid{movie_id}.mp4"

    #YTDLP

    def create_ytdlp_season_json_name(self, series_id, season) -> str:
        return f'ytdlp_data_s{series_id}_s{season}.json'
    
    def create_ytdlp_episode_json_name(self, series_id, episode_id) -> str:
        return f'ytdlp_data_s{series_id}e{episode_id}.json'
    
    def create_ytdlp_movie_json_name(self, movie_id) -> str:
        return f'ytdlp_data_m{movie_id}.json'
        
    #TMDB

    def create_tmbd_season_json_name(self, tmdbid:int , season:int, language:str="en") -> str:
        return f'tmdb_tv_id{tmdbid}s{season}_{language}.json'
    
    def create_tmbd_episode_json_name(self, tmdbid:int, season:int, episode:int, language:str="en") -> str:
        return f'tmdb_tv_id{tmdbid}s{season}e{episode}_{language}.json'
    
    def create_tmbd_movie_json_name(self, tmdbid:int, language:str="en") -> str:
        return f'tmdb_film_{tmdbid}_{language}.json'