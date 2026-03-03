
from typing import Type, TypeVar, Optional
from pydantic import BaseModel, ConfigDict, Field

class SeriesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    genre: Optional[str] = None
    release: Optional[str] = None
    reverse_order: bool = False
    start_season: int = 1
    start_episode: int = 1
    source_url: Optional[str] = None
    tmdb_id: Optional[int] = None

class MovieInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    genre: Optional[str] = None
    release: Optional[str] = None
    source_url: Optional[str] = None
    tmdb_id: Optional[int] = None
    duration: Optional[float] = None

class EpisodeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[int] = None
    series_id: int
    title: str
    description: Optional[str] = None
    release: Optional[str] = None
    season_number: Optional[int] = 1
    episode_number: Optional[int] = 1
    source_url: Optional[str] = None
    tmdb_id: Optional[int] = None
    duration: Optional[float] = None

class ScheduleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    genre: Optional[str] = None
    release: Optional[str] = None
    reverse_order: bool = False
    source_url: Optional[str] = None
    tmdb_id: Optional[int] = None