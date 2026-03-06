
from typing import Type, TypeVar, Optional
from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator
from datetime import datetime, time, date



class NRKInput(BaseModel):
    program_id: str = Field(alias="programId")
    series_id: str | None = Field(alias="seriesId")

    episode_title: str = Field(alias="title")
    series_title: str | None = Field(alias="seriesTitle")

    planned_start: datetime = Field(alias="plannedStart")
    actual_start: datetime | None = Field(alias="actualStart")
    rerun: bool = Field(alias="reRun")
    duration: int
    description: str | None
    category_id: int | None = Field(alias="category.id")
    category_display_value: str | None = Field(alias="category.displayValue")
    status: str







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
    release: str | None
    reverse_order: bool = False
    start_season: int = 1
    start_episode: int = 1
    source_url: str | None
    tmdb_id: int | None

class MovieInput(HTMLFormModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = Field(alias="program_id")
    title: str
    description: str | None
    genre: str | None
    release: str | None
    source_url: str | None
    tmdb_id: int | None
    duration: float | None

class EpisodeInput(HTMLFormModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None
    series_id: int | None
    title: str
    description: str | None
    release: str | datetime | None
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
    release: datetime | None
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
    keep_next_week: bool

    episode: EpisodeOutput | None
    movie: MovieOutput | None


