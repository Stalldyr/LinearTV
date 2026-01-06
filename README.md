**Introduction**

Nostalgic linear TV streaming server that recreates the TV experience before on-demand streaming. Content runs at fixed times throughout the week based on a custom weekly schedule.

**Features**

- Fixed weekly broadcast schedule for series and movies
- Automatic content downloading via yt-dlp
- Metadata integration from TMDB
- Admin panel for schedule management

**Guide**

1. Initialization
```
# Clone repository
git clone https://github.com/Stalldyr/LinearTV.git
cd LinearTV

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

or 

pip install -e ./tvstreamer
```

2. Schedule administration and testing

Administrate and test the viewing schedule by running:
```
python stream_app.py
```

Or in order to access the streamer from another Flask-application: 
```
from tvstreamer.stream_app import stream_app

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

**Configuration**

Configuration such as schedule start- and end-times and custom paths may be edited using config.json

