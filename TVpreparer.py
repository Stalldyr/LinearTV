from TVdownloader import TVDownloader
from TVdatabase import TVDatabase
from helper import create_path, verify_path, create_episode_file_name, create_movie_file_name
import os
import time
import sys
import logging
from TVconstants import *

logging.basicConfig(level=logging.DEBUG)

class TVPreparer():
    def __init__(self, download_path="downloads"):
        self.download_path = download_path

        #self.tv_dl = TVDownloader(download_path) #Remove??
        self.tv_db = TVDatabase()

    def increment_episodes(self):
        scheduled_episodes = self.tv_db.get_scheduled_episodes()

        for e in scheduled_episodes:
            self.tv_db.increment_episode(e['series_id'])

    def update_keeping_status(self):
        """
            Sets episodes that is kept from previous week to be deleted at the end of the week.
        """

        kept_files = self.tv_db.get_kept_episodes()

        for episode in kept_files:
            self.tv_db.update_episode_keeping_status(episode['id'], False)
            print("marked for deletion")

    def cleanup_obsolete_media(self):
        obsolete_episodes = self.tv_db.get_obsolete_episodes()

        for e in obsolete_episodes:
            if not e['last_aired']:
                continue

            series_dl = TVDownloader(e["directory"], TYPE_SERIES)
            series_dl.delete_media(e["id"], e["filename"])

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

            series_dl = TVDownloader(e["directory"], TYPE_SERIES)

            filename = create_episode_file_name(e["directory"], e["season_number"], e["episode_number"])
            
            series_dl.download_episode(e["id"], 
                                       e["source_url"], 
                                       e["season_number"], 
                                       e["episode_number"],
                                       filename,
                                       total_episodes=e["total_episodes"],
                                       reverse_order= e["reverse_order"]
                                       )
            
            time.sleep(1)

        pending_movies = self.tv_db.get_scheduled_movies()
        for m in pending_movies:
            if m["source"] == SOURCE_LOCAL:
                continue
            
            filename = create_movie_file_name(m["directory"])

            movie_dl = TVDownloader(m["directory"], TYPE_MOVIES)
            movie_dl.download_movie(m["id"], m["source_url"], filename)
            
            time.sleep(1)

    def verify_files_for_scheduled_media(self):
        episodes = self.tv_db.get_scheduled_episodes()

        for e in episodes:
            if e["filename"]:
                filename = e["filename"]
            else:
                filename = create_episode_file_name(e["directory"],e["season_number"], e["episode_number"])

            series_dl = TVDownloader(e["directory"], TYPE_SERIES)
            series_dl.verify_local_file(e["id"], filename)

        movies = self.tv_db.get_scheduled_movies()

        for m in movies:
            if m["filename"]:
                filename = m["filename"]
            else:
                filename = create_movie_file_name(m["directory"])

            movies_dl = TVDownloader(m["directory"], TYPE_MOVIES)
            movies_dl.verify_local_file(m["id"], filename)

    def link_programs_to_schedule(self):
        series = self.tv_db.get_all_series()

        for program in series:
            entry = self.tv_db.get_program_schedule(program["id"])
            available_episodes = self.tv_db.get_available_episodes_by_id(program["id"])
            
            if not entry:
                continue
            
            if not available_episodes:
                print(f"No available episodes for {program['name']}")
                continue

            originals = [s for s in entry if s["is_rerun"] == 0]
            reruns = [s for s in entry if s["is_rerun"] == 1]

            first_is_rerun = entry[0]["is_rerun"] == 1
            episode_offset = 0
            
            if first_is_rerun and reruns and available_episodes:
                first_episode_id = available_episodes[0]['id']
                self.tv_db.update_episode_links(reruns[0]["id"], first_episode_id)
                self.tv_db.update_episode_keeping_status(first_episode_id, True)
                print(f"Koblet første reprise for {program['name']} til episode {available_episodes[0]['episode_number']} (beholdes)")
                reruns.pop(0)
                episode_offset = 1

            for idx, original in enumerate(originals):
                episode_idx = idx + episode_offset
                if episode_idx < len(available_episodes):
                    episode_id = available_episodes[episode_idx]['id']
                    self.tv_db.update_episode_links(original['id'], episode_id)
                    print(f"Koblet original sending {available_episodes[episode_idx]['filename']} til (dag {original['day_of_week']}, {original['start_time']})")

            for idx, rerun in enumerate(reruns):
                episode_idx = idx + episode_offset
                if episode_idx < len(available_episodes):
                    episode_id = available_episodes[episode_idx]['id']
                    self.tv_db.update_episode_links(rerun['id'], episode_id)
                    print(f"Koblet reprise {available_episodes[episode_idx]['filename']} til (dag {rerun['day_of_week']}, {rerun['start_time']})")

            
if __name__ == "__main__":
    prep = TVPreparer()

    if len(sys.argv)>1:
        operation = sys.argv[1]
        if operation == "increment":
            prep.increment_episodes()

        elif operation == "keep":
            prep.update_keeping_status()

        elif operation == "delete":
            prep.cleanup_obsolete_media()

        elif operation == "pending":
            prep.create_pending_episodes()

        elif operation == "verify":
            prep.verify_files_for_scheduled_media()

        elif operation == "download":
            prep.download_weekly_schedule()

        elif operation == "link":
            prep.link_programs_to_schedule()

        elif operation == "all":
            prep.cleanup_obsolete_media()
            prep.update_keeping_status()
            prep.create_pending_episodes()
            prep.download_weekly_schedule()
            prep.verify_files_for_scheduled_media()
            prep.link_programs_to_schedule()

        else:
            print("Not a valid operation")