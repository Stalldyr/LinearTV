
from flask import Blueprint, Response, request
from datetime import datetime

try:
    from .tvcore.tvdatabase import TVDatabase
    from .tvcore.metadatafetcher import MetaDataFetcher
    from .templates.program_forms import SeriesForm, MovieForm, ScheduleForm, EpisodesForm, SeasonForm, NewScheduleForm
except ImportError:
    from tvcore.tvdatabase import TVDatabase
    from tvcore.metadatafetcher import MetaDataFetcher
    from templates.program_forms import SeriesForm, MovieForm, ScheduleForm, EpisodesForm, SeasonForm, NewScheduleForm

htmx = Blueprint(
    'htmx', 
    __name__,
)

tv_db = TVDatabase()
metadata_fetcher = MetaDataFetcher()

#Series form
@htmx.route("/admin/partials/series/form-open")
def series_form_open():
    series = tv_db.get_series()
    return SeriesForm().panel(series).dump()

@htmx.route("/admin/partials/series/fields")
def series_fields():
    program_id = request.args.get("program_id")
    program = tv_db.get_series(series_id=program_id) if program_id else None
    return SeriesForm(program).form().dump()

#Movie form
@htmx.route("/admin/partials/movie/form-open")
def movie_form_open():
    movies = tv_db.get_movies()
    return MovieForm().panel(movies).dump()

@htmx.route("/admin/partials/movie/fields")
def movie_fields():
    program_id = request.args.get("program_id")
    program = tv_db.get_movies(movie_id=program_id) if program_id else None
    return MovieForm(program).form().dump()


#Episodes form
@htmx.route("/admin/partials/episodes/form-open")
def episodes_form_open():
    series = tv_db.get_series()
    return EpisodesForm().panel(series).dump()

@htmx.route("/admin/partials/episodes/select")
def episodes_select():
    program_id = request.args.get("program_id")
    program = tv_db.get_episodes(series_id=program_id) if program_id else None
    return EpisodesForm().episode_dropdown(program).dump()

@htmx.route("/admin/partials/episodes/fields")
def episodes_fields():
    episode_id = request.args.get("episode_id")
    program = tv_db.get_episodes(episode_id=episode_id) if episode_id else None
    return EpisodesForm(program).form().dump()

#Season
@htmx.route("/admin/partials/season/form-open")
def season_form_open():
    series = tv_db.get_series()
    return SeasonForm().panel(series).dump()

@htmx.route("/admin/partials/season/fields")
def season_fields():
    series_id = request.args.get("program_id")
    program = tv_db.get_episodes(series_id=series_id) if series_id else None
    return SeasonForm(program).form().dump()


#Schedule Form
@htmx.route("/admin/partials/schedule/form-open")
def schedule_form_open():
    return ScheduleForm().panel().dump()

@htmx.route("/admin/partials/schedule/programs")
def schedule_programs():
    air_date = request.args.get("date")
    channel = request.args.get("channel")
    
    if air_date and channel:
        schedule = tv_db.get_schedule(date=air_date, channel=channel)
        return ScheduleForm().program_select(schedule).dump()
    
    else:
        return Response(status=204, headers={"HX-Reswap": "none"})

@htmx.route("/admin/partials/schedule/fields")
def schedule_fields():
    schedule_id = request.args.get("schedule_id")

    if schedule_id:
        schedule = tv_db.get_schedule(schedule_id=schedule_id)
        return ScheduleForm(schedule).form().dump()

    else:
        return Response(status=204, headers={"HX-Reswap": "none"})
    
@htmx.route("/admin/partials/schedule/new-form-open")
def new_schedule_form_open():
    return NewScheduleForm().panel().dump()

@htmx.route("/admin/partials/schedule/conflict-check")
def schedule_conflict_check():
    channel = request.args.get("channel")
    date_time = request.args.get("datetime")
    program_type = request.args.get("programType")

    if not all([channel, date_time]):
        return ""
    
    start = datetime.fromisoformat(date_time)
    conflict = tv_db.get_schedule_conflict(channel, start)

    if conflict:
        return "Conflict!"
    
    if program_type == "series":
        programs = tv_db.get_series()
    else:
        programs = tv_db.get_movies()

    return NewScheduleForm().program_dropdown(programs, "/admin/partials/schedule/new-fields").dump()

    
@htmx.route("/admin/partials/schedule/new-fields")
def new_schedule_fields():
    program_id = request.args.get("program_id")
    program_type = request.args.get("programType")

    if program_type == "series":
        program = tv_db.get_episodes(series_id=program_id)
    else:
        program = tv_db.get_movies(movie_id=program_id)

    return NewScheduleForm(program).form().dump()    

@htmx.route("/admin/partials/schedule/add/programs")
def add_schedule_programs():
    program_type = request.args.get("programType", "series")
    
    if program_type == "series":
        programs = tv_db.get_series()
    else:
        programs = tv_db.get_movies()
    
    return NewScheduleForm()._programs(programs).dump()
    

#TMDB
@htmx.route("/admin/partials/tmdb-fetch/series")
def tmdb_fetch_series():
    tmdb_id = request.args.get("tmdb_id")
    episode = request.args.get("episode")

    if not tmdb_id:
        return Response(status=204, headers={"HX-Reswap": "none"})
    
    if episode:
        #TODO: Include for episodes
        pass

    data = metadata_fetcher.get_tmdb_series_data(tmdb_id=int(tmdb_id))
    program = metadata_fetcher.extract_series_info_from_tmdb(data)
    return SeriesForm(program).form().dump()

@htmx.route("/admin/partials/tmdb-fetch/movie")
def tmdb_fetch_movie():
    tmdb_id = request.args.get("tmdb_id")

    if not tmdb_id:
        return Response(status=204, headers={"HX-Reswap": "none"})
    
    data = metadata_fetcher.get_tmdb_movie_data(tmdb_id=int(tmdb_id))
    program = metadata_fetcher.extract_movie_info_from_tmdb(data)
    return MovieForm(program).form().dump()
