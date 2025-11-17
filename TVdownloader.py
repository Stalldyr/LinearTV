from TVdatabase import TVDatabase
import yt_dlp
import json
from datetime import datetime
import os
import tmdbsimple as tmdb
import helper

class TVDownloader:
    def __init__(self, path="downloads"):
        self.ydl_opts = {}
        self.tv_db = TVDatabase()
        self.download_path = path

        tmdb.API_KEY = "c8ed91b54503ef6a7e9e9ca6c122a9c9"

    #METADATA

    def get_ytdlp_season_metadata(self, season, directory, video_url=None, download_json = True):
        ydl_opts = {
            'quiet': True,  # Ikke print progresjon
            'no_warnings': True,
            'enable_file_urls': True
        }

        json_path = f'{self.download_path}/{directory}/ytdlp_data_season_{season}.json'

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
    
    def get_tmdb_season_metadata(self, tmdb_id, directory, season):
        json_path = f'{self.download_path}/{directory}/tmdb_data_season_{season}.json'

        if os.path.exists(json_path):
            with open(json_path) as f:
                return json.load(f)

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
            season_url = entry["source_url"].format(season=entry["season"])
            metadata = self.get_ytdlp_season_metadata(entry["season"], entry['directory'], season_url)
            total_episodes = metadata.get('playlist_count', None)
            #self.tv_db.edit_cell("series", entry['series_id'], "total_episodes", total_episodes)
        
            return total_episodes
        
        elif entry["tmdb_id"]:
            metadata = self.get_tmdb_season_metadata(entry["season"], entry['directory'], entry["tmdb_id"])
            episodes = metadata.get('episodes', None)
            total_episodes = len(episodes)
            #self.tv_db.edit_cell("series", entry['series_id'], "total_episodes", total_episodes)

            return len(episodes)
                
        else:
            print(f"No season metada provided for {entry["name"]}")

            return
    
    #DOWNLOAD

    def download_episode(self, entry, episode, episode_num, total_episodes):
        self.tv_db.update_episode_status(episode["id"], "downloading")
        
        # Calculate playlist index
        if entry["reverse"]:
            playlist_idx = total_episodes - episode_num + 1
        else:
            playlist_idx = episode_num

        filename = helper._create_file_name(entry['directory'], entry['season'], episode_num)

        filepath = helper.create_path(self.download_path, entry['directory'], filename)
        success = helper.verify_path(filepath)

        if success:
            print(f"Lokal fil funnet for {filename}, hopper over nedlasting.")
        else:
            season_url = entry["source_url"].format(season=entry["season"])
            success = self.download(
                season_url, 
                entry["directory"],
                filename,
                playlist_idx
            )

        if success:
            if helper.verify_path(filepath):
                file_info = {
                    "filename": filename,
                    "download_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                    "file_size": os.path.getsize(filepath), 
                }   
        
                self.tv_db.edit_row_by_id("episodes", episode["id"], **file_info)
                self.tv_db.update_episode_status(episode["id"], "available")

            else:
                self.tv_db.update_episode_status(episode["id"], "missing")

        else:
            self.tv_db.update_episode_status(episode["id"], "failed")

        return success
    
    def download(self, url, directory, filename, index, quality = 480, **kwargs):
        if kwargs:
            self.ydl_opts.update(kwargs)

        else:
            self.ydl_opts = {
                'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
                'outtmpl': f'{self.download_path}/{directory}/{filename}', 
                'download_archive': f'{self.download_path}/{directory}/.archive.txt',
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
            
    #LOCAL FILES
    
    def update_local_files(self, entry):
        download_folder = f"{self.download_path}/{entry['directory']}"
        if not os.path.exists(download_folder):
            print("No directory exists")
            return None
            
        local_files = sorted([f for f in os.listdir(download_folder) if os.path.splitext(f)[1] == ".mp4"])

        start_episode = entry["episode"]
        for idx, file in enumerate(local_files):
            episode_num = start_episode + idx

            existing = self.tv_db.get_episode_by_details(entry["series_id"], entry["season"], episode_num)

            if existing and existing['status'] == 'available':
                continue    

            file_info = self.get_file_info(entry["series_id"], entry['directory'], file, episode_num)
            self.tv_db.add_new_episode("episodes", file_info)

    def get_file_info(self, directory, filename):
        seriespath = os.path.join(self.download_path, directory)
        filepath = os.path.join(seriespath,filename)

        if os.path.exists(filepath):
            return {
                "filename": filename,
                "download_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                "file_size": os.path.getsize(filepath), 
            }


