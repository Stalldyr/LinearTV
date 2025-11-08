from flask import Flask, jsonify, render_template, send_from_directory, request
from datetime import datetime, timedelta
from TVstreamer import TVStreamManager
from TVdatabase import TVDatabase
from TVdownloader import TVDownloader
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash
import os
import sys
import helper
import TVtracker

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

tv_stream = TVStreamManager()
tv_db = TVDatabase()
tv_dl = TVDownloader()

#Index page
@app.route('/')
def index():
    return render_template('index.html')

#TV streaming page
@app.route('/tv')
def tv():
    episode_info = tv_stream.current_stream
    episode_id = episode_info.get("id", None)
    ip_address = request.remote_addr

    if episode_id:
        TVtracker.log_view(episode_id,ip_address)

    return render_template('tv.html')

#TV streaming page
@app.route('/tvguide')
def tvguide():
    return render_template('tvguide.html')

#MTV page
@app.route('/mtv')
def mtv():
    return render_template('mtv.html')

#MTV page
@app.route('/chat')
def chat():
    return render_template('chat.html')

#Info page
@app.route('/info')
def info():
    return render_template('info.html')

#Links page
@app.route('/links')
def links():
    return render_template('links.html')

#Gamja page
@app.route('/gamja/')
@app.route('/gamja/<path:path>')
def serve_gamja(path='index.html'):
    return send_from_directory(os.path.join(BASE_DIR, 'gamja'), path)

# ============ ADMIN PAGES ============
auth = HTTPBasicAuth()
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$Rk2fJmaIfyGgnuLN$a50e8a6e564506cb60563386a62c48392f489885298ae1bcb92b1f3f7b24008986586df534616d495aff6f36db2339c995804fa554c004e99c6b6fbe93ae207f"

@auth.verify_password
def verify_password(username, password):
    if check_password_hash(ADMIN_PASSWORD_HASH, password):
        return username
    return None

#Admin page
@app.route('/admin')
@auth.login_required
def admin():  
    schedule_data = tv_db.get_weekly_schedule()
    series_data = tv_db.get_all_series()
    movie_data = tv_db.get_all_movies()

    for series in series_data:
        series['blocks'] = helper._calculate_blocks(series['duration'])

    return render_template('admin.html', schedule_data=schedule_data, series_data=series_data, movie_data=movie_data)

# Oppdater save_program ruten
@app.route('/admin/save_schedule', methods=['POST'])
@auth.login_required
def save_schedule():
    data = request.get_json()

    print(f"Mottatt data for lagring: {data}")

    #tv_dl.prepare_weekly_schedule()

    return tv_db.save_schedule_entry(data)
    
@app.route('/admin/add_program', methods=['POST'])
@auth.login_required
def add_program():
    data = request.get_json()

    print(f"Mottatt data for nytt program: {data}")
    
    return tv_db.add_program(data)

# ============ API ROUTES ============

@app.route('/video/<directory>/<filename>')
def serve_video(directory, filename):
    return send_from_directory(f'downloads/{directory}', filename)

@app.route('/api/current')
def current_program():
    return jsonify(tv_stream.current_stream)
    
@app.route('/api/next')
def next_program():
    program = tv_stream.get_next_program()
    if program:
        return jsonify(program)
    else:
        return jsonify({"error": "No program currently streaming"}), 404

@app.route('/api/schedule')
def get_schedule():
    schedule = tv_db.get_weekly_schedule()
    print(f"Schedule requested: {schedule}")
    return jsonify(schedule)

@app.route('/api/status')
def status():
    return jsonify(tv_stream.get_current_status())

@app.route('/api/time')
def get_time():
    time = datetime.now().time()
    return [time.strftime("%H")]

@app.route('/api/local_pending_episodes')
def get_local_pending_episodes():
    pending = tv_db.get_local_pending_episodes()
    return jsonify(tv_db.get_local_pending_episodes())


@app.route('/api/traffic', methods=['POST'])
def get_traffic():
    seconds = request.get_json()["seconds"]
    episode_id = tv_stream.current_stream.get("id", None)
    ip_address = request.remote_addr

    if episode_id:
        TVtracker.update_time(seconds, episode_id, ip_address)
    
    return {'status': 'ok'}

if __name__ == '__main__':
    test_time = None
    if len(sys.argv)>1:
        test_time = datetime.strptime(sys.argv[1], "%Y-%m-%d %H:%M")

    tv_stream = TVStreamManager(time=test_time)
    tv_stream.start_monitoring()

    app.run(host='0.0.0.0', port=5001, debug=True)

tv_stream.start_monitoring()
