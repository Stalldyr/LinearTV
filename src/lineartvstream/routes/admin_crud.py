from flask import Blueprint, request
from lineartvstream.tvcore.programCRUDmanager import ProgramManager
from lineartvstream.ui.html_base import base
from lineartvstream.ui.admin_pages import episodes_body, channels_body, series_body, movies_body, schedule_body, genres_body, form_status, season_schedule_results
from lineartvstream.tvcore.tvdatabase import TVDatabase
from datetime import datetime

admin_crud = Blueprint(
    'admin_crud',
    __name__,
)

program_manager = ProgramManager()
tv_db = TVDatabase()

def _handle_update(update_fn, form_data):
    message, status_code = update_fn(form_data)
    return form_status(message).dump(), status_code


@admin_crud.route('/admin/series', methods=['GET', 'POST'])
def series_page():
    if request.method == 'POST':
        return _handle_update(program_manager.update_series, request.form)
    
    series_id = request.args.get('series_id')
    series = tv_db.get_series(series_id=series_id)

    html = base("Series", "Administrer series")
    html.extend("body", series_body(series))
    return html.dump()

@admin_crud.route('/admin/movies', methods=['GET', 'POST'])
def movies_page():
    if request.method == 'POST':
        return _handle_update(program_manager.update_movie, request.form)

    movie_id = request.args.get('movie_id')
    movies = tv_db.get_movies(movie_id=movie_id)

    html = base("Movies", "Administrate movies")
    html.extend("body", movies_body(movies))
    return html.dump()

@admin_crud.route('/admin/episodes', methods=['GET', 'POST'])
def episodes_page():
    if request.method == 'POST':
        return _handle_update(program_manager.update_episode, request.form)

    series_id = request.args.get('series_id')
    episode_id = request.args.get('episode_id')

    if episode_id:
        episodes = [tv_db.get_episodes(episode_id=episode_id)]
    elif series_id:
        episodes = tv_db.get_episodes(series_id=series_id)
    else:
        episodes = tv_db.get_episodes()

    html = base("Episodes", "Administrate episodes")
    html.extend("body", episodes_body(episodes))
    return html.dump()

@admin_crud.route('/admin/schedule', methods=['GET', 'POST'])
def schedule_page():
    if request.method == 'POST':
        return _handle_update(program_manager.update_schedule, request.form)

    schedule_id = request.args.get("schedule_id")
    episode_id = request.args.get("episode_id")
    movie_id = request.args.get("movie_id")

    if schedule_id:
        schedule = [tv_db.get_schedule(schedule_id=schedule_id)]
    elif episode_id:
        schedule = tv_db.get_schedule(episode_id=episode_id)
    elif movie_id:
        schedule = tv_db.get_schedule(movie_id=movie_id)
    else:
        schedule = tv_db.get_schedule()

    html = base("Schedule", "Administrate schedule")
    html.extend("body", schedule_body(schedule))
    return html.dump()


@admin_crud.route('/admin/channels', methods=['GET', 'POST'])
def channels_page():
    if request.method == 'POST':
        return _handle_update(program_manager.update_channels, request.form)

    channels = tv_db.get_channels()

    html = base("Channels", "Administrate TV-channels")
    html.extend("body", channels_body(channels))
    return html.dump()


@admin_crud.route('/admin/genres', methods=['GET', 'POST'])
def genres_page():
    if request.method == 'POST':
        return _handle_update(program_manager.update_genres, request.form)

    genres = tv_db.get_genres()

    html = base("Genres", "Administrate genres")
    html.extend("body", genres_body(genres))
    return html.dump()


@admin_crud.route('/admin/season', methods=['POST'])
def save_season():
    form = request.form

    message, status_code = program_manager.add_season(
        series_id=form.get("series_id"),
        season_number=form.get("season_number"),
        source_url=form.get("source_url")
    )

    return form_status(message).dump(), status_code

@admin_crud.route('/admin/season-schedule', methods=['POST'])
def schedule_season_page():
    form = request.form

    try:
        start = datetime.fromisoformat(form.get("start"))
    except (ValueError, TypeError):
        return form_status("Invalid date/time").dump(), 400

    success, results, status_code = program_manager.schedule_season(
        series_id=form.get("series_id"),
        season_number=form.get("season_number"),
        channel=form.get("channel"),
        start=start,
        rerun=form.get("rerun") == 'on'
    )

    if not success:
        return form_status(results).dump(), status_code

    return season_schedule_results(results).dump(), status_code


