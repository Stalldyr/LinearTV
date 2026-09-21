from datetime import datetime, timedelta
from functools import wraps
from lineartvstream.tvcore.filehandler import TVFileHandler
from lineartvstream.tvcore.tvdatabase import Channels, TVDatabase, Series, Episode, Movie, Schedule, Genres
from lineartvstream.tvcore.metadatafetcher import MetaDataFetcher
from lineartvstream.tvcore.tvconstants import *
from slugify import slugify
from hypermedia import *
from lineartvstream.tvcore.schemas import MovieInput, SeriesInput, EpisodeInput, ScheduleInput
import logging
from pydantic_core import ValidationError


def db_operation(success_message: str = "Saved successfully"):
    """
    Decorator that wraps a database operation in standard try/except
    handling, returning (success: bool, message: str, status_code: int).

    If the wrapped function returns a value itself (e.g. to signal a
    specific failure like "not found"), that return value is used as-is.
    Otherwise, a successful call (no exception, no return value) yields
    (True, success_message, 200).
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if result is not None:
                    return result
                return success_message, 200
            except Exception as e:
                logging.error(f"Error while saving: {e}")
                return "Database error", 500
        return wrapper
    return decorator


def _validate_input(data: dict, model_class):
    """
    Validate input data against a Pydantic model.

    Returns:
        tuple: (success: bool, validated_model: BaseModel or None, error_message: str or None)
    """
    try:
        validated_model = model_class(**data)
        return validated_model, None
    except ValidationError as e:
        logging.error("Validation failed:\n%s", e)
        return None, "Invalid data"


class ProgramManager:
    """
    Works as a manager between flask/front-end and the database
    """
    def __init__(self):
        self.db = TVDatabase()
        self.metadatafetcher = MetaDataFetcher()
        self.filehandler = TVFileHandler()

    # ============ SERIES ============

    def update_series(self, data: dict):
        validated, error = _validate_input(data, SeriesInput)
        if error:
            return error, 400

        return self._save_series(validated)

    @db_operation("Program saved successfully")
    def _save_series(self, validated):
        self.db.upsert(
            Series(**validated.model_dump(), slug=slugify(validated.title))
        )

    @db_operation("Program deleted successfully")
    def delete_series(self, series_id, slug):
        self.db.delete(Series(id=series_id))

        episodes = self.db.get_episodes(series_id=series_id)
        self.db.delete_bulk(episodes)

        self.filehandler.delete_series_directory(slug=slug)

    # ============ MOVIE ============

    def update_movie(self, data: dict):
        validated, error = _validate_input(data, MovieInput)
        if error:
            return error, 400

        return self._save_movie(validated)

    @db_operation("Program saved successfully")
    def _save_movie(self, validated):
        self.db.upsert(
            Movie(**validated.model_dump(), slug=slugify(validated.title))
        )

    @db_operation("Program deleted successfully")
    def delete_movie(self, movie):
        deleted = self.db.delete(Movie(id=movie.id))

        if not deleted:
            return "Movie not found", 404

        self.filehandler.delete_movie_files(movie)

    # ============ EPISODE ============

    def update_episode(self, data: dict):
        validated, error = _validate_input(data, EpisodeInput)
        if error:
            return error, 400

        return self._save_episode(validated)

    @db_operation("Episode saved successfully")
    def _save_episode(self, validated):
        self.db.upsert(Episode(**validated.model_dump()))

    @db_operation("Program deleted successfully")
    def delete_episode(self, episode):
        self.db.delete(Episode(id=episode.id))

        self.filehandler.delete_episode_files(episode)

    # ============ SCHEDULE ============

    def update_schedule(self, data: dict):
        validated, error = _validate_input(data, ScheduleInput)
        if error:
            return error, 400

        if validated.episode_id:
            episode = self.db.get_episodes(episode_id=validated.episode_id)
            if not episode:
                return "Episode not found", 404
            duration = episode.duration

        if validated.movie_id:
            movie = self.db.get_movies(movie_id=validated.movie_id)
            if not movie:
                return "Movie not found", 404
            duration = movie.duration

        validated.end = (validated.start + timedelta(seconds=duration)).replace(microsecond=0)

        conflict = self.db.get_schedule_conflict(validated.channel, validated.start, validated.end)
        if conflict:
            return "Conflict!", 409

        return self._save_schedule(validated)

    @db_operation("Schedule saved successfully")
    def _save_schedule(self, validated):
        self.db.upsert(
            Schedule(**validated.model_dump())
        )

    @db_operation("Schedule entry deleted successfully")
    def delete_schedule(self, schedule_id):
        self.db.delete(Schedule(id=schedule_id))

    # ============ CHANNELS ============

    @db_operation("Channel saved successfully")
    def update_channels(self, data: dict):
        self.db.upsert(Channels(**data))

    # ============ GENRES ============

    @db_operation("Genre saved successfully")
    def update_genres(self, data: dict):
        self.db.upsert(Genres(**data))

    # ============ SEASON ============

    def calculate_season_schedule(self, episodes: list, start: datetime) -> list[tuple]:
        """
        Given a sorted list of episodes and a start datetime for episode 1,
        returns a list of (episode, start, end) tuples — one per week.
        """
        result = []

        for index, episode in enumerate(episodes):
            episode_start = start + timedelta(weeks=index)
            episode_end = episode_start + timedelta(seconds=episode.duration)

            result.append((episode, episode_start, episode_end))

        return result

    def schedule_season(self, series_id: int, season_number: int, channel: str, start: datetime):
        episodes = self.db.get_episodes(series_id=series_id, season_number=season_number)

        if not episodes:
            return "No episodes found for this season", 404

        planned = self.calculate_season_schedule(episodes, start)

        results = []
        for episode, ep_start, ep_end in planned:
            conflict = self.db.get_schedule_conflict(channel, ep_start, ep_end)

            if conflict:
                results.append({
                    "episode_id": episode.episode_id,
                    "title": episode.title,
                    "status": "conflict",
                    "start": ep_start
                })
                continue

            self.db.upsert(
                Schedule(
                    episode_id=episode.episode_id,
                    title=episode.title,
                    channel=channel,
                    start=ep_start,
                    end=ep_end
                )
            )

            results.append({
                "episode_id": episode.episode_id,
                "title": episode.title,
                "status": "scheduled",
                "start": ep_start
            })

        return True, results, 200

    def add_season(self, series_id: int, season_number: int, source_url: str):
        metadata = self.metadatafetcher.get_ytdlp_data(source_url)
        entries = metadata.get("entries", [])

        if not entries:
            return "No episodes found", 404

        added = []
        for entry in entries:
            try:
                validated = self.metadatafetcher.extract_episode_info_from_ytdlp(entry)
            except ValidationError:
                continue

            episode_id = self.db.add(
                Episode(
                    series_id=series_id,
                    season_number=season_number,
                    episode_number=validated.episode_number,
                    title=validated.title,
                    description=validated.description,
                    duration=validated.duration,
                    program_id=validated.program_id,
                    source_url=validated.source_url
                ),
                unique_on=["program_id"]
            )

            added.append(episode_id)

        return f"{len(added)} episodes added", 200


    # ============ DATABASE ENRICHMENT ============

    def enrich_ytdlp_episode_metadata(self, url, slug, series_id, episode_id):
        json_path = self.paths.get_metadata_path(
            TYPE_SERIES, 
            slug, 
            self.paths.create_ytdlp_episode_json_name(series_id, episode_id)
        )

        episode_data = self.metadata.get_ytdlp_data(url, json_path = json_path)
        relevant_data = self.metadata.extract_episode_info_from_ytdlp(episode_data)

        self.database.upsert(Episode(id=episode_id,**relevant_data.model_dump()))

        if relevant_data.duration:
            self.database.bulk_update_schedule(episode_id,relevant_data.duration)