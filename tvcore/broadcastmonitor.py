
try:
    from .tvdatabase import TVDatabase, Schedule
    from .schemas import ScheduleOutput
    from .tvconstants import *
except:
    from tvdatabase import TVDatabase, Schedule
    from schemas import ScheduleOutput
    from tvconstants import *

from datetime import datetime, timedelta, time
import threading
import time

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
        
        self.is_broadcasting = False

        self.channels = ["nrk1", "nrk2", "cable"] #TODO:Shouldn't be hardcoded
        
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
            if self.debug:
                for channel in self.channels:
                    current = self.get_current_program(channel)
                    print(f"Monitoring: {current['title']} at {current['channel']} at {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")

            time.sleep(1)

    def get_current_time(self):
        """
        Return either real time or simulated time. For testing purposes mainly
        """

        if self.test_time is None and self.time_acceleration is None:
            return datetime.now()

        self.test_time = datetime.now()
        
        if self.time_freeze:
            return self.test_time
        
        if self.simulation_started is None:
            self.simulation_started = datetime.now()
            return self.test_time
        
        real_time_elapsed = datetime.now() - self.simulation_started
        
        simulated_time_elapsed = real_time_elapsed * self.time_acceleration
        
        return self.test_time + simulated_time_elapsed

    
    def calculate_offset(self, start_time:datetime, current_time:datetime, buffer_seconds:int=10):
        offset = (current_time - start_time).seconds - buffer_seconds
        return max(0, offset)
    
    def get_current_program(self, channel):
        now = self.get_current_time()
        current_program = self.database.get_current_program_by_channel(channel, time=now)

        if current_program:
            current_program["offset"] = self.calculate_offset(current_program["start"], now)
            current_program["start"] = current_program["start"].strftime("%H:%M")
            current_program["end"] = current_program["end"].strftime("%H:%M") 

            return current_program

        else:
            no_program = {
                "id": STREAM_ID_NO_PROGRAM,
                "status": "no_program",
                "title": "Ingen program på dette tidspunktet",
                "description": "Det er en stund til neste program starter. Sjekk TV-guide",
                "filepath": None,
                "channel": channel,
            }

            next_program = self.database.get_next_program_by_channel(channel, time=now)
            if next_program:
                no_program["description"] = f"Neste program starter {next_program["start"]}:\n {next_program["title"]}"

            return no_program

    def update_air_date(self, program: ScheduleOutput):
        if program.last_aired != self.current_time.date().strftime("%Y-%m-%d"):
            self.database.upsert(
                Schedule(
                    id = program.id,
                    last_aired = self.current_time.date()
                )
            )