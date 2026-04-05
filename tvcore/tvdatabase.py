import logging
from sqlalchemy import Column, Integer, String, Boolean, Float, Date, Time, DateTime, ForeignKey, Text, JSON, create_engine, and_, or_, case, func, desc, text, inspect
from sqlalchemy.orm import relationship, sessionmaker, Session, DeclarativeBase, joinedload
from sqlalchemy.sql import select, update, delete, exists, not_
from sqlalchemy.dialects.sqlite import insert
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict
from pydantic_core import ValidationError
import math

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
    release = Column(Date)

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
    status = Column(Text, default=STATUS_PENDING, nullable=False)
    last_aired = Column(Date)
    views = Column(Integer)
    
    # Relationships
    episode = relationship("Episode", back_populates="schedule_entries", lazy="selectin")
    movie = relationship("Movie", back_populates="schedule_entries", lazy="selectin")
  
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
                Schedule.status: STATUS_PENDING,
                Schedule.last_aired: None,
                Schedule.views: 0
            })
            
            session.commit()


    #GENERAL CRUD OPERATIONS

    def _to_model(self, obj: Series | Movie | Schedule | Episode) -> tuple[type, dict]:
        model = type(obj)
        data = {k: v for k, v in obj.__dict__.items() if not k.startswith('_') and v is not None}
        
        return model, data
    
    def _execute(self, query, model: ScheduleOutput | SeriesOutput | EpisodeOutput | MovieOutput = None, first=False):
        with self.get_session() as session:
            try:
                if first:
                    return session.execute(query).scalars().first()
                results = session.execute(query).scalars().all()
            except Exception as e:
                logging.error(f"Database query failed: {e}")
                return []
            
            if model is None:
                return results

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
        
    
    def get_series(self, missing=False, series_id=None) -> List[SeriesOutput]:
        """Returns series from the series-table. Defaults to all"""
        q = select(
            Series
        ).order_by(
            Series.title
        )

        if missing:
            q = q.where(
                or_(
                    Series.description.is_(None), 
                    Series.title.is_(None), 
                    Series.release.is_(None)
                    )
                )

        if series_id:
            q = q.where(Series.id == series_id)
            return self._execute(q, SeriesOutput, first=True)

        return self._execute(q, SeriesOutput)
        
    def get_episodes(self, missing=False, episode_id=None, series_id=None) -> List[EpisodeOutput]:
        """Returns episodes from the series-table. Defaults to all"""
        
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

        if episode_id:
            q = q.where(Episode.id == episode_id)
            return self._execute(q, EpisodeOutput)

        if series_id:
            q = q.where(Episode.series_id == series_id)

        return self._execute(q, EpisodeOutput)
    
    def get_movies(self, missing=False, movie_id=None) -> List[MovieOutput]:
        """Returns movies from the movies-table. Defaults to all. """
        q = select(
            Movie
        ).order_by(
            Movie.title
        )

        if missing:
            q = q.where(or_(
                Movie.description.is_(None), 
                Movie.title.is_(None),
                Movie.release.is_(None),
                Movie.genre.is_(None)
            ))
        
        if movie_id:
            q = q.where(Movie.id == movie_id)
            return self._execute(q, MovieOutput, first=True)

        return self._execute(q, MovieOutput)
    
    # SCHEDULE OPERATIONS
                
    def get_scheduled_programs(self, date: datetime = None) -> List[ScheduleOutput]:
        q = select(
            Schedule
        )

        if date:
            q = q.where(func.date(Schedule.start) == date)

        return self._execute(q, ScheduleOutput)
        
    def get_pending_programs(self, strict:bool = False, date:date = None) -> List[ScheduleOutput]:
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
        
        
    def get_current_week_schedule(self, channel:str=None, date:datetime=None, full_week:bool=False) -> List[ScheduleOutput]:
        """Returns all scheduled programs in the current week"""
        offset = timedelta(hours=4) #Marks the end of the air day, to include programs that starts late at night and ends after midnight

        if not date:
            date = datetime.today()

        if full_week:
            year, week, _ = date.isocalendar()
            start = datetime.fromisocalendar(year, week, 1) + offset
            end = start + timedelta(days=7)
        else:
            start = date + offset
            end = start + timedelta(days=1)

        q = select(
                Schedule
                #func.coalesce(Episode.description, Movie.description).label("description")
            ).where(
                Schedule.start.between(start,end),
                Schedule.status.in_([STATUS_PENDING, STATUS_AVAILABLE, STATUS_DELETED])
            ).outerjoin(
                Episode
            ).outerjoin(
                Movie
            ).order_by(
                Schedule.start
            )

        if channel:
            q = q.where(Schedule.channel == channel)
        
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
                Schedule.start
            )

            result = session.execute(q).mappings().first()
            if result:
                return dict(result)
            else:
                return None
            
    def get_next_program_by_channel(self, channel:str, time:datetime=None, limit=1) -> list[dict]:
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
                Schedule.status == STATUS_AVAILABLE,
                Schedule.channel == channel
            ).outerjoin(
                Episode
            ).outerjoin(
                Movie
            ).order_by(
                Schedule.start
            )

            if limit:
                end_time = time + timedelta(days=1)
                q = q.where(Schedule.start < end_time)
        
            result = session.execute(q).mappings().first()
            if result:
                return dict(result)
            else:
                return None

            
    # AIRING OPERATIONS

    def get_air_schedule(self) -> List[ScheduleOutput]:
        q = select(Schedule).options(
            joinedload(Schedule.movie),
            joinedload(Schedule.episode).joinedload(Episode.series)
        )

        return self._execute(q, ScheduleOutput)
    
    def get_new_series_in_current_week(self):
        from .helper import get_iso_week_span

        now = datetime.now()

        start, end = get_iso_week_span(now)
        
        n = now - timedelta(days=7)
        s, e = get_iso_week_span(n-timedelta(weeks=3),n)


        with self.get_session() as session:

            q_in = select(
                    Series
                ).where(
                    Schedule.start.between(s, e)
                ).correlate()
            
            q = select(
                    Series
                ).where(
                    Schedule.start.between(start, end),
                    Series.id.in_(q_in)
                ).outerjoin(Episode).outerjoin(Schedule).distinct()
            
            return session.execute(q).scalars().all()
        
    def get_new_this_week(self, lookback_weeks: int = 3) -> list[ScheduleOutput]:
        """
        Returns programs that appear in this week's schedule but not in the
        previous `lookback_weeks` weeks. Includes both series and movies.
        """
        now = datetime.now()
        year, week, _ = now.isocalendar()

        current_start = datetime.fromisocalendar(year, week, 1)
        current_end = current_start + timedelta(weeks=1)

        lookback_end = current_start
        lookback_start = current_start - timedelta(weeks=lookback_weeks)

        with self.get_session() as session:

            def get_ids_in_period(start, end):
                q = select(
                    Episode.series_id,
                    Schedule.movie_id
                ).outerjoin(
                    Episode, Schedule.episode_id == Episode.id
                ).where(
                    Schedule.start.between(start, end)
                )
                results = session.execute(q).all()
                series_ids = {r.series_id for r in results if r.series_id}
                movie_ids = {r.movie_id for r in results if r.movie_id}
                return series_ids, movie_ids

            current_series, current_movies = get_ids_in_period(current_start, current_end)
            lookback_series, lookback_movies = get_ids_in_period(lookback_start, lookback_end)

            new_series = current_series - lookback_series
            new_movies = current_movies - lookback_movies

            q = select(Schedule).where(
                Schedule.start.between(current_start, current_end),
                or_(
                    and_(Schedule.episode_id.isnot(None), Episode.series_id.in_(new_series)),
                    Schedule.movie_id.in_(new_movies)
                )
            ).outerjoin(
                Episode, Schedule.episode_id == Episode.id
            ).order_by(
                Schedule.start
            )

            return self._execute(q, ScheduleOutput)

    #Bulk update table values

    def update_end_time(self):
        with self.get_session() as session:
            schedules = session.execute(
                select(Schedule)
                .outerjoin(Episode)
                .outerjoin(Movie)
            ).scalars().all()

            for schedule in schedules:
                if schedule.episode:
                    duration = schedule.episode.duration
                elif schedule.movie:
                    duration = schedule.movie.duration
                else:
                    continue

                if duration:
                    schedule.end = schedule.start + timedelta(minutes=math.ceil(duration/60))

            session.commit()
    
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
    



