from .tvdatabase import TVDatabase
from .tvconstants import *
from datetime import datetime, timedelta, time as time_class
import threading
import json
from pathlib import Path

class TVStreamManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, time=None, time_acceleration=1, config_path = 'config.json'):
        if hasattr(self, '_initialized'):
            return

        self.current_stream = None
        self.monitoring = False

        self.test_time = time
        self.time_acceleration = time_acceleration
        self.simulation_started = None
        self.offset = 0

        self.database = TVDatabase()

        with open(Path(__file__).parent.parent.absolute()/config_path, 'r', encoding='utf-8') as f:
            self.config =  json.load(f)

        self._initialized = True


    def get_current_time(self):
        """
        Returnerer enten ekte tid eller simulert tid.
        Hvis time_acceleration = 60, går 1 minutt i virkeligheten = 1 time i simuleringen
        """
        if self.test_time is None:
            return datetime.now()
        
        if self.simulation_started is None:
            self.simulation_started = datetime.now()
            return self.test_time
        
        real_time_elapsed = datetime.now() - self.simulation_started
        
        simulated_time_elapsed = real_time_elapsed * self.time_acceleration
        
        return self.test_time + simulated_time_elapsed

    def get_current_status(self):
        if self.current_stream:
            return {
                "status": "streaming",
                "current_stream": self.current_stream
            }
        else:
            return {"status": "idle"}
        
        
    def monitor_current_program(self):
        current_hour = self.current_time.strftime("%H:%M")
        start_time = self.config["broadcast_start"]
    
        if current_hour < start_time:
            #Checks if the scheduled have started yet.
            #TODO Need to be corrected for times past midnight
            return {
                "status": "off_air",
                "name": "Ingen sending",
                "description": "Sendingen starter kl. 18:00",
                "filename": None,
                #"offset": self.offset
            }

        program = self.database.get_current_program(time = self.current_time)
       
        if not program:
            return {
                "status": "no_program",
                "name": "Ingen program",
                "description": "Ingen program på dette tidspunktet",
                "filename": None,
                #"offset": self.offset
            }
        
        if program.get('status') != 'available':
            return {
                "status": "unavailable",
                "name": program.get('name', 'Ukjent program'),
                "description": "Programmet er ikke tilgjengelig for avspilling",
                "filename": None,
                #"offset": self.offset
            }
        

        offset = self.calculate_offset(program["start_time"]) 
        program["offset"] = offset

        self.update_air_date(program)

        return program
    
    def update_air_date(self, program):
        if program["last_aired"] != self.current_time.date().strftime("%Y-%m-%d"):
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
            self.current_time = self.get_current_time()
            self.current_stream = self.monitor_current_program()
            
            if self.current_stream:
                print(f"Monitoring: {self.current_stream['name']} at {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"No program at {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")

            threading.Event().wait(10)

    def calculate_offset(self, start_time):
        offset = (self.current_time - datetime.strptime(start_time, "%H:%M")).seconds - 10
        return max(0, offset)
  




