**Features**

- Fixed weekly broadcast schedule for series and movies
- Automatic content downloading via yt-dlp
- Metadata integration from TMDB
- Admin panel for schedule management

**Guide**

1. Initialization
```
pip install https://github.com/Stalldyr/LinearTV.git
```

2. Schedule administration and testing

Administrate and test the viewing schedule by running:
```
from lineartvstream.stream_app import stream_app
python stream_app.py
```

Or in order to access the streamer from another Flask-application: 
```
from lineartvstream.stream_app import stream_app

app = Flask(__name__)
app.register_blueprint(stream_app)
```
Then in terminal:
```
# Start server
python app.py
# Or in production:
gunicorn -c gunicorn_config.py app:app
```


If you want the streaming without the routes you could import the html:
```
from lineartvstream.ui.stream_html import stream_html
html = stream_html().dump()
```


3. Schedule maintain

Currently there is no UI to maintain the schedule, this has to be done through tvpreparer.py:

```
# Complete weekly setup
python tvpreparer.py all

# Individual operations
python tvpreparer.py increment    # Increment episode numbers
python tvpreparer.py pending      # Create pending episodes
python tvpreparer.py download     # Download weekly episodes
python tvpreparer.py verify       # Verify files
python tvpreparer.py link         # Link episodes to schedule
python tvpreparer.py delete       # Clean up old episodes
```
