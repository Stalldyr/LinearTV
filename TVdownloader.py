from TVdatabase import TVDatabase
import yt_dlp
import json
from datetime import datetime
import os
import tmdbsimple as tmdb
from helper import create_path, verify_path, create_episode_file_name
import logging
from TVconstants import *

class TVDownloader:
    def __init__(self, directory, media_type, download_path="downloads", series_path=SERIES, movies_path=MOVIES):
        self.ydl_opts = {}
        self.tv_db = TVDatabase()

        tmdb.API_KEY = "c8ed91b54503ef6a7e9e9ca6c122a9c9"

        self.media_type = media_type

        self.download_path = download_path
        self.series_path = create_path(download_path, series_path)
        self.movies_path = create_path(download_path, movies_path)
        self.path_setup()

        if media_type == SERIES:
            self.program_dir = create_path(download_path, series_path, directory)
        elif media_type == MOVIES:
            self.program_dir = create_path(download_path, movies_path, directory)
        else:
            print("Not a valid media type")
        self.create_subpath()


    def path_setup(self):
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        if not os.path.exists(self.series_path):
            os.makedirs(self.series_path)

        if not os.path.exists(self.movies_path):
            os.makedirs(self.movies_path)

    def create_subpath(self):
        if not os.path.exists(self.program_dir):
            os.makedirs(self.program_dir)


    #METADATA

    def get_ytdlp_season_metadata(self, season, video_url=None, download_json = True):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'enable_file_urls': True
        }

        json_name = f'ytdlp_data_season_{season}.json'
        json_path = create_path(self.program_dir, json_name)

        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                return json.load(f)

        if not video_url:
            raise ValueError("video_url must be provided if metadata file does not exist.")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(video_url, download=False)

                if download_json:
                    with open(json_path, 'w') as f:
                        json.dump(info, f, indent=4)

                return info
            
            except Exception as e:
                print(f"Failed to download metadata: {e}")

        return {}

    def get_ytdlp_epsiode_info(self, episode_data):
        yt_dlp_id = episode_data.get("id", None)
        title = episode_data.get("title", None)
        description = episode_data.get("description", None)
        duration = episode_data.get("duration", None)
        season_number = episode_data.get("season_number", None)
        episode_number = episode_data.get("episode_number", None)
        if not episode_number:
            episode_number = episode_data.get("playlist_index", None)

        age_limit = episode_data.get("age_limit", None) #Might be unecessary info
        ext = episode_data.get("ext", None) #This too

        return {
            "yt_dlp_id": yt_dlp_id,
            "season_number": season_number,
            "episode_number": episode_number,
            "title": title,
            "description": description,
            "duration": duration
        }
    
    def get_tmdb_season_metadata(self, tmdb_id, season):
        json_name = f'tmdb_data_season_{season}.json'
        json_path = create_path(self.program_dir, json_name)

        if os.path.exists(json_path):
            with open(json_path) as f:
                return json.load(f)
            
        else:
            try: 
                season_data = tmdb.TV_Seasons(tmdb_id, season).info(language="no")

                with open(json_path, 'w') as f:
                    json.dump(season_data, f, indent=4)

                return season_data
            
            except Exception as e:
                print(f"Failed to download tmdb metadata: {e}")

        return {}

    def get_tmdb_episode_info(self, episode_data):
        tmdb_id = episode_data.get("id", None)
        title = episode_data.get("name", None)
        description = episode_data.get("overview", None)
        duration = episode_data.get("runtime", None)
        season_number = episode_data.get("season_number", None)
        episode_number = episode_data.get("episode_number", None)

        return {
            "tmdb_id": tmdb_id,
            "season_number": season_number,
            "episode_number": episode_number,
            "title": title,
            "description": description,
            "duration": duration
        }


    def get_season_metadata(self, entry):
        if entry.get('total_episodes', False):
            return entry["total_episodes"]
                    
        if entry["source_url"]:      
            metadata = self.get_ytdlp_season_metadata(entry["season"], entry["source_url"])
            total_episodes = metadata.get('playlist_count', None)
        
            return total_episodes
        
        elif entry["tmdb_id"]:
            metadata = self.get_tmdb_season_metadata(entry["tmdb_id"], entry["season"])
            episodes = metadata.get('episodes', [])
            total_episodes = len(episodes)

            return total_episodes
                
        else:
            print(f"No season metada provided for {entry["name"]}")

            return
        
    def get_tmdb_movie_metadata(self, tmdb_id, json_name = 'tmdb_data.json'):
        json_path = create_path(self.program_dir, json_name)

        if os.path.exists(json_path):
            with open(json_path) as f:
                return json.load(f)
            
        else:
            try:
                season_data = tmdb.Movies(tmdb_id).info(language="no")

                with open(json_path, 'w') as f:
                    json.dump(season_data, f, indent=4)

                return season_data
            
            except Exception as e:
                print(f"Failed to download tmdb metadata: {e}")

        return {}
    
    #DOWNLOAD

    def download_episode(self, episode_id, download_url, season, episode, filename, total_episodes = 0, reverse_order = False):
        print(f"Started downloading episode {episode} of season {season}")
        self.tv_db.update_media_status(episode_id, self.media_type, STATUS_DOWNLOADING)
        
        # Calculate playlist index
        if reverse_order and total_episodes:
            playlist_idx = total_episodes - episode + 1
        else:
            playlist_idx = episode

        filepath = create_path(self.program_dir, filename)
        success = verify_path(filepath)

        if success:
            print(f"Local file found for {filename}, skipping download.")
        else:
            success = self.download(
                download_url,
                filename,
                index = playlist_idx
            )

        self._verify_and_update_status(success, episode_id, filename)

        return success
    
    def download_movie(self, movie_id, download_url, filename):
        #print(f"Started downloading episode {episode} of season {season}")
        self.tv_db.update_media_status(movie_id, self.media_type, STATUS_DOWNLOADING)
        
        filepath = create_path(self.program_dir, filename)
        success = verify_path(filepath)

        if success:
            print(f"Local file found for {filename}, skipping download.")
        else:
            success = self.download(
                download_url,
                filename
            )

        self._verify_and_update_status(success, movie_id, filename)

        return success
    
    def _verify_and_update_status(self, success, id, filename):
        if success:
            filepath = create_path(self.program_dir, filename)
            if verify_path(filepath):
                file_info = self.get_file_info(filename)

                if self.media_type == SERIES:
                    self.tv_db.edit_row_by_id(TABLE_EPISODES, id, **file_info)
                elif self.media_type == MOVIES:
                    self.tv_db.edit_row_by_id(TABLE_MOVIES, id, **file_info)

                self.tv_db.update_media_status(id, self.media_type, STATUS_AVAILABLE)
            else:
                self.tv_db.update_media_status(id, self.media_type, STATUS_MISSING)
        else:
            self.tv_db.update_media_status(id, self.media_type, STATUS_FAILED)
    
    def download(self, url, filename, index=1, quality = 480, **kwargs):
        if kwargs:
            self.ydl_opts.update(kwargs)

        else:
            self.ydl_opts = {
                'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
                'outtmpl': f'{self.program_dir}/{filename}', 
                'download_archive': f'{self.program_dir}/.archive.txt',
                'playlist_items': str(index),
                'merge_output_format': 'mp4'
            }

        return self._download(url)
    

    def _download(self, url):
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                ydl.extract_info(url)
                print(f"Downloaded succesfully from {url}")
                return True

            except Exception as e:
                print(f"Error downloading from {url}: {e}")
                return False
            
    #DELETE
    def delete_media(self, media_id, filename):
        file_path = create_path(self.program_dir, filename)
        try:
            if verify_path(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            else:
                print(f"File does not exist: {file_path}")
            
            self.tv_db.update_media_status(media_id, self.media_type, STATUS_DELETED)

        except Exception as e:
            print(f"Error while deleting {file_path}: {e}")
            
    #LOCAL FILES

    def verify_local_file(self, file_id, filename):
        filepath = create_path(self.program_dir, filename)

        file_info = self.get_file_info(filename)
        if self.media_type == SERIES:
            self.tv_db.edit_row_by_id(TABLE_EPISODES, file_id, **file_info)
        elif self.media_type == MOVIES:
            self.tv_db.edit_row_by_id(TABLE_MOVIES, file_id, **file_info)

        success = verify_path(filepath)
        if success:
            print(f"File found: {filename}")
            self.tv_db.update_media_status(file_id, self.media_type, STATUS_AVAILABLE)
        else:
            print(f"File is missing: {filename}")
            self.tv_db.update_media_status(file_id, self.media_type, STATUS_MISSING)
    
    def update_local_files(self, entry):
        "FUNCTION UNUSED AND OUT OF DATE"

        if not os.path.exists(self.program_dir):
            print("No directory exists")
            return None
            
        local_files = sorted([f for f in os.listdir(self.program_dir) if os.path.splitext(f)[1] == ".mp4"])

        start_episode = entry["episode"]
        for idx, file in enumerate(local_files):
            episode_num = start_episode + idx

            existing = self.tv_db.get_episode_by_details(entry["series_id"], entry["season"], episode_num)

            if existing and existing['status'] == STATUS_AVAILABLE:
                continue    

            file_info = self.get_file_info(entry["series_id"], entry['directory'], file, episode_num)
            self.tv_db.add_new_episode("episodes", file_info)

    def get_file_info(self, filename):
        filepath = os.path.join(self.program_dir, filename)

        if os.path.exists(filepath):
            timestamp = os.path.getctime(filepath)
            download_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
            return {
                "filename": filename,
                "download_date": download_time, 
                "file_size": os.path.getsize(filepath), 
            }
        
        else:
            return {
                "filename": None,
                "download_date": None, 
                "file_size": None, 
            }


