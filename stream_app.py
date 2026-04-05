from flask import Flask, jsonify, render_template, send_from_directory, flash, request, Blueprint, Response
import os 
from datetime import datetime

try:
    from .tvcore.tvdatabase import TVDatabase
    from .tvcore.programmanager import ProgramManager
    from .tvcore.mediapathmanager import MediaPathManager
    from .tvcore.metadatafetcher import MetaDataFetcher
    from .tvcore.broadcastmonitor import BroadcastMonitor
    from .templates.stream_html import *
    from .templates.admin_schedule import AdminPanel, base_schedule, SeriesForm, MovieForm
except ImportError:
    from tvcore.tvdatabase import TVDatabase
    from tvcore.programmanager import ProgramManager
    from tvcore.mediapathmanager import MediaPathManager
    from tvcore.metadatafetcher import MetaDataFetcher
    from tvcore.broadcastmonitor import BroadcastMonitor
    from templates.stream_html import *
    from tvstreamer.templates.admin_schedule import AdminPanel, base_schedule, SeriesForm, MovieForm


# ============ STREAMING PAGES ============

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

# ============ STREAMING PAGES ============

@stream_app.route('/tvstream')
def tvstream():
    return render_template("tvstream.html")

@stream_app.route('/video/noprogram')
def noprogram_video():
    return send_from_directory(path_manager.download_path / "ads", "PM5544.mp4")

@stream_app.route('/video/<content_type>/<directory>/<filename>')
def serve_video(content_type, directory, filename):
    return send_from_directory(path_manager.get_program_dir(content_type, directory), filename)

# ============= ADMIN PAGES =============

@stream_app.route('/admin/schedule')
def admin():
    return base_schedule().dump()

@stream_app.route('/admin/preparer')
def prepare():
    return render_template("admin_preparer.html")

#CRUD

@stream_app.route('/admin/save/schedule', methods=['POST'])
def save_schedule():
    data = request.form
    return return_status(*program_manager.save_schedule(data))
    
@stream_app.route('/admin/save/series', methods=['POST'])
def save_series():
    data = request.form
    flash("test")
    return return_status(*program_manager.save_series(data))

@stream_app.route('/admin/save/movie', methods=['POST'])
def save_movie():
    data = request.form
    return return_status(*program_manager.save_movie(data))

@stream_app.route('/admin/delete/program', methods=['POST'])
def delete_program():
    data = request.form
    print(data)
    return ""
    #return return_status(*program_manager.delete_program(data["program_id"], data["program_type"]))

@stream_app.route('/admin/delete/schedule', methods=['POST'])
def delete_schedule():
    data = request.get_json()
    return return_status(*program_manager.delete_schedule())

# ============ API ROUTES ============

#Stream

#TODO: SSE doesn't work on deployment. 
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
    return jsonify([obj.model_dump() for obj in tv_db.get_scheduled_programs()])

@stream_app.route('/api/obsolete')
def get_obsolete_episodes():
    return jsonify([obj.model_dump() for obj in tv_db.get_obsolete_programs()])

#TMDB

@stream_app.route('/tmdb/<program_type>/<int:tmdb_id>', methods=['GET'])
def fetch_metadata(program_type,tmdb_id):
    return jsonify(metadata_fetcher.fetch_tmdb_metadata(program_type, tmdb_id))

#HTMX

panel = AdminPanel()

@stream_app.route("/admin/partials/program-form-open")
def program_form_open():
    panel.visible = True
    series_data = tv_db.get_series()
    return panel.program_form_panel(series_data, SeriesForm).dump()

@stream_app.route("/admin/partials/program-form-close")
def program_form_close():
    panel.visible = False
    return panel.program_form_panel([], SeriesForm).dump()

@stream_app.route("/admin/partials/program-type-select")
def program_type_select():
    program_type = request.args.get("programType")
    
    if program_type == "series":
        program_data = tv_db.get_series()
        return panel.program_form_panel(program_data, SeriesForm).dump()
    elif program_type == "movie":
        program_data = tv_db.get_movies()
        return panel.program_form_panel(program_data, MovieForm).dump()

@stream_app.route("/admin/partials/program-select")
def program_select():
    program_id = request.args.get("program_id")
    program_type = request.args.get("programType")

    if program_type == "series":
        program = tv_db.get_series(series_id=program_id) if program_id else None
        return SeriesForm(program).render().dump()
    elif program_type == "movie":
        program = tv_db.get_movies(movie_id=program_id) if program_id else None
        return MovieForm(program).render().dump()

@stream_app.route("/admin/partials/schedule-form-open")
def schedule_form_open():
    panel.visible = True
    series_data = tv_db.get_series()
    return panel.schedule_form_panel(series_data).dump()

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



