try:
    from .tvconstants import *
except:
    from tvconstants import *

import logging
from unittest import result
from sqlalchemy import Column, Integer, String, Boolean, Float, Date, Time, DateTime, ForeignKey, Text, JSON, create_engine, and_, or_, case, func, desc, text, inspect
from sqlalchemy.orm import relationship, sessionmaker, Session, DeclarativeBase, joinedload
from sqlalchemy.sql import select, update, delete, exists, not_
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Row
from sqlalchemy.ext.declarative import DeclarativeMeta
from pathlib import Path
from datetime import date, datetime
from typing import Optional, List, Dict
from pydantic_core import ValidationError
from types import SimpleNamespace
import json

from .tvconstants import *
from .schemas import ScheduleOutput, SeriesOutput, EpisodeOutput, MovieOutput
from .metadatafetcher import MetaDataFetcher

class Base(DeclarativeBase):
    pass

class MediaBase(Base):
    __abstract__ = True

    #ID's    
    id = Column(Integer, primary_key=True)
    tmdb_id = Column(Integer, unique=True)

    #Metadata
    title = Column(Text, nullable=False)
    description = Column(Text)
    genre = Column(Text)
    release = Column(DateTime)

    slug = Column(Text)

    source_url = Column(Text)

class Series(MediaBase):
    __tablename__ = 'series'

    #User Input
    reverse_order = Column(Boolean, default=False)
    start_season = Column(Integer, default=1)
    start_episode = Column(Integer, default=1)

    # Relationships
    episodes = relationship("Episode", back_populates="series", cascade="all, delete-orphan")

class Movie(MediaBase):
    __tablename__ = 'movies'

    program_id = Column(Text, unique=True)
    duration = Column(Float)
    
    # Relationships
    schedule_entries = relationship("Schedule", back_populates="movie")

class Episode(Base):
    __tablename__ = 'episodes'

    #ID's
    id = Column(Integer, primary_key=True)
    series_id = Column(Integer, ForeignKey('series.id'), nullable=False)
    program_id = Column(Text, unique=True)
    tmdb_id = Column(Integer, unique=True)

    #Metadata
    title = Column(Text)
    season_number = Column(Integer)
    episode_number = Column(Integer)
    description = Column(Text)
    duration = Column(Float)
    source_url = Column(Text)

    # Relationships
    series = relationship("Series", back_populates="episodes", lazy="selectin")
    schedule_entries = relationship("Schedule", back_populates="episode")

class Schedule(Base):
    __tablename__ = 'schedule'

    #ID's    
    id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, ForeignKey('episodes.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))

    title = Column(Text, nullable=False)

    #schedule info
    original_start = Column(DateTime)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    rerun = Column(Boolean, default=False, nullable=False)
    channel = Column(Text)
    
    filepath = Column(Text)
    download_date = Column(Date)
    file_size = Column(Integer)
    status = Column(Text, default='pending', nullable=False)
    last_aired = Column(Date)
    views = Column(Integer)
    
    # Relationships
    episode = relationship("Episode", back_populates="schedule_entries", lazy="selectin")
    movie = relationship("Movie", back_populates="schedule_entries", lazy="selectin")

    @property
    def json(self):
        return self.to_json(self, self.__class__)
    
class TVDatabase:
    def __init__(self, test_time=None, db_path=""):
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path(__file__).parent.parent.absolute() / "data" / "tv.db"
        
        self.test_time = test_time
        
        # Create engine and session factory
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        self.metadatafetcher = MetaDataFetcher()

        #self.sql = SQLexecute(self.db_path)
        #self.execute_query = self.sql.execute_query
        
        # Setup database if it doesn't exist
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.setup_database()
    
    def get_session(self) -> Session:
        """Create and return a new database session"""
        return self.SessionLocal()
    
    # SETUP
    
    def setup_database(self):
        """Sets up database tables if they don't already exist."""
        Base.metadata.create_all(self.engine)
    
    def reset_database(self):
        """
        Reset the database to its initial state while preserving schedule data.
        
        This method clears episode-specific metadata by:
        - Removing file information (file_size, filename)
        - Clearing download and air date information (download_date, last_aired)
        - Resetting episode status to 'pending'
        - Resetting view count to 0
        - Removing keep flags (keep_next_week)
        - Disassociating episodes from the weekly schedule
        """
        with self.get_session() as session:
            session.query(Schedule).update({
                Schedule.file_size: None,
                Schedule.filepath: None,
                Schedule.download_date: None,
                Schedule.status: "pending",
                Schedule.last_aired: None,
                Schedule.views: 0,
                Schedule.keep_next_week: False
            })
            
            session.commit()


    #GENERAL CRUD OPERATIONS

    def _to_model(self, obj: Series | Movie | Schedule | Episode) -> tuple[type, dict]:
        model = type(obj)
        data = {k: v for k, v in obj.__dict__.items() if not k.startswith('_') and v is not None}
        
        return model, data
    
    def _execute(self, query, model: ScheduleOutput| SeriesOutput | EpisodeOutput | MovieOutput ):
        with self.get_session() as session:
            try:
                results = session.execute(query).scalars().all()
            except Exception as e:
                logging.error(f"Database query failed: {e}")
                return []

            validated = []
            for row in results:
                try:
                    validated.append(model.model_validate(row))
                except ValidationError as e:
                    logging.warning(f"Skipping invalid row {getattr(row, 'id', '?')}: {e}")
                except Exception as e:
                    logging.error(f"Unexpected error validating row: {e}")

            return validated
            

    def get(self, obj: Series | Movie | Schedule | Episode) -> Series | Movie | Schedule | Episode:
        with self.get_session() as session:

            model, data = self._to_model
            stmt = select(model)
            for key, value in data.items():
                stmt = stmt.where(getattr(model, key) == value)


            stmt = self._to_model(obj)
            return session.execute(stmt).scalars().first()

    def add(self, obj: Series | Movie | Schedule | Episode, unique_on: list[str] = None):
        """Adds new entry to the weekly schedule"""

        with self.get_session() as session:
            if unique_on:
                model = type(obj)
                conditions = [getattr(model, col) == getattr(obj, col) for col in unique_on]
                exists = session.execute(select(model).where(*conditions)).scalars().first()
                if exists:
                    return exists.id

            session.add(obj)
            session.commit()
            session.refresh(obj)

            return obj.id
    
    def update(self, obj):
        with self.get_session() as session:
            #stmt = update(obj).where(Schedule.channel == "Nrk1").values(channel = "nrk1")
            #session.execute(stmt)
            session.commit()
        
    def upsert(self, obj: Series | Movie | Schedule):
        """Adds or updates an entry in the database based on the presence of a primary ID."""
        with self.get_session() as session:
            session.merge(obj)
            session.commit()

    def upsert_on_column(self, obj: Series | Movie | Schedule, index_elements):
        """Adds or updates an entry in the database based on the presence of a primary ID."""
        with self.get_session() as session:
            model, data = self._to_model(obj)
            update_dict = {col: getattr(stmt.excluded, col) for col in data.keys() if col not in index_elements}

            stmt = insert(model).values(**data)
            stmt = stmt.on_conflict_do_update(index_elements=index_elements, set_=update_dict)
            session.execute(stmt)
            session.commit()

    def delete(self, obj: Series | Movie | Schedule | Episode):
        """
        Deletes an entry from any table 
        
        Args:
            obj: ---- 
        
        Returns:
            True if successful, False otherwise
        """
        with self.get_session() as session:
            db_obj  = session.get(type(obj), obj.id)
            if db_obj :
                session.delete(db_obj)
                session.commit()

                return True
            return False
        

    def delete2(self, obj: Series | Movie | Schedule | Episode):
        """
        Deletes an entry from any table 
        
        Args:
            obj: ---- 
        
        Returns:
            True if successful, False otherwise
        """
        with self.get_session() as session:
            model, data = self._to_model(obj)
            stmt = delete(model).where(model.id == obj.id)
            session.execute(stmt)
            session.commit()
    

    # MEDIA CRUD OPERATIONS
        
    
    def get_all_series(self, missing=False) -> List[SeriesOutput]:
        """Returns all series from the series-table."""
        q = select(
            Series
        ).order_by(
            Series.title
        )

        if missing:
            q = q.where(or_(Series.description, Series.title, Series.release).is_(None))

        return self._execute(q, SeriesOutput)
        
    def get_all_episodes(self, missing=False) -> List[EpisodeOutput]:
        """Returns all series from the series-table."""
        
        q = select(
            Episode
        ).order_by(
            Episode.id
        )

        if missing:
            q = q.where(or_(
                Episode.title.is_(None),
                Episode.description.is_(None),
                Episode.season_number.is_(None),
                Episode.episode_number.is_(None),
                Episode.duration.is_(None)
            ))

        return self._execute(q, EpisodeOutput)
    
    def get_all_movies(self, missing=False) -> List[MovieOutput]:
        """Returns all series from the series-table."""
        q = select(
            Movie
        ).order_by(
            Movie.title
        )

        if missing:
            q = q.where(or_(
                Movie.description, 
                Movie.title,
                Movie.release,
                Movie.genre
            ).is_(None)
        )

        return self._execute(q, MovieOutput)
    
    # SCHEDULE OPERATIONS
                
    def get_scheduled_programs(self, date: datetime = None) -> List[ScheduleOutput]:
        q = select(
            Schedule
        )

        if date:
            q = q.where(func.date(Schedule.start) == date)

        return self._execute(q, ScheduleOutput)
        
    def get_pending_programs(self, strict: bool = False, date: date = None) -> List[ScheduleOutput]:
        """
        Return pending episodes from the episodes table.
        
        Args:
            strict: Whether status is strictly "pending" or have other non-available statuses
            local: Whether to filter for local programs only
            schedule: Whether to return pending episodes only from programs in the weekly schedule
        """
        
        q = select(
            Schedule
        )
        
        if strict:
            q = q.where(Schedule.status == STATUS_PENDING)
        else:
            q = q.where(Schedule.status.in_([
                STATUS_PENDING, STATUS_FAILED, STATUS_MISSING, 
                STATUS_DOWNLOADING, STATUS_DELETED
            ]))

        if date:
            q = q.where(func.date(Schedule.start) == date)

        return self._execute(q, ScheduleOutput)      
            
    def get_obsolete_programs(self) -> list[ScheduleOutput]:
        return self.get_obsolete_episodes() + self.get_obsolete_movies()

    def get_obsolete_episodes(self) -> list[ScheduleOutput]:
        """Returns available episodes that has already been viewed and is not planned to be viewes again."""
        return self._obsolete_filter(Schedule.episode_id)

    def get_obsolete_movies(self) -> list[ScheduleOutput]:
        """Returns available movies that has already been viewed and is not planned to be viewes again."""
        return self._obsolete_filter(Schedule.movie_id)

    def _obsolete_filter(self, id_column: Column[int]):
        future_episode_ids = (
            select(id_column)
            .where(
                Schedule.start > datetime.now(),
                id_column.isnot(None)
            )
            .scalar_subquery()
        )

        q = (
            select(Schedule)
            .where(
                Schedule.start < datetime.now(),
                Schedule.filepath.isnot(None),
                id_column.not_in(future_episode_ids)
            )
        )

        return self._execute(q, ScheduleOutput)           

    def get_episode_by_details(self, series_id: int, season: int, episode: int) -> Optional[Dict]:
        """
        Returns episode from the "episode" table filtered by series_id, season and episode number
        """
        with self.get_session() as session:
            ep = session.query(Episode).filter(
                Episode.series_id == series_id,
                Episode.season_number == season,
                Episode.episode_number == episode
            ).first()
            
            return self._to_dict(ep) if ep else None
        
        
    def get_current_week_schedule(self) -> List[ScheduleOutput]:
        """Returns all scheduled programs in the current week"""
        year, week, day = datetime.today().isocalendar()
        start = datetime.fromisocalendar(year, week, 1)
        end = datetime.fromisocalendar(year, week, 7)


        q = select(
                Schedule
            ).where(
                Schedule.start.between(start,end)
            ).order_by(
                Schedule.start
        )
        
        return self._execute(q, ScheduleOutput)
            
    def get_schedule(self) -> List[ScheduleOutput]:
        """Get all series that are in the weekly schedule"""
        q = select(
            Schedule
        ).order_by(
            Schedule.start
        )
        
        return self._execute(q, ScheduleOutput)
    
    def get_current_program_by_channel(self, channel: str, time=None) -> list[dict]:
        if time is None:
            time = datetime.now()

        with self.get_session() as session:
            #channels = session.execute(select(Schedule.channel).distinct()).scalars().all()

            #print(channels)

            q = select(
                Schedule.id,
                Schedule.channel,
                Schedule.start,
                Schedule.end,
                Schedule.filepath,
                Schedule.rerun,
                Schedule.status,
                Schedule.title,
                func.coalesce(Episode.description, Movie.description).label("description"),
                func.coalesce(Episode.duration, Movie.duration).label("duration")
            ).where(
                Schedule.start <= time,
                Schedule.end >= time,
                Schedule.status == STATUS_AVAILABLE,
                Schedule.channel == channel
            ).outerjoin(
                Episode
            ).outerjoin(
                Movie
            ).order_by(
                Schedule.channel,
                Schedule.start
            )

            result = session.execute(q).mappings().first()
            if result:
                return dict(result)
            else:
                return None
            
    def get_next_programs(self, time=None) -> list[dict]:
        if time is None:
            time = datetime.now()

        with self.get_session() as session:
            q = select(
                Schedule.id,
                Schedule.channel,
                Schedule.start,
                Schedule.end,
                Schedule.filepath,
                Schedule.rerun,
                Schedule.status,
                Schedule.title,
                func.coalesce(Episode.description, Movie.description).label("description"),
                func.coalesce(Episode.duration, Movie.duration).label("duration")
            ).where(
                Schedule.start >= time,
                Schedule.status == STATUS_AVAILABLE
            ).outerjoin(
                Episode
            ).outerjoin(
                Movie
            ).order_by(
                Schedule.channel,
                Schedule.start
            ).group_by(
                Schedule.channel
            )
        
            return self._to_dict(session.execute(q).all())

            
    # AIRING OPERATIONS

    def get_air_schedule(self) -> List[ScheduleOutput]:
        q = select(Schedule).options(
            joinedload(Schedule.movie),
            joinedload(Schedule.episode).joinedload(Episode.series)
        )

        return self._execute(q, ScheduleOutput)
    
    # UTILITY METHODS
    
    @staticmethod
    def _to_dict(obj) -> Dict:
        """Convert SQLAlchemy model instance to dictionary"""
        if obj is None:
            return None
        
        result = {}
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)
            # Convert date/time objects to strings for consistency
            if isinstance(value, (datetime, )):
                value = value.isoformat()
            result[column.name] = value
        return result
        
class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # Convert SQLAlchemy model to dictionary
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data)
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            return fields
        return json.JSONEncoder.default(self, obj)

class Serializer(object):

    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(l):
        return [m.serialize() for m in l]


def to_json(inst, cls):
    """
    Jsonify the sql alchemy query result.
    """
    convert = dict()
    # add your coversions for things like datetime's 
    # and what-not that aren't serializable.
    d = dict()
    for c in cls.__table__.columns:
        v = getattr(inst, c.name)
        if c.type in convert.keys() and v is not None:
            try:
                d[c.name] = convert[c.type](v)
            except:
                d[c.name] = "Error:  Failed to covert using ", str(convert[c.type])
        elif v is None:
            d[c.name] = str()
        else:
            d[c.name] = v
    return json.dumps(d)