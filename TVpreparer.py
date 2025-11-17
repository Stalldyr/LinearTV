from TVdownloader import TVDownloader
from TVdatabase import TVDatabase
from helper import create_path, verify_path, _create_file_name, create_movie_file_name
import os
import time
import sys
import logging

logging.basicConfig(level=logging.DEBUG)

class TVPreparer():
    def __init__(self, download_path="downloads"):
        self.download_path = download_path

        self.tv_dl = TVDownloader(download_path)
        self.tv_db = TVDatabase()

    def cleanup_obsolete_episodes(self):
        obsolete_episodes = self.tv_db.get_obsolete_episodes()

        for episode in obsolete_episodes:
            if not episode['last_aired']:
                continue

            file_path = create_path(self.download_path, episode['directory'], episode['filename'])
            try:
                if verify_path(file_path):
                    os.remove(file_path)
                    print(f"Slettet fil: {file_path}")
                else:
                    print(f"Filen finnes ikke: {file_path}")
                
                self.tv_db.update_episode_status(episode['id'], 'deleted')
            except Exception as e:
                print(f"Feil ved sletting av fil {file_path}: {e}")

        obsolete_movies = self.tv_db.get_obsolete_movies()

        for movie in obsolete_movies:
            file_path = create_path(self.download_path, movie['directory'], movie['filename'])
            try:
                if verify_path(file_path):
                    os.remove(file_path)
                    print(f"Slettet fil: {file_path}")
                else:
                    print(f"Filen finnes ikke: {file_path}")
                
                self.tv_db.update_episode_status(episode['id'], 'deleted')
            except Exception as e:
                print(f"Feil ved sletting av fil {file_path}: {e}")

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

    def create_pending_episodes(self):
        series_list = self.tv_db.get_all_series()

        for series in series_list:
            if series["source_url"]:
                try:
                    yt_dlp_data = self.tv_dl.get_ytdlp_season_metadata(series["season"], series["directory"])
                except Exception as e:
                    print(series["name"], e)

                for entry in yt_dlp_data["entries"]:
                    episode_data = self.tv_dl.get_ytdlp_epsiode_info(entry)

                    if not episode_data["season_number"]:
                        episode_data["season_number"] = series["season"]

                    existing = self.tv_db.get_episode_by_details(series["id"], episode_data["season_number"], episode_data["episode_number"])

                    if existing:
                        continue

                    self.tv_db.insert_row("episodes", data=episode_data, series_id = series["id"], status = "pending", download_date = None)

                    print(f"Pending episode added for {series["name"]}")

            elif series["tmdb_id"]:
                tmdb_data = self.tv_dl.get_tmdb_season_metadata(series["season"], series["directory"], series["tmdb_id"])

                for entry in tmdb_data["episodes"]:
                    episode_data = self.tv_dl.get_tmdb_episode_info(entry)

                    if not episode_data["season_number"]:
                        episode_data["season_number"] = series["season"]

                    existing = self.tv_db.get_episode_by_details(series["id"], episode_data["season_number"], episode_data["episode_number"])

                    if existing:
                        continue

                    self.tv_db.insert_row("episodes", data=episode_data, series_id = series["id"], status = "pending", download_date = None)

                    print(f"Pending episode added for {series["name"]}")

            else:
                print(f"No metadata available for {series["name"]}")

    def download_weekly_schedule(self):
        schedule = self.tv_db.get_weekly_download_schedule()

        for entry in schedule:
            total_episodes = self.tv_dl.get_season_metadata(entry)
            pending_episodes = self.tv_db.get_pending_episodes(entry["series_id"], entry["episode"], entry["count"])

            start_episode = entry["episode"]

            for idx, pending_episode in enumerate(pending_episodes):
                episode_num = start_episode + idx

                self.tv_dl.download_episode(entry, pending_episode, episode_num, total_episodes)

                time.sleep(1)


    def verify_nonavailable_episodes(self):
        '''
            Checks if there's any episodes that should not be there
        '''

        nonavailable_episodes = self.tv_db.get_nonavailable_episodes()

    def verify_files_for_scheduled_media(self):
        episodes = self.tv_db.get_scheduled_episodes()

        for e in episodes:
            if e["filename"]:
                filename = e["filename"]
            else:
                filename = _create_file_name(e["directory"],e["season_number"], e["episode_number"])

            path = create_path(self.download_path, e['directory'], filename)
            success = verify_path(path)

            if success:
                print(f"Fil eksisterer: {filename}")
                file_info = {
                    "filename": filename,
                    "file_size": os.path.getsize(path), 
                } 

                self.tv_db.edit_row_by_id("episodes", e["id"], **file_info)
                self.tv_db.update_episode_status(e['id'], 'available')
            else:
                print(f"Fil mangler: {filename}")
                self.tv_db.update_episode_status(e['id'], 'missing')

        movies = self.tv_db.get_scheduled_movies()

        for m in movies:
            if m["filename"]:
                filename = m["filename"]
            else:
                filename = create_movie_file_name(m["directory"])

            path = create_path(self.download_path, m['directory'], filename)
            success = verify_path(path)

            if success:
                print(f"Fil eksisterer: {filename}")
                file_info = {
                    "filename": filename,
                    "file_size": os.path.getsize(path), 
                } 

                self.tv_db.edit_row_by_id("movies", m["id"], **file_info)
                self.tv_db.update_episode_status(m['id'], 'available')
            else:
                print(f"Fil mangler: {filename}")
                self.tv_db.update_episode_status(m['id'], 'missing')

    def link_episodes_to_schedule(self):
        series = self.tv_db.get_all_series()

        for program in series:
            entry = self.tv_db.get_program_schedule(program["id"])
            available_episodes = self.tv_db.get_available_episodes_by_id(program["id"])
            
            if not entry:
                #print(f"Ingen sendeskjema funnet for serie {entry["series_id"]}")
                continue

            #Checks if rerun comes before the new episode in the weekly schedule
            
            originals = [s for s in entry if s["is_rerun"] == 0]
            reruns = [s for s in entry if s["is_rerun"] == 1]

            offset = entry[0]["is_rerun"]
            if offset:
                self.tv_db.update_download_links(entry[0]["id"], entry[-1]["episode_id"])
                self.tv_db.update_episode_keeping_status(entry[-1]["episode_id"], True)
                reruns.pop(0)
                #print(f"Koblet reprise sending {name} til (dag {original['day_of_week']}, {original['start_time']}) til episode {available_episodes[idx]['episode_number']}")

            for idx, original in enumerate(originals):
                if idx < len(available_episodes):
                    episode_id = available_episodes[idx]['id']
                    name = available_episodes[idx]["filename"]
                    self.tv_db.update_download_links(original['id'], episode_id)
                    print(f"Koblet original sending {name} til (dag {original['day_of_week']}, {original['start_time']}) til episode {available_episodes[idx]['episode_number']}")

            for idx, rerun in enumerate(reruns):
                if idx < len(available_episodes):
                    episode_id = available_episodes[idx]['id']
                    name = available_episodes[idx]["filename"]
                    self.tv_db.update_download_links(rerun['id'], episode_id)
                    print(f"Koblet reprise {name} til (dag {rerun['day_of_week']}, {rerun['start_time']}) til episode {available_episodes[idx]['episode_number']}")
        
if __name__ == "__main__":
    prep = TVPreparer()

    if len(sys.argv)>1:
        operation = sys.argv[1]

        if operation == "delete":
            prep.cleanup_obsolete_episodes()

        if operation == "increment":
            prep.increment_episodes()

        if operation == "keep":
            prep.update_keeping_status()

        elif operation == "pending":
            prep.create_pending_episodes()

        elif operation == "verify":
            prep.verify_files_for_scheduled_media()

        elif operation == "download":
            prep.download_weekly_schedule()

        elif operation == "link":
            prep.link_episodes_to_schedule()

        elif operation == "all":
            prep.cleanup_obsolete_episodes()
            prep.update_keeping_status()
            prep.create_pending_episodes()
            prep.download_weekly_schedule()
            prep.verify_files_for_scheduled_media()
            prep.link_episodes_to_schedule()

        else:
            print("not a valid operation")

    prep.increment_episodes()
