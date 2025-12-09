from TVdownloader import TVDownloader
from TVdatabase import TVDatabase
from TVconstants import *
from helper import create_episode_file_name, create_movie_file_name, verify_path, create_path
from colorama import Fore, Style
import time
import sys
import logging

logging.basicConfig(level=logging.DEBUG)

class TVPreparer():
    def __init__(self, download_path="downloads"):
        self.download_path = download_path

        self.tv_db = TVDatabase()

    def increment_episodes(self):
        '''
            Increment the current episode.
            Run only once at the start of the week.
        '''
        scheduled_episodes = self.tv_db.get_scheduled_episodes()

        for e in scheduled_episodes:
            self.tv_db.increment_episode(e['series_id'])
            print(f"Series {e["series_name"]}: Episode number incremented.")

    def update_keeping_status(self):
        '''
            Sets episodes that is kept from previous week to be deleted at the end of the week.
        '''

        kept_files = self.tv_db.get_kept_episodes()

        for episode in kept_files:
            self.tv_db.update_episode_keeping_status(episode['id'], False)
            print(f"{episode["filename"]} marked for deletion")

    def cleanup_obsolete_episodes(self):
        obsolete_episodes = self.tv_db.get_obsolete_episodes()

        for e in obsolete_episodes:
            if not e['last_aired']:
                continue

            series_dl = TVDownloader(e["directory"], TYPE_SERIES)
            series_dl.delete_media(e["id"], e["filename"])

    def delete_obsolete_movies(self):
        obsolete_movies = self.tv_db.get_obsolete_movies()
        for m in obsolete_movies:
            if not m['last_aired']:
                continue

            series_dl = TVDownloader(m["directory"], TYPE_MOVIES)
            series_dl.delete_media(m["id"], m["filename"])

    def create_pending_episodes(self):
        series_list = self.tv_db.get_all_series()

        for series in series_list:
            series_dl = TVDownloader(series["directory"], TYPE_SERIES)
            if series["source_url"]:
                try:
                    yt_dlp_data = series_dl.get_ytdlp_season_metadata(series["season"])
                
                    for entry in yt_dlp_data["entries"]:
                        episode_data = series_dl.get_ytdlp_epsiode_info(entry)

                        if not episode_data["season_number"]:
                            episode_data["season_number"] = series["season"]

                        existing = self.tv_db.get_episode_by_details(series["id"], episode_data["season_number"], episode_data["episode_number"])

                        if existing:
                            continue

                        self.tv_db.insert_row(TABLE_EPISODES, data=episode_data, series_id = series["id"], status = "pending", download_date = None)

                        print(f"Pending episode added for {series["name"]}")

                except Exception as e:
                    print(series["name"], e)

            elif series["tmdb_id"]:
                try:
                    tmdb_data = series_dl.get_tmdb_season_metadata(series["tmdb_id"], series["season"])

                    for entry in tmdb_data["episodes"]:
                        episode_data = series_dl.get_tmdb_episode_info(entry)

                        if not episode_data["season_number"]:
                            episode_data["season_number"] = series["season"]

                        existing = self.tv_db.get_episode_by_details(series["id"], episode_data["season_number"], episode_data["episode_number"])

                        if existing:
                            continue

                        self.tv_db.insert_row(TABLE_EPISODES, data=episode_data, series_id = series["id"], status = "pending", download_date = None)

                        print(f"Pending episode added for {series["name"]}")

                except Exception as e:
                    print(e)

            else:
                print(f"No metadata available for {series["name"]}")

    def download_weekly_schedule(self):
        pending_episodes = self.tv_db.get_pending_episodes()

        if not pending_episodes:
            print("All episodes are already downloaded")

        for e in pending_episodes:
            if e["source"] == SOURCE_LOCAL:
                continue

            filename = create_episode_file_name(
                e["directory"],
                e["season_number"],
                e["episode_number"]
            )

            series_dl = TVDownloader(e["directory"], TYPE_SERIES, filename)

            filepath = create_path(series_dl.program_dir, filename)
            integrity_check = verify_path(filepath)

            #Verify file integrity

            if integrity_check:
                print(f"Local file found for {filename}, skipping download.")
            else:
                status = series_dl.download_episode(
                    e["id"], 
                    e["source_url"], 
                    e["season_number"], 
                    e["episode_number"],
                    filename,
                    total_episodes=e["total_episodes"],
                    reverse_order= e["reverse_order"]
                )

                if status == STATUS_AVAILABLE:
                    series_dl._update_file_info(e["id"])

            time.sleep(1)

        pending_movies = self.tv_db.get_scheduled_movies()
        for m in pending_movies:
            if m["source"] == SOURCE_LOCAL:
                continue
            
            filename = create_movie_file_name(m["directory"])
            integrity_check = verify_path(filepath)

            #Verify file integrity

            if integrity_check:
                print(f"Local file found for {filename}, skipping download.")
            else:
                movie_dl = TVDownloader(m["directory"], TYPE_MOVIES, filename)
                movie_dl.download_movie(m["id"], m["source_url"], filename)
            
            time.sleep(1)

    def verify_files_for_scheduled_media(self):
        episodes = self.tv_db.get_scheduled_episodes()

        for e in episodes:
            if e["filename"]:
                filename = e["filename"]
            else:
                filename = create_episode_file_name(e["directory"],e["season_number"], e["episode_number"])

            series_dl = TVDownloader(e["directory"], TYPE_SERIES, filename)
            #series_dl._check_file_integrity()
            if series_dl.verify_local_file(e["id"]) == STATUS_AVAILABLE:
                print(Fore.GREEN + "File found: " + Style.RESET_ALL, filename)
            else:
                print(Fore.RED + "File missing: "+ Style.RESET_ALL, filename)

            series_dl._update_file_info(e["id"])

        movies = self.tv_db.get_scheduled_movies()

        for m in movies:
            if m["filename"]:
                filename = m["filename"]
            else:
                filename = create_movie_file_name(m["directory"])

            movies_dl = TVDownloader(m["directory"], TYPE_MOVIES, filename)
            
            #series_dl._check_file_integrity()
            if movies_dl.verify_local_file(e["id"]) == STATUS_AVAILABLE:
                print(Fore.GREEN + "File found: " + Style.RESET_ALL, filename)
            else:
                print(Fore.RED + "File missing: "+ Style.RESET_ALL, filename)

    def link_programs_to_schedule(self):
        series = self.tv_db.get_all_series()

        for program in series:
            entry = self.tv_db.get_program_schedule_by_id(program["id"])
            scheduled_episodes = self.tv_db.get_scheduled_episodes_by_id(program["id"])
            
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
                    self.tv_db.update_episode_links(reruns[0]["id"], first_episode_id)
                    self.tv_db.update_episode_keeping_status(first_episode_id, True)
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
                        self.tv_db.update_episode_links(original['id'], episode_id)
                        print(Fore.GREEN + "Success:" + Style.RESET_ALL, f"Linked original run of {program['name']} (S{scheduled_episodes[episode_idx]['season_number']}E{scheduled_episodes[episode_idx]['episode_number']}). {scheduled_episodes[episode_idx]['filename']} set to show at (day {original['day_of_week']}, {original['start_time']})")
                    else:
                        print(Fore.RED + "Failure:" + Style.RESET_ALL, f"Failed to link original run of {program['name']} (S{scheduled_episodes[episode_idx]['season_number']}E{scheduled_episodes[episode_idx]['episode_number']}), scheduled to show at (day {original['day_of_week']}, {original['start_time']}). File is not available")

            for idx, rerun in enumerate(reruns):
                episode_idx = idx + episode_offset
                if episode_idx < len(scheduled_episodes):
                    if scheduled_episodes[episode_idx]["status"] == STATUS_AVAILABLE:
                        episode_id = scheduled_episodes[episode_idx]['id']
                        self.tv_db.update_episode_links(rerun['id'], episode_id)
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

        elif operation == "verify":
            prep.verify_files_for_scheduled_media()

        elif operation == "download":
            prep.download_weekly_schedule()

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