from .tvconstants import *
from .tvdatabase import TVDatabase
import yt_dlp

class TVDownloader:
    def __init__(self):
        '''
            series_path: 
        '''
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
        
        success = self.downloader.download(
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
        self.default_quality = 480
        self.ydl_opts = {}
         
    def download(self, url, output_path, index=1, quality=None, **kwargs):
        '''
        Downloads from playlist
        
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
            Boolean: Wheather the file was successfully downloaded or not
        '''

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                ydl.extract_info(url)
                print(f"Downloaded succesfully from {url}")
                return True

            except Exception as e:
                print(f"Error downloading from {url}: {e}")
                return False
            