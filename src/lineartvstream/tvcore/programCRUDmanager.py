from lineartvstream.tvcore.tvdatabase import Channels, TVDatabase, Series, Episode, Movie, Schedule, Genres
from lineartvstream.tvcore.metadatafetcher import MetaDataFetcher
from lineartvstream.tvcore.tvconstants import *
from slugify import slugify
from hypermedia import *
from lineartvstream.tvcore.schemas import MovieInput, SeriesInput, EpisodeInput, ScheduleInput
import logging
from pydantic_core import ValidationError

class ProgramManager:
    """
    Works as a manager between flask/front-end and the database
    """
    def __init__(self):
        self.db = TVDatabase()
        self.metadatafetcher = MetaDataFetcher()

    # ============ CRUD OPERATIONS ============

    def update_series(self, data: dict):
        """
        Handle the complete workflow of adding or updating a program.

        Returns:
            tuple: (success: bool, message: str, status_code: int)
        """
        try:
            series = SeriesInput(**data)
        except ValidationError as e:
            logging.error("Validation failed:\n%s", e)
            return False, "Invalid data", 400

        try:
            self.db.upsert(
                Series(
                    **series.model_dump(),
                    slug=slugify(series.title)
                )
            )
            return True, "Program saved successfully", 200

        except Exception as e:
            logging.error(f"Error while saving: {e}")
            return False, "Database error", 500

    def delete_series(self, series_id):
        try:
            self.db.delete(
                Series(id=series_id)
            )

            episodes = self.db.get_episodes(series_id=series_id)
            self.db.delete_bulk(episodes)

            # TODO: Should also delete relevant files

            return True, "Program deleted successfully", 200

        except Exception as e:
            logging.error(f"Error while deleting: {e}")
            return False, "Database error", 500

    def update_movie(self, data: dict):
        """
        Handle the complete workflow of adding or updating a program.

        Returns:
            tuple: (success: bool, message: str, status_code: int)
        """
        try:
            movie = MovieInput(**data)
        except ValidationError as e:
            logging.error("Validation failed:\n%s", e)
            return False, "Invalid data", 400

        try:
            self.db.upsert(
                Movie(
                    **movie.model_dump(),
                    slug=slugify(movie.title)
                )
            )
            return True, "Program saved successfully", 200

        except Exception as e:
            logging.error(f"Error while saving: {e}")
            return False, "Database error", 500

    def delete_movie(self, movie_id):
        try:
            deleted = self.db.delete(
                Movie(id=movie_id)
            )

            # TODO: Should also delete relevant files

            if not deleted:
                return False, "Movie not found", 404

            return True, "Program deleted successfully", 200

        except Exception as e:
            logging.error(f"Error while deleting: {e}")
            return False, "Database error", 500

    def update_episode(self, data: dict):
        """
        Returns:
            tuple: (success: bool, message: str, status_code: int)
        """
        try:
            episode = EpisodeInput(**data)
        except ValidationError as e:
            logging.error("Validation failed:\n%s", e)
            return False, "Invalid data", 400

        try:
            self.db.upsert(
                Episode(
                    **episode.model_dump()
                )
            )
            return True, "Episode saved successfully", 200

        except Exception as e:
            logging.error(f"Error while saving: {e}")
            return False, "Database error", 500

    def delete_episode(self, episode_id):
        try:
            self.db.delete(
                Episode(id=episode_id)
            )

            # TODO: Should also delete relevant files

            return True, "Program deleted successfully", 200

        except Exception as e:
            logging.error(f"Error while deleting: {e}")
            return False, "Database error", 500

    # Schedule

    def update_schedule(self, data: dict):
        """
        Save (create or update) an entry in the weekly schedule.
        """

        try:
            schedule = ScheduleInput(**data, )
        except ValidationError as e:
            logging.error("Validation failed:\n%s", e)
            return False, e.errors(), 400

        conflict = self.db.get_schedule_conflict(schedule.channel, schedule.start, schedule.end)

        if conflict:
            print("Conflict?")
            return False, "Conflict!"

        try:
            self.db.upsert(
                Schedule(
                    **schedule.model_dump(exclude={"date", "time"})
                )
            )
            return True, "Schedule saved successfully", 200

        except Exception as e:
            logging.error(f"Error while saving: {e}")
            return False, "Database error", 500

    def delete_schedule(self, schedule_id):
        try:
            self.db.delete(
                Schedule(id=schedule_id)
            )
            return True, "Schedule entry deleted successfully", 200

        except Exception as e:
            logging.error(f"Error while deleting: {e}")
            return False, "Database error", 500

    def update_channels(self, data: dict):
        """
        Save (create or update) a channel.
        """
        try:
            self.db.upsert(
                Channels(
                    **data
                )
            )
            return True, "Channel saved successfully", 200

        except Exception as e:
            logging.error(f"Error while saving: {e}")
            return False, "Database error", 500

    def update_genres(self, data: dict):
        """
        Save (create or update) a genre.
        """
        try:
            self.db.upsert(
                Genres(
                    **data
                )
            )
            return True, "Channel saved successfully", 200

        except Exception as e:
            logging.error(f"Error while saving: {e}")
            return False, "Database error", 500

    def add_season(self, data:dict):
        metadata = self.metadatafetcher.get_ytdlp_data(data["source_url"])

