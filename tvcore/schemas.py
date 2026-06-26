
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, AliasChoices
from datetime import datetime, time, date, timedelta
import json
import isodate
from pathlib import Path
from .helper import parse_aspnet_date, same_iso_week_this_year
import math

from typing import Literal
Channel = Literal["nrk1", "nrk2"]

class NRKInputCategory(BaseModel):
    display_value: str = Field(alias="displayValue")

class NRKInputStatus(BaseModel):
    status: str

class NRKInput(BaseModel):
    program_id: str = Field(alias="programId")
    series_id: str | None = Field(alias="seriesId")

    title: str = Field(alias="title")
    series_title: str | None = Field(alias="seriesTitle")

    original_start: datetime = Field(alias="plannedStart")
    start: datetime = None
    end: datetime = None
    rerun: bool = Field(alias="reRun")

    duration: float
    description: str | None
    category: NRKInputCategory
    availability: NRKInputStatus

    channel: Channel = None

    source_url: str | None = None


    @field_validator("original_start", mode="before")
    @classmethod
    def parse_aspnet_date(cls, v):
        if isinstance(v, str):
            return parse_aspnet_date(v)
        return v
        
    @field_validator("duration", mode="before")
    @classmethod
    def parse_duration(cls, v):
        if isinstance(v, str):
            return isodate.parse_duration(v).total_seconds()
        return v
    
    @model_validator(mode="after")
    def _(self):
        self.start = same_iso_week_this_year(self.original_start)
        self.end = self.start + timedelta(minutes=math.ceil(self.duration/60))

        if self.series_id:
            self.source_url = f"https://tv.nrk.no/serie/{self.series_id}/{self.program_id}"
        else:
            self.source_url = f"https://tv.nrk.no/program/{self.program_id}"

        return self
    

    

class HTMLFormModel(BaseModel):
    """Base class for all HTML form models — treats empty strings as None."""

    @field_validator("*", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

class SeriesInput(HTMLFormModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = Field(alias="program_id")
    title: str
    description: str | None
    genre: str | None
    release: date | None
    reverse_order: bool = False
    start_season: int | None = Field(default=1) 
    start_episode: int | None = Field(default=1)
    tmdb_id: int | None

class MovieInput(HTMLFormModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = Field(alias="program_id")
    title: str
    description: str | None
    genre: str | None
    release: str | date | None
    source_url: str | None
    tmdb_id: int | None
    duration: float | None

class EpisodeInput(HTMLFormModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = Field(None, alias="episode_id")
    series_id: int | None
    program_id: str | None
    title: str
    description: str | None
    season_number: int | None
    episode_number: int | None
    source_url: str | None
    tmdb_id: int | None
    duration: float | int | None

class ScheduleInput(HTMLFormModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = Field(None, alias="schedule_id")
    episode_id: int | None
    movie_id: int | None
    title: str 
    start: datetime | None
    end: datetime | None
    rerun: bool
    channel: str

class ScheduleUpdate(HTMLFormModel):
    id: int = Field(alias="schedule_id")
    title: str
    date: date
    time: time
    channel: str
    rerun: bool = False
    start: datetime = None

    @model_validator(mode="after")
    def combine_date_and_time(self):
        self.start = datetime.combine(self.date, self.time)
        return self

class SeriesOutput(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    description: str | None
    genre: str | None
    release: date | None
    reverse_order: bool
    start_season: int | None
    start_episode: int | None
    source_url: str | None
    tmdb_id: int | None
    slug: str | None

class EpisodeOutput(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    program_id: str
    series_id: int
    title: str | None
    description: str | None
    #release: datetime | None
    season_number: int | None
    episode_number: int | None
    source_url: str | None
    tmdb_id: int | None
    duration: float | None

    series: SeriesOutput | None

class MovieOutput(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    program_id: str | None

    title: str
    description: str | None
    genre: str | None
    release: datetime | None
    source_url: str | None
    tmdb_id: int | None
    duration: float | None
    slug: str | None

class ScheduleOutput(BaseModel):
    model_config = {"from_attributes": True}

    #ID's    
    id: int
    episode_id: int | None
    movie_id: int | None

    title: str | None

    #schedule info
    original_start: datetime | None
    start: datetime
    end: datetime | None
    rerun: bool
    channel: str
    
    filepath: str | None
    download_date: date | None
    file_size: int | None
    status: str
    last_aired: datetime | None
    views: int | None

    episode: EpisodeOutput | None
    movie: MovieOutput | None


class YTDLPInput(BaseModel):
    program_id: str | None = Field(None, alias="id")
    season_number: int | None = Field(None)
    episode_number: int | None = Field(None, validation_alias = AliasChoices("episode_number", "playlist_index"))
    title: str | None
    #"series_title": episode_data.get("series"),
    description: str | None
    duration: float | int | None
    source_url: str | None = Field(alias="webpage_url")

class TMDBEpisodeInput(BaseModel):
    tmdb_id: int | None = Field(None, alias="id")
    season_number: int | None = Field(None)
    episode_number: int | None = Field(None)
    title: str | None = Field(None, alias="name")
    #"series_title": episode_data.get("series"),
    description: str | None = Field(None, alias="overview")
    duration: float | int | None = Field(None, alias="runtime")

class TMDBSeriesInput(BaseModel):
    title: str | None = Field(None, alias="name")
    tmdb_id: str | int | None = Field(None, alias="id")
    release: str | None = Field(None,  alias="first_air_date")
    description: str | None = Field(None, alias="overview")
    genre: str | None = Field(None, alias="genres")

    @field_validator("genre", mode="before")
    @classmethod
    def extract_genre_name(cls, v):
        if isinstance(v, list) and v:
            return v[0].get("name")
        return v

class TMDBMovieInput(BaseModel):
    tmdb_id: int | None = Field(None, alias="id")
    title: str | None = None
    description: str | None = Field(None, alias="overview")
    duration: float | int | None = Field(None, alias="runtime")
    release: str | None = Field(None, alias="release_date")
    genre: str | None = Field(None, alias="genres")
    original_language: str | None

    @field_validator("genre", mode="before")
    @classmethod
    def extract_genre_name(cls, v):
        if isinstance(v, list) and v:
            return v[0].get("name")
        return v



class MetadataInput(TMDBEpisodeInput, TMDBSeriesInput, TMDBMovieInput, YTDLPInput):
    pass


class ScheduleConfig(BaseModel):
    broadcast_start: time
    broadcast_end: time
    broadcast_steps: int

class PathsConfig(BaseModel):
    download_path: str | Path
    series_path: str | Path
    movies_path: str | Path

class UpdateConfig(BaseModel):
    frequency: str

class VideoConfig(BaseModel):
    quality: str | int

class TVConfig(BaseModel):
    language: str = "en"
    schedule: ScheduleConfig
    paths: PathsConfig
    updates: UpdateConfig
    video: VideoConfig
    genres: list[str]
    
    @classmethod
    def from_file(cls, path: str | Path = "") -> "TVConfig":
        if not path:
            path = Path(__file__).parent.parent.absolute()/"config.json"
        
        with open(path) as f:
            return cls(**json.load(f))