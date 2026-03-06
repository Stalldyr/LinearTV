from .tvconstants import *
from pathlib import Path

class MediaPathManager:
    def __init__(self, download_path="", series_subdir=TYPE_SERIES, movies_subdir=TYPE_MOVIES, **kwargs):
        self.base_dir = Path(__file__).parent.parent.resolve()

        if download_path:
            self.download_path = Path(download_path)
        else:
            self.download_path = self.base_dir / "downloads"
            
        self.series_path = self.download_path / series_subdir
        self.movies_path = self.download_path / movies_subdir

        self.paths = []
        for path in kwargs:
            self.paths.append(Path(download_path)/path)

        self._ensure_base_paths()

    def _ensure_base_paths(self):
        """Create base slug structure if it doesn't exist"""

        for path in [self.download_path, self.series_path, self.movies_path]:
            Path(path).mkdir(exist_ok=True)

    def get_program_dir(self, media_type, slug) -> Path:
        """Get the full path to a program's slug"""

        if media_type == TYPE_SERIES:
            media_dir = self.series_path
        elif media_type == TYPE_MOVIES:
            media_dir = self.movies_path
        else:
            raise ValueError(f"Invalid media type: {media_type}")
        
        program_dir = self.base_dir / media_dir / slug
        
        # Create if doesn't exist
        program_dir.mkdir(exist_ok = True)
        
        return program_dir
    
    def get_filepath(self, media_type, slug, filename) -> Path:
        """Get full path to a specific file"""
        program_dir = self.get_program_dir(media_type, slug)
        return Path(program_dir)/filename
    
    def get_relative_episode_path(self, slug, filename) -> Path:
        """Get full path to a specific file"""
        return Path(TYPE_SERIES)/slug/filename
    
    def get_relative_movie_path(self, slug, filename) -> Path:
        """Get full path to a specific file"""
        return Path(TYPE_MOVIES)/slug/filename
    
    def get_metadata_path(self, media_type, slug, metadata_file) -> Path:
        """Get path for metadata JSON files"""
        program_dir = self.get_program_dir(media_type, slug)
        return Path(program_dir)/metadata_file
    
    def get_full_path(self, relative_path) -> Path:
        """Convert a relative path to a full path"""
        return self.download_path / relative_path
    
    #Filename generation

    def create_episode_file_name(self, slug, season, episode) -> str:
        return f"{slug}_s{season:02d}e{episode:02d}.mp4"

    def create_movie_file_name(self, slug) -> str:
        return f"{slug}.mp4"

    def create_ytdlp_season_json_name(self, season) -> str:
        return f'ytdlp_data_season_{season}.json'
    
    def create_ytdlp_episode_json_name(self, season, episode) -> str:
        return f'ytdlp_data_episode_S{season}E{episode}.json'
    
    def create_tmbd_season_json_name(self, season, language) -> str:
        return f'tmdb_data_season_{season}_{language}.json'
    
    def create_tmbd_movie_json_name(self, film_name, language) -> str:
        return f'tmdb_data_{film_name}_{language}.json'
    

    
    #File

    def create_episode_file_name2(self, series_id, episode_id) -> str:
        return f"seriesid{series_id}_episodeid{episode_id}.mp4"

    def create_movie_file_name2(self, movie_id) -> str:
        return f"movieid{movie_id}.mp4"

    #YTDLP

    def create_ytdlp_season_json_name2(self, season) -> str:
        return f'ytdlp_data_season_{season}.json'
    
    def create_ytdlp_episode_json_name2(self, series_id, episode_id) -> str:
        return f'ytdlp_data__s{series_id}e{episode_id}.json'
    

    
    #TMDB
    def create_tmbd_episode_json_name(self, tmdbid, season, episode, language) -> str:
        return f'tmdb_tv_id{tmdbid}s{season}s{episode}_{language}.json'

    def create_tmbd_season_json_name2(self, tmdbid, season, language) -> str:
        return f'tmdb_tv_id{season}_{language}.json'
    
    def create_tmbd_movie_json_name2(self, tmdbid, language) -> str:
        return f'tmdb_film_{tmdbid}_{language}.json'
