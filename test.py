from TVdatabase import TVDatabase
from TVdownloader import TVDownloader
from datetime import datetime
import os

tvdb = TVDatabase()
tvdl = TVDownloader()

#tvdl.prepare_weekly_schedule()
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

print(BASE_DIR)