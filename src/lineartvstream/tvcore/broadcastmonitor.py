
from .tvdatabase import TVDatabase, Schedule
from .schemas import ScheduleOutput
from .tvconstants import *
from datetime import datetime, time
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
            #if self.debug:
            #    for channel in self.database.get_channels():
            #        current = self.database.get_current_program(channel.channel_id)
            #        print(f"Monitoring: {current.title} at {current.channel} at {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")

            time.sleep(1)

    def get_current_time(self):
        """
        Return either real time or simulated time. For testing purposes mainly
        """

        if self.test_time is None and self.time_acceleration is None:
            return datetime.now()
        
        if self.time_freeze:
            return self.test_time
        
        if self.simulation_started is None:
            self.simulation_started = datetime.now()
            if self.test_time is None:
                self.test_time = datetime.now()
                
        real_time_elapsed = datetime.now() - self.simulation_started
        
        simulated_time_elapsed = real_time_elapsed * self.time_acceleration
        
        return self.test_time + simulated_time_elapsed

    def update_air_date(self, program: ScheduleOutput):
        if program.last_aired != self.current_time.date().strftime("%Y-%m-%d"):
            self.database.upsert(
                Schedule(
                    id = program.id,
                    last_aired = self.current_time.date()
                )
            )