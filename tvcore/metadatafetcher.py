from .mediapathmanager import MediaPathManager
from .tvconstants import *
from .tvconfig import TVConfig
from .schemas import YTDLPInput, TMDBEpisodeInput, TMDBMovieInput, TMDBSeriesInput, MetadataInput
import yt_dlp
import json
import tmdbsimple as tmdb
from dotenv import load_dotenv
import os
from pathlib import Path
from pydantic_core import ValidationError


load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

class MetaDataFetcher:
    def __init__(self, tmdb_api_key=TMDB_API_KEY, translate=True):
        self.paths = MediaPathManager()
        tmdb.API_KEY = tmdb_api_key

        config = TVConfig()
        language = config.get_language()
        if language: 
            self.language = language
        else:
            self.language = "en"

        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'enable_file_urls': True
        }

        self.translate = translate

    # ============ YTDLP ============

    def get_ytdlp_data(self, url, json_path:Path=None, write_to_json=True):
        if json_path.exists():
            with open(json_path) as f:
                return json.load(f)
        
        data = self.fetch_ytdlp_data(url)
        
        if write_to_json:
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=4)
        
        return data

                
    def fetch_ytdlp_data(self, url):
        """ Fetch metadata from YTDLP without downloading."""
        
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                return ydl.extract_info(url, download=False)
            except Exception as e:
                print(f"Failed to fetch YTDLP metadata from {url}: {e}")
                return {}

    # ============ TMDB ============
    
    def get_tmdb_series_data(self, tmdb_id:int=None, season=None, episode=None, json_path:Path=None, write_to_json = True, validate=False) -> dict:
        '''
        Get metadata from TMDB (with caching)
        
        media_type: "movies" or "series"
        tmdb_id: ID of TMDB-media
        season: Season for series (only needed for mediatype "series")
        '''

        if json_path and json_path.exists():
            with open(json_path) as f:
                return json.load(f)

        if not tmdb_id:
            return
        
        if season:
            if episode:
                data = self.fetch_tmdb_episode_data(tmdb_id, season, episode)
            else:
                data = self.fetch_tmdb_season_data(tmdb_id, season)
        else:
            data = self.fetch_tmdb_series_data(tmdb_id)

        if json_path and write_to_json:
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=4)

        if validate:
            return self.extract_series_info_from_tmdb(data)    
        
        return data
    
    def get_tmdb_movie_data(self, tmdb_id:int=None, json_path:Path=None, write_to_json = True, validate=False):
        if json_path and json_path.exists():
            with open(json_path) as f:
                return json.load(f)
        
        if not tmdb_id:
            return
        
        data = self.fetch_tmdb_movie_data(tmdb_id)
        
        if json_path and write_to_json:
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=4)

        if validate:
            return self.extract_movie_info_from_tmdb(data)
        
        return data
    
    def fetch_tmdb_series_data(self, tmdb_id):
        return tmdb.TV(tmdb_id).info()
    
    def fetch_tmdb_season_data(self, tmdb_id, season):
        return tmdb.TV_Seasons(tmdb_id, season).info()
    
    def fetch_tmdb_episode_data(self, tmdb_id, season, episode):
        return tmdb.TV_Episodes(tmdb_id, season, episode).info()
    
    def fetch_tmdb_movie_data(self, tmdb_id):
        return tmdb.Movies(tmdb_id).info()
            
    # ============ EXTRACT METADATA ============
    def _validate_model(self, model:MetadataInput, data:dict):
        try:
            return model.model_validate(data)
        except ValidationError as e:
            raise

    def extract_episode_info_from_ytdlp(self, episode_data: dict):
        """Extract relevant episode info from yt-dlp data"""
        return self._validate_model(YTDLPInput, episode_data)
        
    def extract_episode_info_from_tmdb(self, episode_data:dict):
        """Extract relevant episode info from TMDB data"""
        return self._validate_model(TMDBEpisodeInput, episode_data)
        
    def extract_series_info_from_tmdb(self, series_data:dict):
        """Extract relevant movie info from TMDB data"""
        return self._validate_model(TMDBSeriesInput, series_data)
    
    def extract_movie_info_from_tmdb(self, movie_data:dict):
        """Extract relevant movie info from TMDB data"""
        return self._validate_model(TMDBMovieInput, movie_data)

    
    # ============ API ============

    def fetch_tmdb_metadata(self, media_type, tmdb_id):
        """
        API-call to TMDB data 
        """

        try:
            if media_type == TYPE_SERIES:
                return self.fetch_tmdb_series_data(tmdb_id)
            elif media_type == TYPE_MOVIES:
                return self.fetch_tmdb_movie_data(tmdb_id)
            
        except Exception as e:
            print(f"Error recieving tmdb metadata: {e}")
            return True
