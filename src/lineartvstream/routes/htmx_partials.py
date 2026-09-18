from flask import Blueprint, Response, request

from lineartvstream.tvcore.tvdatabase import TVDatabase
from lineartvstream.tvcore.metadatafetcher import MetaDataFetcher
from lineartvstream.ui.admin_forms import (
    GenreForm, SeasonScheduleForm, SeriesForm, MovieForm, ScheduleForm, EpisodesForm,
    SeasonForm, ChannelForm
)
from lineartvstream.ui.stream_html import stream_channel_panel

htmx_admin = Blueprint(
    'htmx_admin',
    __name__,
    url_prefix="/admin/partials",
)

htmx = Blueprint(
    'htmx',
    __name__,
    url_prefix="/partials",
)

tv_db = TVDatabase()
metadata_fetcher = MetaDataFetcher()


# ============ CHANNEL ============

@htmx_admin.route("/channel/form", methods=['GET'])
def channel_form_open():
    channel_id = request.args.get("channel_id")
    channel = tv_db.get_channels(id=channel_id)[0] if channel_id else None

    return ChannelForm(channel).form().dump()

# ============ GENRES ============

@htmx_admin.route("/genres/form", methods=['GET'])
def genres_form_open():
    genre_id = request.args.get("genre_id")
    genre = tv_db.get_genres(id=genre_id)[0] if genre_id else None

    return GenreForm(genre).form().dump()

# ============ SERIES ============

@htmx_admin.route("/series/form", methods=['GET'])
def series_form_open():
    series_id = request.args.get("series_id")
    series = tv_db.get_series(series_id=series_id)[0] if series_id else None
    return SeriesForm(series).form().dump()

# ============ MOVIE ============

@htmx_admin.route("/movies/form", methods=['GET'])
def movie_form_open():
    movie_id = request.args.get("movie_id")
    movie = tv_db.get_movies(movie_id=movie_id) if movie_id else None
    return MovieForm(movie).form().dump()

# ============ EPISODES ============

@htmx_admin.route("/episodes/form", methods=['GET'])
def episodes_form_open():
    episode_id = request.args.get("episode_id")
    series_id = request.args.get("series_id")

    episode = tv_db.get_episodes(episode_id=episode_id) if episode_id else None
    return EpisodesForm(episode, series_id=series_id).form().dump()

# ============ SEASON ============

@htmx_admin.route("/season/form", methods=['GET'])
def season_form_open():
    series_id = request.args.get("series_id")
    return SeasonForm(series_id=series_id).form().dump()

# ============ SEASON SCHEDULE ============

@htmx_admin.route("/season-schedule/form", methods=['GET'])
def season_schedule_form_open():
    series_id = request.args.get("series_id")
    return SeasonScheduleForm(series_id=series_id).form().dump()

# ============ SCHEDULE ============

@htmx_admin.route("/schedule/form", methods=['GET'])
def schedule_form_open():
    schedule_id = request.args.get("schedule_id")
    schedule = tv_db.get_schedule(schedule_id=schedule_id)
    return ScheduleForm(schedule).form().dump()

# ============ TMDB ============

@htmx.route("/tmdb-fetch/series")
def tmdb_fetch_series():
    tmdb_id = request.args.get("tmdb_id")

    if not tmdb_id:
        return Response(status=204, headers={"HX-Reswap": "none"})

    data = metadata_fetcher.get_tmdb_series_data(tmdb_id=int(tmdb_id))
    program = metadata_fetcher.extract_series_info_from_tmdb(data)
    return SeriesForm(program).form().dump()

@htmx.route("/tmdb-fetch/movie")
def tmdb_fetch_movie():
    tmdb_id = request.args.get("tmdb_id")

    if not tmdb_id:
        return Response(status=204, headers={"HX-Reswap": "none"})

    data = metadata_fetcher.get_tmdb_movie_data(tmdb_id=int(tmdb_id))
    program = metadata_fetcher.extract_movie_info_from_tmdb(data)
    return MovieForm(program).form().dump()

# ============ STREAM ============

@htmx.route("/stream/panel/<channel>")
def stream_panel(channel):
    return stream_channel_panel(channel).dump()