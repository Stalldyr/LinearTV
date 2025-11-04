from TVdownloader import TVDownloader
from TVdatabase import TVDatabase
import helper
import os
import time
import sys

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

            self.tv_db.increment_episode(episode['series_id'])

            file_path = os.path.join(self.download_path, episode['directory'], episode['filename'])
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Slettet fil: {file_path}")
                else:
                    print(f"Filen finnes ikke: {file_path}")
                
                self.tv_db.update_episode_status(episode['id'], 'deleted')
            except Exception as e:
                print(f"Feil ved sletting av fil {file_path}: {e}")

    def update_deletion_status(self):
        kept_files = self.tv_db.get_kept_episodes()

        for episode in kept_files:
            self.tv_db.update_episode_keeping_status(episode['id'], False)

    def create_pending_episodes(self):
        series_list = self.tv_db.get_all_series()

        for series in series_list:
            if series["source_url"]:
                yt_dlp_data = self.tv_dl.get_ytdlp_season_metadata(series["season"], series["directory"])

                for entry in yt_dlp_data["entries"]:
                    episode_data = self.tv_dl.get_ytdlp_epsiode_info(entry)

                    if not episode_data["season_number"]:
                        episode_data["season_number"] = series["season"]

                    existing = self.tv_db.get_episode_by_details(series["id"], episode_data["season_number"], episode_data["episode_number"])

                    if existing:
                        continue

                    self.tv_db.insert_row("episodes", data=episode_data, series_id = series["id"], status = "pending", download_date = None)


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

            else:
                print("No metadata available")

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

    def verify_available_episodes(self):
        available_episodes = self.tv_db.get_available_episodes()

        for episode in available_episodes:
            path = helper._get_file_path(self.download_path, episode['directory'], episode['filename'])
            success = helper._verify_local_file(path)

            if success:
                print(f"Fil eksisterer: {episode['filename']}")
            else:
                print(f"Fil mangler: {episode['filename']}")
                self.tv_db.update_episode_status(episode['id'], 'missing')

    def verify_nonavailable_episodes(self):
        '''
            Checks if any episodes that should not be there
        '''

        nonavailable_episodes = self.tv_db.get_nonavailable_episodes()

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
            prep.update_deletion_status()

        elif operation == "pending":
            prep.create_pending_episodes()

        elif operation == "verify":
            prep.verify_available_episodes()

        elif operation == "download":
            prep.download_weekly_schedule()

        elif operation == "link":
            prep.link_episodes_to_schedule()

        elif operation == "all":
            prep.cleanup_obsolete_episodes()
            prep.update_deletion_status()
            prep.create_pending_episodes()
            prep.download_weekly_schedule()
            prep.verify_available_episodes()
            prep.link_episodes_to_schedule()

        else:
            print("not a valid operation")