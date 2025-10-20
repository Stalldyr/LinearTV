from TVdatabase import TVDatabase
from TVdownloader import TVDownloader
from datetime import datetime

tvdb = TVDatabase()
tvdl = TVDownloader()

tvdl.prepare_weekly_schedule()