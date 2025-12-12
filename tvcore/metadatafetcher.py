from tvcore.tvhandler import MediaPathManager
from tvcore.tvconstants import *
import yt_dlp
import json
import tmdbsimple as tmdb

class MetaDataFetcher:
    def __init__(self, tmdb_api_key="c8ed91b54503ef6a7e9e9ca6c122a9c9"):
        self.paths = MediaPathManager()
        tmdb.API_KEY = tmdb_api_key

    #YTDLP

    def get_ytdlp_season_metadata(self, media_type, directory, season, video_url=None, download_json = True):
        '''
            Docstring for get_ytdlp_season_metadata
            
            :param self: Description
            :param media_type: Description
            :param directory: Description
            :param season: Description
            :param video_url: Description
            :param download_json: Description
        '''
        
        json_name = self.paths.create_ytdlp_season_json_name(season)
        json_path = self.paths.get_metadata_path(media_type, directory, json_name)

        if json_path.exists():
            with open(json_path, 'r') as f:
                return json.load(f)

        if not video_url:
            raise ValueError("video_url must be provided if metadata cache does not exist.")
        
        metadata = self._fetch_ytdlp_info(video_url)

        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=4)
        
        return metadata
    
    def _fetch_ytdlp_info(self, url):
        """
            Fetch info from YTDLP without downloading.
        """

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'enable_file_urls': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                return ydl.extract_info(url, download=False)
            except Exception as e:
                print(f"Failed to fetch YTDLP metadata from {url}: {e}")
                return {}

    #TMDB

    def get_tmdb_metadata(self, media_type:str, directory:str,  tmdb_id:int, season:int=None, language:str="no"):
        '''
            Get metadata from TMDB (with caching)
            
            media_type: "movies" of "series"
            tmdb_id: ID of TMDB-media
            season: Season for series (only needed for mediatype "series")
            language: Language for metadata
        '''

        if media_type == TYPE_SERIES:
            if season is None:
                print("Need to provide season for series")
                return None
        
            json_name = self.paths.create_tmbd_season_json_name(season)
            params = (tmdb_id, season)
            fetcher = tmdb.TV_Seasons
            
        elif media_type == TYPE_MOVIES:
            json_name = self.paths.create_tmbd_movie_json_name(directory)
            params = (tmdb_id,)
            fetcher = tmdb.Movies
        else:
            print("Invalid media type")
            return None
        
        json_path = self.paths.get_metadata_path(media_type, directory, json_name)

        if json_path.exists():
            with open(json_path) as f:
                return json.load(f)
            
        fetch_options  = {
            "language": language
        }       

        try:
            metadata = self._fetch_tmdb_info(fetcher, params, fetch_options)
        except Exception as e:
            print(f"Failed to download tmdb metadata: {e}")
            return None

        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=4)

        return metadata

    def _fetch_tmdb_info(self, fetcher, params, fetch_options):
        return fetcher(*params).info(**fetch_options)
    
    #EXTRACT INFO

    def get_season_episode_count(self, directory, season, source_url=None, tmdb_id=None):
        """Get total episode count for a season from either source"""
        if source_url:
            metadata = self.get_ytdlp_season_metadata(TYPE_SERIES, directory, season, source_url)
            return metadata.get('playlist_count', 0)
        
        elif tmdb_id:
            metadata = self.get_tmdb_metadata(TYPE_SERIES, directory, tmdb_id, season)
            episodes = metadata.get('episodes', [])
            return len(episodes)
        
        else:
            print("Need either source_url or tmdb_id to get episode_count")
            return 0
        
    def extract_episode_info_from_ytdlp(self, episode_data):
        """Extract relevant episode info from yt-dlp data"""
        return {
            "yt_dlp_id": episode_data.get("id"),
            "season_number": episode_data.get("season_number"),
            "episode_number": episode_data.get("episode_number") or episode_data.get("playlist_index"),
            "title": episode_data.get("title"),
            "description": episode_data.get("description"),
            "duration": episode_data.get("duration")
        }

        age_limit = episode_data.get("age_limit", None) #Might be unecessary info
        ext = episode_data.get("ext", None) #This too
        
    def extract_episode_info_from_tmdb(self, episode_data):
        """Extract relevant episode info from TMDB data"""
        return {
            "tmdb_id": episode_data.get("id"),
            "season_number": episode_data.get("season_number"),
            "episode_number": episode_data.get("episode_number"),
            "title": episode_data.get("name"),
            "description": episode_data.get("overview"),
            "duration": episode_data.get("runtime")
        }
        
    def extract_movie_info_from_tmdb(self, movie_data):
        """Extract relevant movie info from TMDB data"""
        return {
            "tmdb_id": movie_data.get("id"),
            "title": movie_data.get("name"),
            "description": movie_data.get("overview"),
            "duration": movie_data.get("runtime")
        }