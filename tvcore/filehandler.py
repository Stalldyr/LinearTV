from .tvdatabase import TVDatabase, Schedule
from .tvconstants import *
from .mediapathmanager import MediaPathManager
from datetime import datetime
from pathlib import Path
import subprocess

class TVFileHandler:
    """
    Class that deals with all sorts of file handling, such as deleting, recieve file metadata, etc. 
    """
    def __init__(self):
        self.paths = MediaPathManager()
        self.tv_db = TVDatabase()

    def delete_media(self, schedule_id, file_path):
        path = Path(file_path)
        if path.exists():
            path.unlink()
            self.tv_db.upsert(
                Schedule(
                    id=schedule_id,
                    status=STATUS_DELETED,
                    file_size=None,
                    download_date=None,
                    filepath=None
                )
            )

        else:
            self.tv_db.upsert(
                Schedule(
                    id=schedule_id,
                    status=STATUS_MISSING,
                    file_size=None,
                    download_date=None,
                    filepath=None
                )
            )

    def update_file_info(self, schedule_id, file_path):
        file_info = self.get_file_info(file_path)
        self.tv_db.upsert(Schedule(id=schedule_id, **file_info))
        return file_info

    def verify_local_file(self, schedule_id, filepath):
        if Path(filepath).exists():
            self.tv_db.upsert(Schedule(id=schedule_id, status=STATUS_AVAILABLE))
            return STATUS_AVAILABLE
        else:
            self.tv_db.upsert(Schedule(id=schedule_id, status=STATUS_MISSING))
            return STATUS_MISSING

    def _check_file_integrity(self, path):
        #TODO: Unfinished

        print(f"Checking file integrity.")
        test = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", path, "-f", "null", "-"],
            stderr=subprocess.PIPE,
            text=True
        )
        print(test.stdout)

    def get_file_info(self, input_path):
        path = Path(input_path) 
        
        if path.is_file():
            stats = path.stat()
            timestamp = stats.st_ctime
            download_date = datetime.fromtimestamp(timestamp)
            return {
                "filepath": str(path.relative_to(self.paths.download_path)),
                "download_date": download_date, 
                "file_size": stats.st_size, 
            }
        
        else:
            return {
                "filepath": None,
                "download_date": None, 
                "file_size": None, 
            }
