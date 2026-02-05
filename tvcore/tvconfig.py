import json
from pathlib import Path

try:
    from .helper import calculate_time_slots
except:
    from helper import calculate_time_slots

class TVConfig:
    def __init__(self, config_path=""):
        if not config_path:
            default_path = Path(__file__).parent.parent.absolute()/"config.json"
            with open(default_path, 'r', encoding='utf-8') as f:
                self.config =  json.load(f)

        else:
            with open(Path(config_path), 'r', encoding='utf-8') as f:
                self.config =  json.load(f)

    def get_time_slots(self):
        schedule_options = self.config["schedule"]

        timeslots = calculate_time_slots(
            schedule_options["broadcast_start"],
            schedule_options["broadcast_end"],
            schedule_options["broadcast_steps"]
        )

        return timeslots

    def get_genres(self):
        return self.config["genres"]
    
    def get_header(self):
        if self.config["language"] == "no":
            return ["Tid", "Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag", "Søndag"]

        elif self.config["language"] == "en":
            return ["Time", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        else:
            print("Language not supported")

    def get_language(self):
        return self.config.get("language", "")
