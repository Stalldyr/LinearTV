from flask import Flask, jsonify, render_template, send_from_directory, request, Blueprint
import os 
from datetime import datetime

try:
    from .htmx_partials import htmx
    from .tvcore.tvdatabase import TVDatabase
    from .tvcore.programmanager import ProgramManager
    from .tvcore.mediapathmanager import MediaPathManager
    from .tvcore.metadatafetcher import MetaDataFetcher
    from .tvcore.broadcastmonitor import BroadcastMonitor
    from .templates.stream_html import *
    from .templates.html_base import base
    from .templates.admin_schedule import admin_schedule_body, form_status
except ImportError:
    from tvcore.tvdatabase import TVDatabase
    from tvcore.programmanager import ProgramManager
    from tvcore.mediapathmanager import MediaPathManager
    from tvcore.metadatafetcher import MetaDataFetcher
    from tvcore.broadcastmonitor import BroadcastMonitor
    from templates.html_base import base
    from templates.stream_html import *
    from templates.admin_schedule import admin_schedule_body, form_status

stream_app = Blueprint(
    'streaming', 
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/tvstreamer/static'      
)

stream_app.register_blueprint(htmx)

tv_db = TVDatabase()
program_manager = ProgramManager()
path_manager = MediaPathManager()
metadata_fetcher = MetaDataFetcher()
broadcast_monitor = BroadcastMonitor()

# ============ STREAMING PAGES ============

@stream_app.route('/tvstream')
def tvstream():
    return render_template("tvstream.html")


# ============= ADMIN PAGES =============

@stream_app.route('/admin/schedule')
def schedule():
    html = base("Admin", "Administrative panel for managing broadcasting schedule")
    html.extend("body", admin_schedule_body())
    return html.dump()

@stream_app.route('/admin/preparer')
def prepare():
    return render_template("admin_preparer.html")


# ============= FILE ROUTING =============

@stream_app.route('/video/noprogram')
def noprogram_video():
    return send_from_directory(path_manager.download_path / "ads", "PM5544.mp4")

@stream_app.route('/video/<content_type>/<directory>/<filename>')
def serve_video(content_type, directory, filename):
    return send_from_directory(path_manager.get_program_dir(content_type, directory), filename)


# ============= ADMIN CRUD =============
    
@stream_app.route('/admin/series/save', methods=['POST'])
def save_series():
    success, message, error = program_manager.save_series(request.form)
    return form_status(message).dump()

@stream_app.route('/admin/series/delete', methods=['POST'])
def delete_series():
    data = request.form
    series_id = data.get("program_id", None)

    if series_id:
        success, message, error = program_manager.delete_series(series_id)
        return form_status(message).dump()
    else:
        return form_status("No series").dump()
    

@stream_app.route('/admin/movie/save', methods=['POST'])
def save_movie():
    success, message, error = program_manager.save_movie(request.form)
    return form_status(message).dump()
    
@stream_app.route('/admin/movie/delete', methods=['POST'])
def delete_movie():
    data = request.form
    movie_id = data.get("program_id", None)

    if movie_id:
        success, message, error = program_manager.delete_movie(movie_id)
        return form_status(message).dump()
    else:
        return form_status("No movie").dump()


@stream_app.route('/admin/episode/save', methods=['POST'])
def save_episode():
    success, message, error = program_manager.save_episode(request.form)
    return form_status(message).dump()
    
@stream_app.route('/admin/episode/delete', methods=['POST'])
def delete_episode():
    data = request.form
    episode_id = data.get("episode_id", None)

    if episode_id:
        success, message, error = program_manager.delete_episode(episode_id)
        return form_status(message).dump()
    else:
        return form_status("No movie").dump()

@stream_app.route('/admin/schedule/save', methods=['POST'])
def save_schedule():
    success, message, error = program_manager.save_schedule(request.form)

    return form_status(message).dump()

@stream_app.route('/admin/schedule/update', methods=['POST'])
def update_schedule():
    success, message, error = program_manager.update_schedule(request.form)

    return form_status(message).dump()

@stream_app.route('/admin/schedule/delete', methods=['POST'])
def delete_schedule():
    data = request.get_json()
    program_manager.delete_schedule()
    return 

# ============ API ROUTES ============

#Stream

@stream_app.route('/stream/<channel>')
def current_program(channel):
    return broadcast_monitor.get_current_program(channel)

@stream_app.route('/api/schedule', methods=['GET'])
def get_schedule():
    #TODO: Create pydantic model
    channel = request.args.get("channel", None)
    date = request.args.get("date", None)
    full_week = request.args.get("full_week", False)
    full_week_bool = True if full_week in ["true", "True", "1"] else False

    return jsonify([obj.model_dump() for obj in tv_db.get_current_week_schedule(channel=channel, date=date, full_week=full_week_bool)])

@stream_app.route('/api/pending')
def get_pending_episodes():
    return jsonify([obj.model_dump() for obj in tv_db.get_pending_programs()])

@stream_app.route('/api/scheduled')
def get_scheduled_episodes():
    return jsonify([obj.model_dump() for obj in tv_db.get_schedule()])

@stream_app.route('/api/obsolete')
def get_obsolete_episodes():
    return jsonify([obj.model_dump() for obj in tv_db.get_obsolete_programs()])

#TMDB

@stream_app.route('/tmdb/<program_type>/<int:tmdb_id>', methods=['GET'])
def fetch_metadata(program_type,tmdb_id):
    return jsonify(metadata_fetcher.fetch_tmdb_metadata(program_type, tmdb_id))


# ============= TEST RUN =============

def test_run():
    app = Flask(__name__)
    app.register_blueprint(stream_app)

    test_time = None
    test_acc = 1
    if os.getenv('TEST_TIME'):
        test_time = datetime.strptime(os.getenv('TEST_TIME'), "%Y-%m-%d %H:%M")

    if os.getenv('TEST_ACC'):
        test_acc = int(os.getenv('TEST_ACC'))

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        broadcast_monitor = BroadcastMonitor(time=test_time, time_acceleration=test_acc, debug=True)
        broadcast_monitor.start_monitoring()

    @app.route('/')
    def setup_index():
        return render_template("admin_panel.html")

    app.run(host='0.0.0.0', port=5001, debug=True)

if __name__ == '__main__':
    test_run()



