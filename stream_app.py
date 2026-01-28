from flask import Flask, jsonify, render_template, send_from_directory, request, Blueprint
from pathlib import Path
import json
import os 
from datetime import datetime

try:
    from .tvcore.tvstreamer import TVStreamManager
    from .tvcore.tvdatabase import TVDatabase
    from .tvcore.programmanager import ProgramManager
    from .tvcore.mediapathmanager import MediaPathManager
    from .tvcore.helper import calculate_time_slots
except ImportError:
    from tvcore.tvstreamer import TVStreamManager
    from tvcore.tvdatabase import TVDatabase
    from tvcore.programmanager import ProgramManager
    from tvcore.mediapathmanager import MediaPathManager
    from tvcore.helper import calculate_time_slots

stream_app = Blueprint(
    'streaming', 
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/tvstreamer/static'      
)


tv_stream = TVStreamManager()
tv_stream.start_monitoring()

tv_db = TVDatabase()
program_manager = ProgramManager()
path_manager = MediaPathManager()

# ============ CONFIG FUNCTION ============

class TVConfig:
    def __init__(self, config_path=""):
        if not config_path:
            with open(Path(__file__).parent.absolute()/"config.json", 'r', encoding='utf-8') as f:
                self.config =  json.load(f)

        else:
            with open(Path(config_path), 'r', encoding='utf-8') as f:
                self.config =  json.load(f)

    def get_time_slots(self):
        timeslots = calculate_time_slots(
            self.config["broadcast_start"],
            self.config["broadcast_end"],
            self.config["broadcast_steps"]
        )

        return timeslots

    def get_genres(self):
        return self.config["genres"]


# ============ STREAMING PAGES ============
@stream_app.route('/tvstream')
def tvstream():
    return render_template('tvstream.html', offset=tv_stream.offset)
# ============= ADMIN PAGES =============

@stream_app.route('/admin/schedule')
def admin():
    schedule_data, series_data, movie_data = program_manager.initialize_admin_page()
    
    tv_config = TVConfig()
    timeslots = tv_config.get_time_slots()
    genres = tv_config.get_genres()

    return render_template('admin_schedule.html', schedule_data=schedule_data, series_data=series_data, movie_data=movie_data, genres=genres, timeslots=timeslots)

@stream_app.route('/admin/save_schedule', methods=['POST'])
def save_schedule():
    data = request.get_json()

    print(f"Recived data for weekly schedule: {data}")

    return return_status(*program_manager.save_schedule(data))
    
@stream_app.route('/admin/add_program', methods=['POST'])
def add_program():
    data = request.get_json()

    print(f"Recieved data for new program: {data}")

    return return_status(*program_manager.add_or_update_program(data))

@stream_app.route('/admin/delete_program', methods=['POST'])
def delete_program():
    data = request.get_json()

    return return_status(*program_manager.delete_program(data["program_id"], data["program_type"]))

@stream_app.route('/admin/fetch_metadata', methods=['POST'])
def fetch_metadata():
    #TODO Return fetched metadata
    data = request.get_json()

    metadata = program_manager.fetch_metadata(data["program_type"], data["tmdb_id"])

    return return_status(True, "succes")

@stream_app.route('/admin/preparer')
def prepare():
    return render_template("admin_preparer.html")

# ============ API ROUTES ============

@stream_app.route('/video/<content_type>/<directory>/<filename>')
def serve_video(content_type, directory, filename):
    return send_from_directory(path_manager.get_program_dir(content_type, directory), filename) #TODO Might reassign to programmanager or mediapathmanager

@stream_app.route('/api/config')
def get_config():
    return send_from_directory(".", 'config.json')

@stream_app.route('/api/current')
def current_program():
    return jsonify(tv_stream.current_stream)
    
@stream_app.route('/api/schedule')
def get_schedule():
    schedule = tv_db.get_weekly_schedule()
    print(f"Schedule requested: {schedule}")
    return jsonify(schedule)

@stream_app.route('/api/status')
def status():
    return jsonify(tv_stream.get_current_status())

@stream_app.route('/api/pending_episodes')
def get_pending_episodes():
    return jsonify(tv_db.get_pending_episodes())

@stream_app.route('/api/scheduled_episodes')
def get_scheduled_episodes():
    return jsonify(tv_db.get_scheduled_episodes())

@stream_app.route('/api/scheduled_movies')
def get_scheduled_movies():
    return jsonify(tv_db.get_scheduled_movies())

@stream_app.route('/api/kept_episodes')
def get_kept_episodes():
    return jsonify(tv_db.get_kept_episodes())

@stream_app.route('/api/obsolete_episodes')
def get_obsolete_episodes():
    return jsonify(tv_db.get_obsolete_episodes())

def return_status(success, message, error_code = None, debug=False):
    """Helper function for status"""
    if debug:
        print(message)

    if success:
        return jsonify({"status": "success", "message": message})
    else:
        return jsonify({"status": "error", "message": message}), error_code


if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(stream_app)

    test_time = None 
    if os.getenv('TEST_TIME'):
        test_time = datetime.strptime(os.getenv('TEST_TIME'), "%Y-%m-%d %H:%M")

    tv_stream = TVStreamManager()
    tv_stream.start_monitoring()

    @app.route('/')
    def setup_index():
        return render_template("test_panel.html")

    app.run(host='0.0.0.0', port=5000, debug=True)
