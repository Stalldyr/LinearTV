from flask import Flask, jsonify, render_template, send_from_directory, request, Blueprint, Response
import os 
from datetime import datetime
import time
import json

try:
    from .tvcore.tvdatabase import TVDatabase
    from .tvcore.programmanager import ProgramManager
    from .tvcore.mediapathmanager import MediaPathManager
    from .tvcore.metadatafetcher import MetaDataFetcher
    from .tvcore.broadcastmonitor import BroadcastMonitor
except ImportError:
    from tvcore.tvdatabase import TVDatabase
    from tvcore.programmanager import ProgramManager
    from tvcore.mediapathmanager import MediaPathManager
    from tvcore.metadatafetcher import MetaDataFetcher
    from tvcore.broadcastmonitor import BroadcastMonitor


stream_app = Blueprint(
    'streaming', 
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/tvstreamer/static'      
)

tv_db = TVDatabase()
program_manager = ProgramManager()
path_manager = MediaPathManager()
metadata_fetcher = MetaDataFetcher()
broadcast_monitor = BroadcastMonitor()

#broadcast_monitor.start_monitoring()

# ============ STREAMING PAGES ============

@stream_app.route('/tvstream')
def tvstream():
    return render_template('tvstream.html')

@stream_app.route('/video/<content_type>/<directory>/<filename>')
def serve_video(content_type, directory, filename):
    return send_from_directory(path_manager.get_program_dir(content_type, directory), filename)


@stream_app.route('/test')
def test():
    return send_from_directory('downloads/series/lotto', 'lotto_s2025e03.nb-ttv.vtt')

# ============= ADMIN PAGES =============

@stream_app.route('/admin/schedule')
def admin():
    return render_template('admin_schedule.html', **program_manager.initialize_admin_page())

@stream_app.route('/admin/preparer')
def prepare():
    return render_template("admin_preparer.html")

#CRUD

@stream_app.route('/admin/save_schedule', methods=['POST'])
def save_schedule():
    data = request.get_json()
    return return_status(*program_manager.save_schedule(data))

@stream_app.route('/admin/delete_schedule', methods=['POST'])
def delete_schedule():
    data = request.get_json()
    return return_status(*program_manager.delete_schedule(data["day"], data["time"]))
    
@stream_app.route('/admin/save_program', methods=['POST'])
def save_program():
    data = request.get_json()
    return return_status(*program_manager.save_program(data))

@stream_app.route('/admin/delete_program', methods=['POST'])
def delete_program():
    data = request.get_json()
    return return_status(*program_manager.delete_program(data["program_id"], data["program_type"]))

# ============ API ROUTES ============

#Stream

#TODO: SSE doesn't work ideally on deployment. 
"""
@stream_app.route('/stream/current')
def current_program():
    def current_stream():
        last_id = None
        while True:
            current = broadcast_monitor.get_current_stream()
            if current is not None and current.get("id") != last_id:
                yield f"data: {json.dumps(current)}\n\n"
                last_id = current["id"]
                
            time.sleep(1)

    return Response(current_stream(), mimetype="text/event-stream")
""" 

@stream_app.route('/stream/current')
def current_program():
    return jsonify(broadcast_monitor.current_stream)

@stream_app.route('/stream/status')
def status():
    return jsonify(broadcast_monitor.get_current_status())

#TV-Schedule

@stream_app.route('/api/schedule')
def get_schedule():
    return jsonify(tv_db.get_weekly_schedule())

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

#TMDB

@stream_app.route('/tmdb/<program_type>/<int:tmdb_id>', methods=['GET'])
def fetch_metadata(program_type,tmdb_id):
    return jsonify(metadata_fetcher.fetch_tmdb_metadata(program_type, tmdb_id))


def return_status(success, message, error_code = None, debug=False):
    """Helper function for status"""
    if debug:
        print(message)

    if success:
        return jsonify({"status": "success", "message": message})
    else:
        return jsonify({"status": "error", "message": message}), error_code


def test_run():
    app = Flask(__name__)
    app.register_blueprint(stream_app)

    test_time = None 
    if os.getenv('TEST_TIME'):
        test_time = datetime.strptime(os.getenv('TEST_TIME'), "%Y-%m-%d %H:%M")

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        broadcast_monitor = BroadcastMonitor(time=test_time, debug=True)
        broadcast_monitor.start_monitoring()

    @app.route('/')
    def setup_index():
        return render_template("admin_panel.html")

    app.run(host='0.0.0.0', port=5001, debug=True)

if __name__ == '__main__':
    test_run()



