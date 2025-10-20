import threading
from datetime import datetime, timedelta, time as time_class
from TVdatabase import TVDatabase

class TVStreamManager:
    def __init__(self, time=None):
        self.current_stream = None
        self.monitoring = False

        if time:
            self.tv_db = TVDatabase(test_time=time)
            self.time = time
        else:
            self.tv_db = TVDatabase()
            self.time = datetime.now()


    def get_current_status(self):
        if self.current_stream:
            return {
                "status": "streaming",
                "current_stream": self.current_stream
            }
        else:
            return {"status": "idle"}
        
        
    def get_current_program(self):
        current_hour = int(self.time.strftime("%H"))
    
        if current_hour < 18:
            self.current_stream = None
            return {
                "status": "off_air",
                "show_name": "Ingen sending",
                "description": "Sendingen starter kl. 18:00",
                "filepath": None
            }

        program = self.tv_db.get_current_program()

        if not program:
            self.current_stream = None
            return {
                "status": "no_program",
                "show_name": "Ingen program",
                "description": "Ingen program på dette tidspunktet",
                "filepath": None
            }
        
        if program.get('status') != 'available':
            self.current_stream = None
            return {
                "status": "unavailable",
                "show_name": program.get('show_name', 'Ukjent program'),
                "description": "Programmet er ikke tilgjengelig for avspilling",
                "filepath": None
            }

        self.current_stream = program
        return program
    
    def get_next_program(self):
        next_program = self.tv_db.get_next_program()
        return next_program
    
    def start_monitoring(self):
        #Checks the current program and update the status
        if not self.monitoring:
            self.monitoring = True
            print("Started monitoring streams.")
            self.schedule = self.tv_db.get_weekly_schedule()
            threading.Thread(target=self._monitor_streams, daemon=True).start()

    def stop_monitoring(self):
        self.monitoring = False
            
    def _monitor_streams(self):
        while self.monitoring:
            current_program = self.get_current_program()
            current_time = datetime.now()
 
            if current_program:
                print(f"Monitoring: {current_program['show_name']} at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("No current program to monitor.")

            # Sleep for a while before checking again
            threading.Event().wait(10)




