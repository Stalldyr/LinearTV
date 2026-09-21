from .mediapathmanager import MediaPathManager
from .metadatafetcher import MetaDataFetcher
from .tvconstants import TYPE_MOVIES, TYPE_SERIES
from .tvdatabase import Movie, TVDatabase, Episode


class MetadataEnricher:
    """
    Fetches metadata for a single program and saves it to the database.

    Shared by TVPreparer (batch) and ProgramManager (manual additions).
    Methods raise on failure; the caller decides how to handle it.
    """

    def __init__(self):
        self.paths = MediaPathManager()
        self.metadata = MetaDataFetcher()
        self.database = TVDatabase()

    def enrich_ytdlp_episode_metadata(self, url, slug, series_id, episode_id):
        json_path = self.paths.get_metadata_path(
            TYPE_SERIES,
            slug,
            self.paths.create_ytdlp_episode_json_name(series_id, episode_id)
        )

        episode_data = self.metadata.get_ytdlp_data(url, json_path=json_path)
        relevant_data = self.metadata.extract_episode_info_from_ytdlp(episode_data)

        self.database.upsert(Episode(id=episode_id, **relevant_data.model_dump()))

        if relevant_data.duration:
            self.database.bulk_update_schedule(episode_id, relevant_data.duration)

    def enrich_tmdb_episode_metadata(self, slug, tmdb_id, series_id, episode_id):
        json_path = self.paths.get_metadata_path(
            TYPE_SERIES, 
            slug, 
            self.paths.create_tmbd_episode_json_name(tmdb_id, series_id, episode_id)
        )

        episode_data = self.metadata.get_tmdb_episode_data(tmdb_id=tmdb_id, json_path = json_path)
        relevant_data = self.metadata.extract_episode_info_from_tmdb(episode_data)

        self.database.upsert(Episode(id=episode_id,**relevant_data.model_dump()))

        if relevant_data.duration:
            self.database.bulk_update_schedule(episode_id, relevant_data.duration)

    def enrich_ytdlp_movie_metadata(self, url, slug, movie_id):
        json_path = self.paths.get_metadata_path(
            TYPE_MOVIES, 
            slug, 
            self.paths.create_ytdlp_movie_json_name(movie_id)
        )

        movie_data = self.metadata.get_ytdlp_data(url, json_path = json_path)
        relevant_data = self.metadata.extract_movie_info_from_ytdlp(movie_data)

        self.database.upsert(Movie(id=movie_id,**relevant_data.model_dump()))

        if relevant_data.duration:
            self.database.bulk_update_schedule(movie_id, relevant_data.duration)