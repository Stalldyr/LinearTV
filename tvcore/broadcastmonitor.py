
try:
    from .tvdatabase import TVDatabase
    from .tvconstants import *
    from .helper import calculate_end_time
    from .tvconfig import TVConfig
except:
    from tvdatabase import TVDatabase
    from tvconstants import *
    from helper import calculate_end_time
    from tvconfig import TVConfig

from datetime import datetime, timedelta, time as time_class
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

        self.offset = 0 #How far into the stream the program should start
        
        self.broadcast_start = datetime.strptime(TVConfig().config["schedule"]["broadcast_start"], "%H:%M").time()
        self.broadcast_end = datetime.strptime(TVConfig().config["schedule"]["broadcast_end"], "%H:%M").time()
        
        self.is_broadcasting = False
        self.current_stream = None

        self.database = TVDatabase()

    def update_schedule(self):
        self.schedule = self.database.get_air_schedule()

    def start_monitoring(self):
        if not self.is_broadcasting:
            self.is_broadcasting = True
            self.schedule = self.database.get_air_schedule()
            threading.Thread(target=self._monitor_loop, daemon=True).start()
    
    def stop_monitoring(self):
        if self.is_broadcasting:
            self.is_broadcasting = False

    def _monitor_loop(self):
        while self.is_broadcasting:
            self.current_time = self.get_current_time()
            self.current_stream = self.get_current_program()
            if self.debug:
                if self.current_stream:
                    print(f"Monitoring: {self.current_stream['name']} at {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print(f"No program at {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")

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

    def get_current_program(self) -> dict:
        if self.current_time.time() < self.broadcast_start:
            #Checks if the scheduled have started yet.
            #TODO: Need to be corrected for times past midnight
            return {
                "id": STREAM_ID_OFF_AIR,
                "status": "off_air",
                "name": "Ingen sending",
                "description": "Sendingen starter kl. 18:00",
                "filename": None,
            }
        
        if self.current_time.time() >= self.broadcast_end:  
            #TODO: Need to be corrected for times past midnight
            self.is_broadcasting = False
            return {
                "id": STREAM_ID_OFF_AIR,
                "status": "off_air",
                "name": "Ingen sending",
                "description": "Sendingen er ferdig for i dag",
                "filename": None,
            }

        program = self.search_current_program()
       
        if not program:
            return {
                "id": STREAM_ID_NO_PROGRAM,
                "status": "no_program",
                "name": "Ingen program",
                "description": "Ingen program på dette tidspunktet",
                "filename": None,
            }
        
        if program.get('status') != STATUS_AVAILABLE:
            return {
                "id": STREAM_ID_UNAVAILABLE,
                "status": "unavailable",
                "name": program.get('name', 'Ukjent program'),
                "description": "Programmet er ikke tilgjengelig for avspilling",
                "filename": None,
            }
        
        offset = self.calculate_offset(program["start_time"])
        program["offset"] = offset

        self.current_stream = program
        self.update_air_date(program)

        return program

    def get_current_stream(self):
        return self.current_stream
    
    def search_current_program(self) -> dict:
        """
        Returns the program showing at the current time
        TODO: Needs to implement logic that goes past midnight
        """
        current_time = self.current_time.time()
        current_day = int(self.current_time.strftime('%w'))

        if current_day == 0:
            current_day = 7
        
        for program in self.schedule:
            if program['day_of_week'] == current_day:
                start_hour, start_min = map(int, program['start_time'].split(':'))
                start_time = time_class(start_hour, start_min)
                
                end_time = datetime.strptime(program['end_time'], "%H:%M").time() if program['end_time'] else None
                if not end_time:
                    duration_minutes = program['duration'] if program['duration'] else 30
                    end_time = calculate_end_time(program['start_time'], duration_minutes)

                if start_time <= current_time < end_time:
                    return program
        
        return None
    
    def calculate_offset(self, start_time, buffer_seconds=10):
        offset = (self.current_time - datetime.strptime(start_time, "%H:%M")).seconds - buffer_seconds
        return max(0, offset)
    

    def update_air_date(self, program):
        if program["last_aired"] != self.current_time.date().strftime("%Y-%m-%d"):
            if program["content_type"] == TYPE_SERIES:
                self.database.update_program_info(TYPE_SERIES, program["media_id"], last_aired = self.current_time.date())

            elif program["content_type"] == TYPE_MOVIES:
                    self.database.update_program_info(TYPE_MOVIES, program["media_id"], last_aired = self.current_time.date())
    
    def get_current_status(self):
        if self.current_stream:
            return {
                "status": "streaming",
                "current_stream": self.current_stream
            }
        else:
            return {"status": "idle"}
        
    def correct_for_times_past_midnight(self, start_time, end_time):
        if end_time < start_time:
            pass
