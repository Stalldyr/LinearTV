from tvcore.tvdatabase import TVDatabase, Series, Movie, Schedule, Episode
from tvcore.schemas import SeriesInput, MovieInput, EpisodeInput, ScheduleInput

tvdb = TVDatabase()
from datetime import datetime, time

def db_setup():
    tvdb.setup_database()
    tvdb.reset_database()

def insert_update_delete_media():
    # ============================================================================
    # EKSEMPEL 1: Legge til og administrere serier og filmer
    # ============================================================================

    delete_test = Series(title = "madetobedeleted")
    delete_id = tvdb.add(delete_test)
    tvdb.delete(Series(id=delete_id))

    delete_test = Movie(title = "madetobedeleted")
    delete_id = tvdb.add(delete_test)
    tvdb.delete(Movie(id=delete_id))

    for s in series:
        print(Series(**s.model_dump()))
        tvdb.add(Series(**s.model_dump()))

    # Oppdatere serie
    #tvdb.insert_program(data)

    # Hente alle serier
    all_series = tvdb.get_all_series()
    for series in all_series:
        print(f"{series.title} - S{series.start_season}E{series.start_episode}")

def episodes():
    # ============================================================================
    # EKSEMPEL 2: Håndtere episoder
    # ============================================================================

    # Legge til episode
    new_episode = EpisodeInput(
        series_id = 2,
        season_number=1,
        episode_number=1,
        title="Pilot",
        description="Walter White finner ut han har kreft",
        duration=58
    )

    tvdb.add(Episode(**new_episode.model_dump()))


def schedule_test():
    # ============================================================================
    # EKSEMPEL 3: Weekly schedule
    # ============================================================================

    # Legge til schedule entry
    tvdb.add({
        'series_id': series_id,
        'episode_id': episode['id'],
        'name': 'Breaking Bad',
        'day_of_week': 5,  # Fredag
        'start_time': time(20, 0),  # 20:00
        'end_time': time(20, 45),
        'is_rerun': False
    })

    # Hente ukens schedule
    weekly_schedule = tvdb.get_weekly_schedule()
    for entry in weekly_schedule:
        day_names = ['', 'Man', 'Tir', 'Ons', 'Tor', 'Fre', 'Lør', 'Søn']
        print(f"{day_names[entry['day_of_week']]} {entry['start_time']}: {entry['name']}")

    # Hente schedule for en spesifikk serie
    series_schedule = tvdb.get_program_schedule_by_series_id(series_id)
    print(f"\n{len(series_schedule)} airings for denne serien")

    # Oppdatere schedule count
    tvdb.update_schedule_count()

    # ============================================================================
    # EKSEMPEL 4: Filmer
    # ============================================================================

    # Legge til film
    movie_id = tvdb.add(
        "movies",
        name="The Shawshank Redemption",
        tmdb_id=278,
        description="To fengslede menn knytter vennskap",
        duration=142,
        year=1994,
        genre="Drama",
        directory="/media/movies/shawshank"
    )

    # Hente alle filmer
    all_movies = tvdb.get_all_movies()
    for movie in all_movies:
        print(f"{movie['name']} ({movie['year']})")

    # ============================================================================
    # EKSEMPEL 5: Download schedule
    # ============================================================================

    # Hente download schedule
    download_schedule = tvdb.get_weekly_download_schedule()
    for item in download_schedule:
        print(f"{item['name']}: {item['count']} episodes to download")
        print(f"  Season {item['season']}, starting from episode {item['episode']}")

    # Inkrement episode etter download
    tvdb.increment_episode(series_id)

    # ============================================================================
    # EKSEMPEL 6: Airing operations
    # ============================================================================

    # Hente komplett air schedule
    air_schedule = tvdb.get_air_schedule()
    for program in air_schedule:
        content = f"{program['content_type']}: {program['name']}"
        if program['episode_number']:
            content += f" (Episode {program['episode_number']})"
        print(f"{content} - Status: {program['status']}")

    # Hente current program
    current = tvdb.get_current_program()
    if current:
        print(f"\nNå vises: {current['name']}")
        print(f"Status: {current['status']}")
        print(f"Filnavn: {current['filename']}")
    else:
        print("\nIngen program sender nå")

    # ============================================================================
    # EKSEMPEL 7: Cleanup operations
    # ============================================================================

    # Hente obsolete episodes (for sletting)
    obsolete_eps = tvdb.get_obsolete_episodes()
    print(f"\n{len(obsolete_eps)} episodes kan slettes")
    for ep in obsolete_eps:
        print(f"  - {ep['filename']}")

    # Hente kept episodes
    kept_eps = tvdb.get_kept_episodes()
    print(f"\n{len(kept_eps)} episodes beholdes")

    # ============================================================================
    # EKSEMPEL 8: Søk og filter
    # ============================================================================

    # Scheduled series (serier i ukeplanen)
    scheduled = tvdb.get_scheduled_series()
    print(f"\n{len(scheduled)} serier i ukeplanen")

    # Available episodes
    available = tvdb.get_available_episodes()
    print(f"\n{len(available)} episodes tilgjengelig for visning")

    # Sjekk om rerun kommer før ny episode
    has_rerun_first = tvdb.check_if_rerun_before_new(series_id)
    if has_rerun_first:
        print("Reprise vises før ny episode")

    # ============================================================================
    # EKSEMPEL 9: Database maintenance
    # ============================================================================

    # Reset database (fjerner metadata men beholder struktur)
    # tvdb.reset_database()  # Uncomment for å kjøre

    # Slette program
    # tvdb.delete_program(series_id, 'series')  # Uncomment for å kjøre

    print("\n✅ Alle eksempler kjørt!")

###Movies

shawshank = MovieInput(
    title="The Shawshank Redemption",
    tmdb_id=278,
    description="To fengslede menn knytter vennskap",
    duration=142,
    release="1994",
    genre="Drama"
)

series = [
    SeriesInput(
        title="Seinfeld",
        description="Serie om ingenting",
        genre="comedy",
        start_season=4,
        start_episode=1,
        tmdb_id=1400
    ),
    SeriesInput(
        title="Breaking Bad",
        start_season=1,
        start_episode=1
    )
]

def SQLAlchemy_test():

    """
    Eksempler på bruk av den nye SQLAlchemy-baserte TVDatabase
    """


    # ============================================================================
    # EKSEMPEL 1: Legge til og administrere serier
    # ============================================================================

    # Legge til ny serie
    series_id = 5

    # Oppdatere serie
    series_id = tvdb.add(
        Series(
            **SeriesInput(
                title="Breaking Bad",
                start_season=1,
                start_episode=1
            ).model_dump()
        )
    )

    # Hente alle serier
    all_series = tvdb.get_all_series()
    for series in all_series:
        print(f"{series['name']} - S{series['season']}E{series['episode']}")

    # ============================================================================
    # EKSEMPEL 2: Håndtere episoder
    # ============================================================================

    # Legge til episode
    new_episode = EpisodeInput(
        series_id = series_id,
        season_number=1,
        episode_number=1,
        title="Pilot",
        description="Walter White finner ut han har kreft",
        duration=58
    )



    # ============================================================================
    # EKSEMPEL 3: Weekly schedule
    # ============================================================================

    # Legge til schedule entry
    tvdb.add({
        'series_id': series_id,
        'episode_id': episode['id'],
        'name': 'Breaking Bad',
        'day_of_week': 5,  # Fredag
        'start_time': time(20, 0),  # 20:00
        'end_time': time(20, 45),
        'is_rerun': False
    })

    # Hente ukens schedule
    weekly_schedule = tvdb.get_weekly_schedule()
    for entry in weekly_schedule:
        day_names = ['', 'Man', 'Tir', 'Ons', 'Tor', 'Fre', 'Lør', 'Søn']
        print(f"{day_names[entry['day_of_week']]} {entry['start_time']}: {entry['name']}")

    # Hente schedule for en spesifikk serie
    series_schedule = tvdb.get_program_schedule_by_series_id(series_id)
    print(f"\n{len(series_schedule)} airings for denne serien")

    # Oppdatere schedule count

    # Hente pending episodes
    pending = tvdb.get_pending_episodes(strict=True, schedule=True)
    for ep in pending:
        print(f"{ep['series_name']} - S{ep['season_number']}E{ep['episode_number']}: {ep['title']}")

    # Oppdatere episode status
    episode = tvdb.get_episode_by_details(series_id, 1, 1)
    if episode:
        tvdb.update_media_status(
            episode['id'],
            'series',
            'available',
            filename='breaking_bad_s01e01.mp4',
            file_size=1500000000,  # bytes
            download_date=datetime.now().date()
        )

    # Markere episode for keeping
    tvdb.update_episode_keeping_status(episode['id'], keep=True)

    # ============================================================================
    # EKSEMPEL 4: Filmer
    # ============================================================================

    # Legge til film
    movie_id = tvdb.add(
        "movies",
        name="The Shawshank Redemption",
        tmdb_id=278,
        description="To fengslede menn knytter vennskap",
        duration=142,
        year=1994,
        genre="Drama",
        directory="/media/movies/shawshank"
    )

    # Hente alle filmer
    all_movies = tvdb.get_all_movies()
    for movie in all_movies:
        print(f"{movie['name']} ({movie['year']})")

    # ============================================================================
    # EKSEMPEL 5: Download schedule
    # ============================================================================

    # Hente download schedule
    download_schedule = tvdb.get_weekly_download_schedule()
    for item in download_schedule:
        print(f"{item['name']}: {item['count']} episodes to download")
        print(f"  Season {item['season']}, starting from episode {item['episode']}")

    # Inkrement episode etter download
    tvdb.increment_episode(series_id)

    # ============================================================================
    # EKSEMPEL 6: Airing operations
    # ============================================================================

    # Hente komplett air schedule
    air_schedule = tvdb.get_air_schedule()
    for program in air_schedule:
        content = f"{program['content_type']}: {program['name']}"
        if program['episode_number']:
            content += f" (Episode {program['episode_number']})"
        print(f"{content} - Status: {program['status']}")

    # Hente current program
    current = tvdb.get_current_program()
    if current:
        print(f"\nNå vises: {current['name']}")
        print(f"Status: {current['status']}")
        print(f"Filnavn: {current['filename']}")
    else:
        print("\nIngen program sender nå")

    # ============================================================================
    # EKSEMPEL 7: Cleanup operations
    # ============================================================================

    # Hente obsolete episodes (for sletting)
    obsolete_eps = tvdb.get_obsolete_episodes()
    print(f"\n{len(obsolete_eps)} episodes kan slettes")
    for ep in obsolete_eps:
        print(f"  - {ep['filename']}")

    # Hente kept episodes
    kept_eps = tvdb.get_kept_episodes()
    print(f"\n{len(kept_eps)} episodes beholdes")

    # ============================================================================
    # EKSEMPEL 8: Søk og filter
    # ============================================================================

    # Scheduled series (serier i ukeplanen)
    scheduled = tvdb.get_scheduled_series()
    print(f"\n{len(scheduled)} serier i ukeplanen")

    # Available episodes
    available = tvdb.get_available_episodes()
    print(f"\n{len(available)} episodes tilgjengelig for visning")

    # Sjekk om rerun kommer før ny episode
    has_rerun_first = tvdb.check_if_rerun_before_new(series_id)
    if has_rerun_first:
        print("Reprise vises før ny episode")

    # ============================================================================
    # EKSEMPEL 9: Database maintenance
    # ============================================================================

    # Reset database (fjerner metadata men beholder struktur)
    # tvdb.reset_database()  # Uncomment for å kjøre

    # Slette program
    # tvdb.delete_program(series_id, 'series')  # Uncomment for å kjøre

    print("\n✅ Alle eksempler kjørt!")


def add_test_entries():
    from datetime import datetime

    # Series
    blackadder = Series(
        title="Blackadder",
        description="Historisk britisk komedieserie",
        genre="Comedy",
        release=datetime(1983, 6, 15),
        slug="blackadder",
        source_url="https://www.youtube.com/playlist?list=PLx",
        reverse_order=False,
        start_season=1,
        start_episode=1
    )

    # Movie
    life_of_brian = Movie(
        title="Monty Python's Life of Brian",
        description="Satirisk komediefilm fra 1979",
        genre="Comedy",
        release=datetime(1979, 11, 8),
        slug="life-of-brian",
        source_url="https://www.youtube.com/watch?v=xxx",
        duration=94.0
    )

    # Episode
    episode1 = Episode(
        series=blackadder,
        title="The Foretelling",
        season_number=1,
        episode_number=1,
        description="Blackadder møter Henrik V",
        duration=29.5,
        release=datetime(1983, 6, 15)
    )

    # Schedule entries
    schedule1 = Schedule(
        series=blackadder,
        episode=episode1,
        title="Blackadder",
        start=datetime(2026, 3, 3, 20, 0),
        end=datetime(2026, 3, 3, 20, 30),
        channel="cable",
        status="pending",
        is_rerun=False
    )

    schedule2 = Schedule(
        movie=life_of_brian,
        title="Monty Python's Life of Brian",
        start=datetime(2026, 3, 5, 21, 0),
        end=datetime(2026, 3, 5, 22, 34),
        channel="cable",
        status="pending",
        is_rerun=False
    )

    for x in [blackadder, life_of_brian, episode1, schedule1, schedule2]:
        print(tvdb.add(x))

test = tvdb.get_pending_programs(datetime(2026, 3, 5, 0, 0), datetime(2026, 3, 6, 21, 0))

#add_test_entries()

#test = tvdb.get_air_schedule()

print(test[0].episode)

