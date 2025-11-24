import os

#Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#Media status
STATUS_PENDING = 'pending'
STATUS_AVAILABLE = 'available'
STATUS_DELETED = 'deleted'
STATUS_FAILED = 'failed'
STATUS_DOWNLOADING = 'downloading'
STATUS_MISSING = 'missing'

#Media types
TYPE_SERIES = 'series'
TYPE_MOVIES = 'movies'

#Media sources
SOURCE_LOCAL = "Local"
SOURCE_NRK = "NRK"
SOURCE_YOUTUBE = "Youtube"

#Database tables
TABLE_MOVIES = "movies"
TABLE_SERIES = "series"
TABLE_EPISODES = "episodes"
TABLE_SCHEDULE = "weekly_schedule"
