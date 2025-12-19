from tvcore.tvdatabase import TVDatabase
from tvcore.tvconstants import *
from datetime import datetime, timedelta, time as time_class
import threading
import json

class TVStreamManager:
    def __init__(self, time=None, config_path = 'config.json'):
        self.current_stream = None
        self.monitoring = False

        self.test_time = time

        self.database = TVDatabase()

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config =  json.load(f)

    def get_current_status(self):
        if self.current_stream:
            return {
                "status": "streaming",
                "current_stream": self.current_stream
            }
        else:
            return {"status": "idle"}
        
        
    def monitor_current_program(self, time = datetime.now()):
        current_hour = time.strftime("%H:%M")
        start_time = self.config["broadcast_start"]
    
        if current_hour < start_time:
            #Checks if the scheduled have started yet.
            #Need to be corrected for times past midnight
            return {
                "status": "off_air",
                "name": "Ingen sending",
                "description": "Sendingen starter kl. 18:00",
                "filepath": None
            }

        program = self.database.get_current_program(time=time)

        if not program:
            return {
                "status": "no_program",
                "name": "Ingen program",
                "description": "Ingen program på dette tidspunktet",
                "filepath": None
            }
        
        if program.get('status') != 'available':
            return {
                "status": "unavailable",
                "name": program.get('name', 'Ukjent program'),
                "description": "Programmet er ikke tilgjengelig for avspilling",
                "filepath": None
            }

        self.update_air_date(program)

        return program
    
    def update_air_date(self, program):
        if program["last_aired"] != datetime.now().date().strftime("%Y-%m-%d"):
            if program["content_type"] == TYPE_SERIES:
                self.database.update_program_info(TYPE_SERIES, program["media_id"], last_aired = datetime.now().date())
        if program["content_type"] == TYPE_MOVIES:
                self.database.update_program_info(TYPE_MOVIES, program["media_id"], last_aired = datetime.now().date())
    
    def start_monitoring(self):
        #Checks the current program and update the status
        if not self.monitoring:
            self.monitoring = True
            print("Started monitoring streams.")
            self.schedule = self.database.get_weekly_schedule()
            threading.Thread(target=self._monitor_streams, daemon=True).start()

    def stop_monitoring(self):
        self.monitoring = False
            
    def _monitor_streams(self):
        while self.monitoring:
            current_time = self.test_time if self.test_time else datetime.now()
            self.current_stream = self.monitor_current_program(time=current_time)
            
            if self.current_stream:
                print(f"Monitoring: {self.current_stream['name']} at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("No current program to monitor.")

            # Sleep for a while before checking again
            threading.Event().wait(10)




