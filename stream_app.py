from flask import Flask, jsonify, render_template, send_from_directory, request, Blueprint
import os 
from datetime import datetime

try:
    from .tvcore.tvstreamer import TVStreamManager
    from .tvcore.tvdatabase import TVDatabase
    from .tvcore.programmanager import ProgramManager
    from .tvcore.mediapathmanager import MediaPathManager
    from .tvcore.tvconfig import TVConfig
except ImportError:
    from tvcore.tvstreamer import TVStreamManager
    from tvcore.tvdatabase import TVDatabase
    from tvcore.programmanager import ProgramManager
    from tvcore.mediapathmanager import MediaPathManager
    from tvcore.tvconfig import TVConfig


stream_app = Blueprint(
    'streaming', 
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/tvstreamer/static'      
)

tv_stream = TVStreamManager()
tv_stream.start_monitoring()


tv_config = TVConfig()
tv_db = TVDatabase()
program_manager = ProgramManager()
path_manager = MediaPathManager()


# ============ STREAMING PAGES ============
@stream_app.route('/tvstream')
def tvstream():
    return render_template('tvstream.html', offset=tv_stream.offset)

# ============= ADMIN PAGES =============

@stream_app.route('/admin/schedule')
def admin():
    schedule_data, series_data, movie_data = program_manager.initialize_admin_page()

    timeslots = tv_config.get_time_slots()
    genres = sorted(tv_config.get_genres())

    return render_template('admin_schedule.html', schedule_data=schedule_data, series_data=series_data, movie_data=movie_data, genres=genres, timeslots=timeslots)

@stream_app.route('/admin/save_schedule', methods=['POST'])
def save_schedule():
    data = request.get_json()

    return return_status(*program_manager.save_schedule(data))

@stream_app.route('/admin/delete_schedule', methods=['POST'])
def delete_schedule():
    data = request.get_json()

    return return_status(*program_manager.delete_schedule(data["day"], data["time"]))
    
@stream_app.route('/admin/add_program', methods=['POST'])
def add_program():
    data = request.get_json()

    return return_status(*program_manager.add_or_update_program(data))

@stream_app.route('/admin/delete_program', methods=['POST'])
def delete_program():
    data = request.get_json()

    return return_status(*program_manager.delete_program(data["program_id"], data["program_type"]))

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

@stream_app.route('/api/fetch_metadata/<program_type>/<int:tmdb_id>', methods=['GET'])
def fetch_metadata(program_type,tmdb_id):
    metadata = program_manager.fetch_metadata(program_type, tmdb_id)

    return jsonify(metadata)

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
        return render_template("admin_panel.html")

    app.run(host='0.0.0.0', port=5001, debug=True)
