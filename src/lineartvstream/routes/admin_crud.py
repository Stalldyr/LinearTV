from flask import Blueprint, request, redirect
from lineartvstream.tvcore.programCRUDmanager import ProgramManager

admin_crud = Blueprint(
    'admin_crud',
    __name__,
)

program_manager = ProgramManager()

from lineartvstream.ui.html_base import base
from hypermedia import * 
from lineartvstream.ui.admin_pages import episodes_body, channels_body, series_body, movies_body, schedule_body, genres_body
from lineartvstream.tvcore.tvdatabase import TVDatabase

tv_db = TVDatabase()

@admin_crud.route('/admin/preparer')
def prepare():
    return ""

@admin_crud.route('/admin/series', methods=['GET', 'POST'])
def series_page():
    if request.method == 'POST':
        program_manager.update_series(request.form)
        return redirect('/admin/series')

    series_id = request.args.get('series_id')
    series = tv_db.get_series(series_id=series_id)

    html = base("Series", "Administrer serier")
    html.extend("body", series_body(series))
    return html.dump()

@admin_crud.route('/admin/movies', methods=['GET', 'POST'])
def movies_page():
    if request.method == 'POST':
        program_manager.update_movie(request.form)
        return redirect('/admin/movies')

    movie_id = request.args.get('movie_id')
    movies = tv_db.get_movies(movie_id=movie_id)

    html = base("Movies", "Administrate movies")
    html.extend("body", movies_body(movies))
    return html.dump()

@admin_crud.route('/admin/episodes', methods=['GET', 'POST'])
def episodes_page():
    if request.method == 'POST':
        program_manager.update_episode(request.form)
        return redirect(f"/admin/episodes?series_id={series_id}")

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
        program_manager.update_schedule(request.form)
        return redirect(f"/admin/schedule")

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
        program_manager.update_channels(request.form)
        return redirect(f"/admin/channels")

    channels = tv_db.get_channels()

    edit_id = request.args.get('edit')
    editing_channel = tv_db.get_channel(channel_id=edit_id) if edit_id else None

    html = base("Channels", "Administrate TV-channels")
    html.extend("body", channels_body(channels, editing_channel))
    return html.dump()

@admin_crud.route('/admin/genres', methods=['GET', 'POST'])
def genres_page():
    if request.method == 'POST':
        program_manager.update_genres(request.form)
        return redirect(f"/admin/genres")

    genres = tv_db.get_genres()

    edit_id = None #request.args.get('edit')
    editing_channel = tv_db.get_channel(channel_id=edit_id) if edit_id else None

    html = base("Genres", "Administrate genres")
    html.extend("body", genres_body(genres, editing_channel))
    return html.dump()





