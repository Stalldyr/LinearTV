from flask import Flask, jsonify, render_template, send_from_directory, request, Blueprint, Response
import os, random
from datetime import datetime
from time import sleep
from markupsafe import escape

from hypermedia import Div, H2, P
from lineartvstream.tvcore.helper import calculate_offset
from lineartvstream.routes.htmx_partials import htmx, htmx_admin
from lineartvstream.routes.admin_crud import admin_crud
from lineartvstream.tvcore.tvdatabase import TVDatabase
from lineartvstream.tvcore.mediapathmanager import MediaPathManager
from lineartvstream.tvcore.metadatafetcher import MetaDataFetcher
from lineartvstream.tvcore.broadcastmonitor import BroadcastMonitor
from lineartvstream.ui.admin_pages import admin_panel
from lineartvstream.ui.stream_html import stream_html

stream_app = Blueprint(
    'streaming', 
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/streaming/static'
)

stream_app.register_blueprint(htmx_admin)
stream_app.register_blueprint(htmx)
stream_app.register_blueprint(admin_crud)

tv_db = TVDatabase()
path_manager = MediaPathManager()
metadata_fetcher = MetaDataFetcher()
broadcast_monitor = BroadcastMonitor()

# ============ STREAMING PAGES ============

@stream_app.route('/tvstream')
def tvstream():
    return stream_html().dump()

# ============= FILE ROUTING =============

@stream_app.route('/video/noprogram')
def noprogram_video():
    ads = [p.name for p in path_manager.ad_path.iterdir() if p.is_file()]
    if ads:
        return send_from_directory(path_manager.ad_path.resolve(), random.choice(ads))


@stream_app.route('/video/<content_type>/<directory>/<filename>')
def serve_video(content_type, directory, filename):
    return send_from_directory(path_manager.media_path.resolve()/content_type/directory, filename)

# ============ API ROUTES ============

#Stream
@stream_app.route('/stream/<channel>/events')
def stream_events(channel):
    def event_stream():
        last_program_id = None

        while True:
            current_time = broadcast_monitor.get_current_time()
            current = tv_db.get_current_program(channel, time=current_time)
            if current:
                program_id = current.id
                offset = calculate_offset(current.start, current_time)
                source = current.filepath or ""
                status = current.status

                title = current.title
                if current.rerun:
                    title += " (R)"
                timeslot = f"{current.start.strftime("%H:%M")} - {current.end.strftime("%H:%M")}"
                description = current.description

            else:
                next = tv_db.get_next_program(channel, time=current_time)
                if next:
                    program_id = -2
                    offset = 0
                    source = 'noprogram'
                    status = next.status

                    title = f"Neste program: {next.title}"
                    timeslot = f"{next.start.strftime("%H:%M")} - {next.end.strftime("%H:%M")}"
                    description = next.description
                else:
                    program_id = -1
                    offset = 0
                    source = 'noprogram'
                    status = "no_program"

                    title = "Ingen program på dette tidspunktet"
                    timeslot = ""
                    description = "Det er en stund til neste program starter. Sjekk TV-guide"


            if program_id != last_program_id:
                last_program_id = program_id

                html = Div(
                    H2(title),
                    P(timeslot),
                    P(description),
                    id="program-info",
                    data_source=escape(source),
                    data_offset=offset,
                    data_status=escape(status)
                )

                yield f"event: program-update\ndata: {html.dump()}\n\n"

            sleep(1)

    return Response(event_stream(), mimetype='text/event-stream')

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
    data = metadata_fetcher.fetch_tmdb_metadata(program_type, tmdb_id)
    if data is None:
        return jsonify({"error": "Could not fetch TMDB metadata"}), 502
    return jsonify(data)

# ============= TEST RUN =============

def test_run():
    app = Flask(__name__)
    app.register_blueprint(stream_app)

    test_time = datetime(2026,8,27,19,57)
    test_acc = 30

    if os.getenv('TEST_TIME'):
        test_time = datetime.strptime(os.getenv('TEST_TIME'), "%Y-%m-%d %H:%M")

    if os.getenv('TEST_ACC'):
        test_acc = int(os.getenv('TEST_ACC'))

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        broadcast_monitor = BroadcastMonitor(time=test_time, time_acceleration=test_acc, debug=True)
        broadcast_monitor.start_monitoring()

    @app.route('/')
    def setup_index():
        return admin_panel().dump()

    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)

if __name__ == '__main__':
    test_run()



