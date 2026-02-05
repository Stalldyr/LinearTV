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

#Database tables
TABLE_MOVIES = "movies"
TABLE_SERIES = "series"
TABLE_EPISODES = "episodes"
TABLE_SCHEDULE = "weekly_schedule"

# Special stream IDs (negative to avoid collision with database IDs)
STREAM_ID_OFF_AIR = -1
STREAM_ID_NO_PROGRAM = -2
STREAM_ID_UNAVAILABLE = -3