from flask import Blueprint, Response, request

from lineartvstream.tvcore.tvdatabase import TVDatabase
from lineartvstream.tvcore.metadatafetcher import MetaDataFetcher
from lineartvstream.ui.admin_forms import (
    SeriesForm, MovieForm, ScheduleForm, EpisodesForm,
    SeasonForm, ChannelForm
)
from lineartvstream.ui.stream_html import stream_channel_panel

htmx = Blueprint(
    'htmx',
    __name__,
    url_prefix="/admin/partials",
)

tv_db = TVDatabase()
metadata_fetcher = MetaDataFetcher()


# ============ CHANNEL ============

@htmx.route("/channel/form", methods=['GET'])
def channel_form_open():
    channel_id = request.args.get("channel_id")
    channel = tv_db.get_channels(channel_id=channel_id)
    return ChannelForm(channel).form().dump()

# ============ SERIES ============

@htmx.route("/series/form", methods=['GET'])
def series_form_open():
    series_id = request.args.get("series_id")
    series = tv_db.get_series(series_id=series_id)
    return SeriesForm(series).form().dump()

# ============ MOVIE ============

@htmx.route("/movies/form", methods=['GET'])
def movie_form_open():
    movie_id = request.args.get("movie_id")
    movie = tv_db.get_movies(movie_id=movie_id)
    return MovieForm(movie).form().dump()

# ============ EPISODES ============

@htmx.route("/episodes/form", methods=['GET'])
def episodes_form_open():
    episode_id = request.args.get("episode_id")
    episode = tv_db.get_episodes(episode_id=episode_id)
    return EpisodesForm(episode).form().dump()

# ============ SEASON ============
# TODO

@htmx.route("/season/form")
def season_form_open():
    pass


# ============ ADS ============
# TODO

@htmx.route("/ads/form")
def ad_form_open():
    pass


# ============ SCHEDULE ============

@htmx.route("/schedule/form", methods=['GET'])
def schedule_form_open():
    schedule_id = request.args.get("schedule_id")
    schedule = tv_db.get_schedule(schedule_id=schedule_id)
    print(schedule)
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