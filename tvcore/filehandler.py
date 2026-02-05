from .tvdatabase import TVDatabase
from .tvconstants import *
from .mediapathmanager import MediaPathManager
from datetime import datetime
from pathlib import Path
import subprocess


class TVFileHandler:
    """
    Class that deals with all sorts of file handling, such as deleting, recive file metadata, etc. 
    """
    def __init__(self):
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
        self.tv_db.update_program_info(media_type, media_id, **file_info)

        return file_info

    def verify_local_file(self, media_id, filepath, media_type):
        if Path(filepath).exists():
            self.tv_db.update_media_status(media_id, media_type, STATUS_AVAILABLE)
            return STATUS_AVAILABLE
        else:
            self.tv_db.update_media_status(media_id, media_type, STATUS_MISSING)
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
