from .tvcore.tvstreamer import TVStreamManager
from .tvcore.tvdatabase import TVDatabase
from .tvcore.programmanager import ProgramManager
from .tvcore.mediapathmanager import MediaPathManager
from flask import Flask, jsonify, render_template, send_from_directory, request, Blueprint
from pathlib import Path
import os

stream_app = Blueprint(
    'streaming', 
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/tvstreamer/static'      
) 

tv_stream = TVStreamManager()
tv_db = TVDatabase()
program_manager = ProgramManager()
path_manager = MediaPathManager()

#Stream page
@stream_app.route('/tvstream')
def stream():
    return render_template('tvstream.html')

# ============ ADMIN PAGES ============

@stream_app.route('/admin')
def admin():  
    schedule_data, series_data, movie_data = program_manager.initialize_admin_page()
    
    #Should be improved on eventually
    import json

    with open(Path(__file__).parent.absolute()/"config.json", 'r', encoding='utf-8') as f:
        tv_config =  json.load(f)

    return render_template('admin.html', schedule_data=schedule_data, series_data=series_data, movie_data=movie_data, tv_config=tv_config)

@stream_app.route('/admin/save_schedule', methods=['POST'])
def save_schedule():
    data = request.get_json()

    print(f"Recived data for weekly schedule: {data}")

    return return_status(*program_manager.save_schedule(data))
    
@stream_app.route('/admin/add_program', methods=['POST'])
def add_program():
    data = request.get_json()

    print(f"Recieved data for new program: {data}")

    return return_status(*program_manager.create_or_update_program(data))

@stream_app.route('/admin/delete_program', methods=['POST'])
def delete_program():
    data = request.get_json()

    return return_status(*program_manager.delete_program(data["program_id"], data["program_type"]))

# ============ API ROUTES ============

@stream_app.route('/video/<content_type>/<directory>/<filename>')
def serve_video(content_type, directory, filename):
    return send_from_directory(path_manager.get_program_dir(content_type, directory), filename) #Might reassign to programmanager or mediapathmanager

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

@stream_app.route('/api/kept_episodes')
def get_kept_episodes():
    return jsonify(tv_db.get_kept_episodes())

@stream_app.route('/api/obsolete_episodes')
def get_obsolete_episodes():
    return jsonify(tv_db.get_obsolete_episodes())


def return_status(success, message, error_code = None, debug=False):
    if debug:
        print(message)

    if success:
        return jsonify({"status": "success", "message": message})
    else:
        return jsonify({"status": "error", "message": message}), error_code
    

if __name__ == '__main__':
    stream_app.run(host='0.0.0.0', port=5000, debug=True)

tv_stream.start_monitoring()