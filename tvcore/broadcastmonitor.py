
try:
    from .tvdatabase import TVDatabase, Schedule
    from .schemas import ScheduleOutput
    from .tvconstants import *
    from .helper import calculate_end_time
    from .tvconfig import TVConfig
except:
    from tvdatabase import TVDatabase, Schedule
    from schemas import ScheduleOutput
    from tvconstants import *
    from helper import calculate_end_time
    from tvconfig import TVConfig

from datetime import datetime, timedelta, time as time_class
import threading
import time
from flask import url_for

class BroadcastMonitor:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, time=None, time_acceleration=1, time_freeze=False, debug=False, loop_interval=1):
        self.debug = debug
        self.loop_interval = loop_interval

        #Testing parameters
        self.test_time = time #Sets start time for testing
        self.time_freeze = time_freeze #Wether or not time should pass or freeze
        self.current_time = time #Sets the "now" time for testing
        self.time_acceleration = time_acceleration # Sets time acceleration for testing
        self.simulation_started = None #For time testing

        self.offset = 0 #How far into the stream the program should start
        
        self.broadcast_start = datetime.strptime(TVConfig().config["schedule"]["broadcast_start"], "%H:%M").time()
        self.broadcast_end = datetime.strptime(TVConfig().config["schedule"]["broadcast_end"], "%H:%M").time()
        
        self.is_broadcasting = False
        
        self.current_nrk1 = None
        self.current_nrk2 = None

        self.database = TVDatabase()



    def start_monitoring(self):
        if not self.is_broadcasting:
            self.is_broadcasting = True
            threading.Thread(target=self._monitor_loop, daemon=True).start()
    
    def stop_monitoring(self):
        if self.is_broadcasting:
            self.is_broadcasting = False

    def _monitor_loop(self):
        while self.is_broadcasting:
            self.current_time = self.get_current_time()
            self.current_nrk1 = self.get_current_program("nrk1")
            self.current_nrk2 = self.get_current_program("nrk2")
            if self.debug:
                print(f"Monitoring: {self.current_nrk1['title']} at {self.current_nrk1['channel']} at {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Monitoring: {self.current_nrk2['title']} at {self.current_nrk2['channel']} at {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")

            time.sleep(1)

    def get_current_time(self):
        """
        Return either real time or simulated time. For testing purposes mainly
        """

        if self.test_time is None:
            return datetime.now()
        
        if self.time_freeze:
            return self.test_time
        
        if self.simulation_started is None:
            self.simulation_started = datetime.now()
            return self.test_time
        
        real_time_elapsed = datetime.now() - self.simulation_started
        
        simulated_time_elapsed = real_time_elapsed * self.time_acceleration
        
        return self.test_time + simulated_time_elapsed

    def get_current_stream(self, channel):
        if channel == "nrk1":
            return self.current_nrk1
        elif channel == "nrk2":
            return self.current_nrk2
        else:
            return None
    
    def calculate_offset(self, start_time:datetime, buffer_seconds:int=10):
        offset = (self.current_time - start_time).seconds - buffer_seconds
        return max(0, offset)
    
    def get_current_program(self, channel):
        current_program = self.database.get_current_program_by_channel(channel, time=self.current_time)

        if current_program:
            current_program["offset"] = self.calculate_offset(current_program["start"])
            current_program["start"] = current_program["start"].strftime("%H:%M")
            current_program["end"] = current_program["end"].strftime("%H:%M") 
            return current_program

        else:
            return {
                "id": STREAM_ID_NO_PROGRAM,
                "status": "no_program",
                "title": "Ingen program",
                "description": "Ingen program på dette tidspunktet",
                "filepath": "static/PM5544.mp4",
                "channel": channel,
            }


    def update_air_date(self, program: ScheduleOutput):
        if program.last_aired != self.current_time.date().strftime("%Y-%m-%d"):
            self.database.upsert(
                Schedule(
                    id = program.id,
                    last_aired = self.current_time.date()
                )
            )
    
    def get_current_status(self):
        if self.current_stream:
            return {
                "status": "streaming",
                "current_stream": self.current_stream
            }
        else:
            return {"status": "idle"}
    
