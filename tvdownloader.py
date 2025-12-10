from tvdatabase import TVDatabase
from tvhandler import TVFileHandler, MediaPathManager
import yt_dlp
import json
import tmdbsimple as tmdb
from helper import create_path, verify_path, create_episode_file_name
import logging
from tvconstants import *
import ffmpeg 
from pathlib import Path


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
        
        json_name = f'ytdlp_data_season_{season}.json'
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

    def get_tmdb_metadata(self, media_type:str, tmdb_id:int, directory:str, season:int=None, language:str="no"):
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
        
            json_name = f'tmdb_data_season_{season}.json'
            params = (tmdb_id, season)
            fetcher = tmdb.TV_Seasons
            
        elif media_type == TYPE_MOVIES:
            json_name = 'tmdb_data.json'
            params = (tmdb_id,)
            fetcher = tmdb.Movies
        else:
            print("Invalid media type")
            return None
        
        json_path = self.paths.get_metadata_path(media_type, directory, json_name)

        if json_path.exists():
            with open(json_path) as f:
                return json.load(f)
            
        conditions = {
            "language": language
        }       

        try:
            metadata = self._fetch_tmdb_info(fetcher, params, conditions)
        except Exception as e:
            print(f"Failed to download tmdb metadata: {e}")
            return None

        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=4)

        return metadata

    def _fetch_tmdb_info(self, fetcher, params, conditions):
        return fetcher(*params).info(**conditions)
    
    #EXTRACT INFO

    def get_season_episode_count(self, directory, season, source_url=None, tmdb_id=None):
        """Get total episode count for a season from either source"""
        if source_url:
            metadata = self.get_ytdlp_season_metadata(TYPE_SERIES, directory, season, source_url)
            return metadata.get('playlist_count', 0)
        
        elif tmdb_id:
            metadata = self.get_tmdb_series_season_metadata(TYPE_SERIES, directory, tmdb_id, season)
            episodes = metadata.get('episodes', [])
            return len(episodes)
        
        else:
            print("Need either source_url or tmdb_id")
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

class TVDownloader:
    def __init__(self):
        '''
            series_path: 
        '''
        self.paths = TVFileHandler()
        self.metadata = MetaDataFetcher()
        self.downloader = Downloader()
        self.database = TVDatabase()
        

    def download_from_playlist(self, media_id, media_type, output_path, download_url, episode, total_episodes=0, reverse_order=False):
        """
        Download a TV episode
        
        Args:
            episode_id: Database ID of the episode
            media_type: TYPE_SERIES or TYPE_MOVIES
            directory: Program directory name
            download_url: Source URL
            season: Season number
            episode: Episode number
            filename: Output filename
            total_episodes: Total episodes in season (for reverse order)
            reverse_order: Whether playlist is in reverse order
        
        Returns:
            str: Status (STATUS_AVAILABLE, STATUS_FAILED, etc.)
        """
        #print(f"Started downloading episode {episode} of season {season}") Move to TVpreparer?
        self.database.update_media_status(media_id, media_type, STATUS_DOWNLOADING)
        
        # Calculate playlist index
        playlist_idx = self._calculate_playlist_index(
            episode, total_episodes, reverse_order
        )

        success = self.downloader.download(
            download_url,
            output_path,
            index = playlist_idx
        )

        status = self._update_download_status(media_id, media_type, success)

        return status
    
    def download_movie(self, media_id, media_type, download_url, output_path):
        self.database.update_media_status(media_id, media_type, STATUS_DOWNLOADING)
        
        success = self.download(
            download_url,
            output_path
        )

        status = self._update_download_status(media_id, media_type, success)
        
        return status
    
    def _update_download_status(self, media_id, media_type, success):
        if success:
            self.database.update_media_status(media_id, media_type, STATUS_AVAILABLE)
            return STATUS_AVAILABLE
        else:
            self.database.update_media_status(media_id, media_type, STATUS_FAILED)
            return STATUS_FAILED

    def _calculate_playlist_index(self, episode, total_episodes, reverse_order):
        """Calculate the correct playlist index based on settings"""
        if reverse_order and total_episodes:
            return total_episodes - episode + 1
        return episode
    


    
class Downloader:
    def __init__(self):
        self.paths = MediaPathManager()
        self.default_quality = 480
        self.ydl_opts = {}
         
    def download(self, url, output_path, index=1, quality=None, **kwargs):
        '''
            Downloads from playlist
            
            :param self: Description
            :param url: Description
            :param output_path: Description
            :param index: Description
            :param kwargs: Description
        '''

        quality = quality or self.default_quality

        if kwargs:
            self.ydl_opts.update(kwargs)

        else:
            self.ydl_opts = {
                'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
                'outtmpl': str(output_path), 
                #'download_archive': os.path.join(directory, '.archive.txt'),
                'playlist_items': str(index),
                'merge_output_format': 'mp4'
            }

        return self._execute_download(url)
    

    def _execute_download(self, url):
        '''
        Returns:
            Boolean
        '''

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                ydl.extract_info(url)
                print(f"Downloaded succesfully from {url}")
                return True

            except Exception as e:
                print(f"Error downloading from {url}: {e}")
                return False
            