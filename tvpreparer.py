from tvdownloader import TVDownloader
from metadatafetcher import MetaDataFetcher
from tvdatabase import TVDatabase
from tvhandler import TVFileHandler, MediaPathManager
from tvconstants import *
from colorama import Fore, Style
import time
import sys
import logging

logging.basicConfig(level=logging.DEBUG)


class TVPreparer():
    def __init__(self):
        self.paths = MediaPathManager()
        self.database = TVDatabase()
        self.downloader = TVDownloader()
        self.handler = TVFileHandler()

    def increment_episodes(self):
        '''
            Increment the current episode.
            Run only once at the start of the week.
        '''
        scheduled_episodes = self.database.get_scheduled_episodes()

        for e in scheduled_episodes:
            self.database.increment_episode(e['series_id'])
            print(f"Series {e["series_name"]}: Episode number incremented.")

    def update_keeping_status(self):
        '''
            Sets episodes that is kept from previous week to be deleted at the end of the week.
        '''

        kept_files = self.database.get_kept_episodes()

        for episode in kept_files:
            self.database.update_episode_keeping_status(episode['id'], False)
            print(f"{episode["filename"]} marked for deletion")

    def cleanup_obsolete_episodes(self):
        obsolete_episodes = self.database.get_obsolete_episodes()

        if not obsolete_episodes:
            print("No episodes to delete")

        for e in obsolete_episodes:
            if not e['last_aired']:
                continue

            path = self.paths.get_filepath(TYPE_SERIES, e["directory"], e["filename"])
            self.handler.delete_media(e["id"], path, TYPE_SERIES)


    def cleanup_obsolete_movies(self):
        obsolete_movies = self.database.get_obsolete_movies()

        if not obsolete_movies:
            print("No movies to delete")
        
        for m in obsolete_movies:
            if not m['last_aired']:
                continue

            path = self.paths.get_filepath(TYPE_MOVIES, m["directory"], m["filename"])
            self.handler.delete_media(m["id"], path, TYPE_MOVIES)

    def create_pending_episodes(self):
        series_list = self.database.get_all_series()
        metadata_fetcher = MetaDataFetcher()

        for series in series_list:    
            if series["source_url"]:
                try:
                    yt_dlp_data = metadata_fetcher.get_ytdlp_season_metadata(TYPE_SERIES, series["directory"], series["season"], video_url=series["source_url"])
                
                    for entry in yt_dlp_data["entries"]:
                        episode_data = metadata_fetcher.extract_episode_info_from_ytdlp(entry)

                        if not episode_data["season_number"]:
                            episode_data["season_number"] = series["season"]

                        existing = self.database.get_episode_by_details(series["id"], episode_data["season_number"], episode_data["episode_number"])

                        if existing:
                            continue

                        self.database.insert_row(TABLE_EPISODES, data=episode_data, series_id = series["id"], status = "pending", download_date = None)

                        print(f"Pending episode added for {series["name"]}")

                except Exception as e:
                    print(f"No metadata available for {series["name"]}")

            elif series["tmdb_id"]:
                try:
                    tmdb_data = metadata_fetcher.get_tmdb_metadata(TYPE_SERIES, series["directory"], series["tmdb_id"], series["season"])

                    for entry in tmdb_data["episodes"]:
                        episode_data = metadata_fetcher.extract_episode_info_from_tmdb(entry)

                        if not episode_data["season_number"]:
                            episode_data["season_number"] = series["season"]

                        existing = self.database.get_episode_by_details(series["id"], episode_data["season_number"], episode_data["episode_number"])

                        if existing:
                            continue

                        self.database.insert_row(TABLE_EPISODES, data=episode_data, series_id = series["id"], status = "pending", download_date = None)

                        print(f"Pending episode added for {series["name"]}")

                except Exception as e:
                    print(f"No metadata available for {series["name"]}")

            else:
                print(f"No metadata available for {series["name"]}")

    def download_weekly_schedule(self):
        pending_episodes = self.database.get_pending_episodes()
        if not pending_episodes:
            print("All episodes are already downloaded")

        for e in pending_episodes:
            if e["source"] == SOURCE_LOCAL:
                continue

            filename = self.paths.create_episode_file_name(
                e["directory"],
                e["season_number"],
                e["episode_number"]
            )

            file_path = self.paths.get_filepath(TYPE_SERIES, e["directory"], filename)
            file_path_check = file_path.exists()

            if file_path_check:
                print(f"Local file found for {filename}, skipping download.")
            else:
                status = self.downloader.download_from_playlist(
                    e["id"],
                    TYPE_SERIES,
                    file_path,
                    e["source_url"],
                    e["episode_number"],
                    total_episodes=e["total_episodes"],
                    reverse_order= e["reverse_order"]
                )

                if status == STATUS_AVAILABLE:
                    self.handler.update_file_info(e["id"], TYPE_SERIES, file_path)

            time.sleep(1)

        pending_movies = self.database.get_scheduled_movies()
        for m in pending_movies:
            if m["source"] == SOURCE_LOCAL:
                continue
            
            filename = self.paths.create_movie_file_name(m["directory"])
            file_path_check = self.paths.get_filepath(TYPE_MOVIES, e["directory"], filename).exists()

            if file_path_check:
                print(f"Local file found for {filename}, skipping download.")
            else:
                status = self.downloader.download_movie(m["id"], m["source_url"])

            if status == STATUS_AVAILABLE:
                self.handler.update_file_info(m["id"], TYPE_MOVIES, file_path)
            
            time.sleep(1)

    def verify_files_for_scheduled_media(self):
        episodes = self.database.get_scheduled_episodes()

        for e in episodes:
            if e["filename"]:
                filename = e["filename"]
            else:
                filename = self.paths.create_episode_file_name(e["directory"],e["season_number"], e["episode_number"])

            #series_dl._check_file_integrity()

            file_path = self.paths.get_filepath(TYPE_SERIES, e["directory"], filename)
            file_status = self.handler.verify_local_file(e["id"], file_path, TYPE_SERIES)

            if file_status == STATUS_AVAILABLE:
                print(Fore.GREEN + "File found: " + Style.RESET_ALL, filename)
            else:
                print(Fore.RED + "File missing: "+ Style.RESET_ALL, filename)

            self.handler.update_file_info(e["id"], TYPE_SERIES, file_path)

        movies = self.database.get_scheduled_movies()

        for m in movies:
            if m["filename"]:
                filename = m["filename"]
            else:
                filename = self.paths.create_movie_file_name(m["directory"])
            
            #series_dl._check_file_integrity()

            file_path = self.paths.get_filepath(TYPE_MOVIES, m["directory"], filename)
            file_status = self.handler.verify_local_file(m["id"], file_path, TYPE_MOVIES)

            if file_status == STATUS_AVAILABLE:
                print(Fore.GREEN + "File found: " + Style.RESET_ALL, filename)
            else:
                print(Fore.RED + "File missing: "+ Style.RESET_ALL, filename)

            self.handler.update_file_info(m["id"], TYPE_MOVIES, file_path)

    def link_programs_to_schedule(self):
        series = self.database.get_all_series()

        for program in series:
            entry = self.database.get_program_schedule_by_id(program["id"])
            scheduled_episodes = self.database.get_scheduled_episodes_by_id(program["id"])
            
            if not entry:
                continue
            
            if not scheduled_episodes:
                print(f"No scheduled episodes for {program['name']}")
                continue

            originals = [s for s in entry if s["is_rerun"] == 0]
            reruns = [s for s in entry if s["is_rerun"] == 1]

            first_is_rerun = entry[0]["is_rerun"] == 1
            episode_offset = 0
            
            if first_is_rerun and reruns and scheduled_episodes:
                if scheduled_episodes[0]["status"] == STATUS_AVAILABLE:
                    first_episode_id = scheduled_episodes[0]['id']
                    self.database.update_episode_links(reruns[0]["id"], first_episode_id)
                    self.database.update_episode_keeping_status(first_episode_id, True)
                    print(Fore.GREEN + "Success:" + Style.RESET_ALL, f"Linked first re-run of {program['name']} to episode {scheduled_episodes[0]['episode_number']} (kept from last week)")
                else:
                    print(Fore.RED + "Failure:" + Style.RESET_ALL, f"Failed to link first re-run of {program['name']} (S{scheduled_episodes[0]['season_number']}E{scheduled_episodes[0]['episode_number']}) scheduled to link to (day {rerun['day_of_week']}, {rerun['start_time']}). File is not available")
                
                reruns.pop(0)
                episode_offset = 1

            for idx, original in enumerate(originals):
                episode_idx = idx + episode_offset
                if episode_idx < len(scheduled_episodes):
                    if scheduled_episodes[episode_idx]["status"] == STATUS_AVAILABLE:
                        episode_id = scheduled_episodes[episode_idx]['id']
                        self.database.update_episode_links(original['id'], episode_id)
                        print(Fore.GREEN + "Success:" + Style.RESET_ALL, f"Linked original run of {program['name']} (S{scheduled_episodes[episode_idx]['season_number']}E{scheduled_episodes[episode_idx]['episode_number']}). {scheduled_episodes[episode_idx]['filename']} set to show at (day {original['day_of_week']}, {original['start_time']})")
                    else:
                        print(Fore.RED + "Failure:" + Style.RESET_ALL, f"Failed to link original run of {program['name']} (S{scheduled_episodes[episode_idx]['season_number']}E{scheduled_episodes[episode_idx]['episode_number']}), scheduled to show at (day {original['day_of_week']}, {original['start_time']}). File is not available")

            for idx, rerun in enumerate(reruns):
                episode_idx = idx + episode_offset
                if episode_idx < len(scheduled_episodes):
                    if scheduled_episodes[episode_idx]["status"] == STATUS_AVAILABLE:
                        episode_id = scheduled_episodes[episode_idx]['id']
                        self.database.update_episode_links(rerun['id'], episode_id)
                        print(Fore.GREEN + "Success:" + Style.RESET_ALL, f"Linked re-run of {program['name']} (S{scheduled_episodes[episode_idx]['season_number']}E{scheduled_episodes[episode_idx]['episode_number']}). {scheduled_episodes[episode_idx]['filename']} set to show at (day {rerun['day_of_week']}, {rerun['start_time']})")
                    else:
                        print(Fore.RED + "Failure:" + Style.RESET_ALL, f"Failed to link re-run of {program['name']} (S{scheduled_episodes[episode_idx]['season_number']}E{scheduled_episodes[episode_idx]['episode_number']}), scheduled to show at (day {rerun['day_of_week']}, {rerun['start_time']}). File is not available")


if __name__ == "__main__":
    prep = TVPreparer()

    if len(sys.argv)>1:
        operation = sys.argv[1]
        if operation == "increment":
            prep.increment_episodes()

        elif operation == "delete":
            prep.cleanup_obsolete_episodes()

        elif operation == "keep":
            prep.update_keeping_status()

        elif operation == "pending":
            prep.create_pending_episodes()

        elif operation == "download":
            prep.download_weekly_schedule()

        elif operation == "verify":
            prep.verify_files_for_scheduled_media()

        elif operation == "link":
            prep.link_programs_to_schedule()

        elif operation == "all":
            prep.cleanup_obsolete_episodes()
            prep.update_keeping_status()
            prep.create_pending_episodes()
            prep.download_weekly_schedule()
            prep.verify_files_for_scheduled_media()
            prep.link_programs_to_schedule()

        else:
            print("Not a valid operation")